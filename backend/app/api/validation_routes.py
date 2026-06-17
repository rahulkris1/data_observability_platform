"""Validation API routes for executing validations and retrieving audit history."""

import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pyspark.sql import DataFrame
import pandas as pd

from app.core.database import get_db
from app.schemas.validation_response import (
    ValidationExecutionRequest,
    ValidationExecutionResponse,
    ValidatorResultResponse,
    AuditHistoryResponse,
    AuditHistoryItem,
    APIErrorResponse,
)
from app.services.validation_aggregator import ValidationAggregator
from app.services.validation_log_service import ValidationLogService
from app.services.audit_service import AuditService
from app.services.ingestion_service import IngestionService
from app.services.schema_contract_service import SchemaContractService
from app.services.cache_service import get_cache_service
from app.storage.minio_client import minio_client
from app.utils.spark_utils import get_spark
from app.validators.base_validator import ValidationStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1",
    tags=["validations", "audit"]
)


def _convert_summary_to_response(summary) -> ValidationExecutionResponse:
    """Convert ValidationSummary to ValidationExecutionResponse."""
    validators_response = [
        ValidatorResultResponse(
            validator_name=v.validator_name,
            status=v.status.value if hasattr(v.status, 'value') else v.status,
            passed=v.passed,
            total_records=v.total_records,
            failed_records=v.failed_records,
            pass_rate=v.pass_rate,
            message=v.message,
            execution_time_ms=v.execution_time_ms,
            errors=v.errors
        )
        for v in summary.validators
    ]
    
    return ValidationExecutionResponse(
        dataset_name=summary.dataset_name,
        validation_timestamp=summary.validation_timestamp,
        overall_status=summary.overall_status.value if hasattr(summary.overall_status, 'value') else summary.overall_status,
        overall_passed=summary.overall_passed,
        total_validators=summary.total_validators,
        passed_validators=summary.passed_validators,
        failed_validators=summary.failed_validators,
        warning_validators=summary.warning_validators,
        error_validators=summary.error_validators,
        total_records=summary.total_records,
        total_execution_time_ms=summary.total_execution_time_ms,
        validators=validators_response,
        metadata=summary.metadata
    )


@router.post(
    "/validations/execute",
    response_model=ValidationExecutionResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": APIErrorResponse, "description": "Bad request"},
        404: {"model": APIErrorResponse, "description": "Dataset not found"},
        500: {"model": APIErrorResponse, "description": "Internal server error"}
    },
    summary="Execute validation on a dataset",
    description="Execute validation checks on a dataset and return results"
)
async def execute_validation(
    request: ValidationExecutionRequest,
    db: Session = Depends(get_db)
):
    """
    Execute validation on a dataset.
    
    Args:
        request: Validation execution request with dataset information
        db: Database session
        
    Returns:
        ValidationExecutionResponse with validation results
        
    Raises:
        HTTPException: If dataset not found or validation fails
    """
    start_time = datetime.utcnow()
    logger.info(f"Validation execution request received for dataset: {request.dataset_name}")
    logger.info(f"Request details: {request.dict()}")
    
    try:
        # Initialize services
        ingestion_service = IngestionService()
        validation_aggregator = ValidationAggregator()
        validation_log_service = ValidationLogService(db)
        audit_service = AuditService(db)
        schema_contract_service = SchemaContractService()
        
        # Determine dataset path
        dataset_path = request.dataset_path or request.dataset_name
        
        # Load dataset from MinIO
        logger.info(f"Loading dataset from MinIO: {dataset_path}")
        try:
            # Try to load as processed JSON first
            dataset_data = ingestion_service.load_processed_dataset(dataset_path)
        except FileNotFoundError:
            # If not found, try raw bucket
            try:
                raw_data = ingestion_service.load_raw_dataset(dataset_path)
                # Parse based on file extension
                if dataset_path.endswith('.csv'):
                    from app.utils.csv_parser import parse_csv_bytes
                    dataset_data = parse_csv_bytes(raw_data)
                elif dataset_path.endswith('.json'):
                    from app.utils.json_parser import parse_json_bytes
                    dataset_data = parse_json_bytes(raw_data)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Unsupported file format for dataset: {dataset_path}"
                    )
            except FileNotFoundError:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Dataset not found: {dataset_path}"
                )
        
        # Convert to Spark DataFrame
        logger.info("Converting dataset to Spark DataFrame")
        spark = get_spark()
        pandas_df = pd.DataFrame(dataset_data)
        df: DataFrame = spark.createDataFrame(pandas_df)
        
        # Load schema contract if provided
        schema_contract = None
        if request.schema_contract_id:
            logger.info(f"Loading schema contract by ID: {request.schema_contract_id}")
            # For now, schema contracts are loaded from files, not by ID
            # This would need to be updated when database persistence is added
            contracts = schema_contract_service.get_all_contracts()
            if contracts and request.schema_contract_id <= len(contracts):
                contract = contracts[request.schema_contract_id - 1]
                schema_contract = contract.schema_definition
            else:
                logger.warning(f"Schema contract not found for ID: {request.schema_contract_id}")
        
        # Execute validation with defaults
        logger.info("Executing validation...")
        validation_summary = validation_aggregator.validate_with_defaults(
            df=df,
            dataset_name=request.dataset_name,
            schema_contract=schema_contract,
            null_threshold=request.null_threshold
        )
        
        # Log validation results to database
        logger.info("Storing validation results in database")
        validation_log_service.log_validation_summary(validation_summary)
        
        # Create audit records for each validator
        for validator_summary in validation_summary.validators:
            audit_service.create_audit_record(
                dataset_name=request.dataset_name,
                validation_type=validator_summary.validator_name.lower().replace('validator', '').strip(),
                status=validator_summary.status.value if hasattr(validator_summary.status, 'value') else validator_summary.status,
                execution_time_ms=validator_summary.execution_time_ms,
                total_records=validator_summary.total_records,
                failed_records=validator_summary.failed_records,
                pass_rate=validator_summary.pass_rate,
                validator_name=validator_summary.validator_name,
                triggered_by="api",
                environment="dev",
                error_summary="; ".join(validator_summary.errors) if validator_summary.errors else None,
                details={"message": validator_summary.message}
            )
        
        # Convert to response model
        response = _convert_summary_to_response(validation_summary)
        
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds() * 1000
        logger.info(f"Validation completed in {execution_time:.2f}ms")
        logger.info(f"Overall status: {response.overall_status}, Passed: {response.overall_passed}")
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Validation execution failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation execution failed: {str(e)}"
        )


@router.get(
    "/audit/history",
    response_model=AuditHistoryResponse,
    status_code=status.HTTP_200_OK,
    responses={
        500: {"model": APIErrorResponse, "description": "Internal server error"}
    },
    summary="Get audit history",
    description="Retrieve audit history with optional filtering by dataset, status, and validation type"
)
async def get_audit_history(
    dataset_name: Optional[str] = Query(None, description="Filter by dataset name"),
    validation_type: Optional[str] = Query(None, description="Filter by validation type"),
    status: Optional[str] = Query(None, description="Filter by status (passed/failed/warning/error)"),
    triggered_by: Optional[str] = Query(None, description="Filter by who triggered the validation"),
    environment: Optional[str] = Query(None, description="Filter by environment"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_db)
):
    """
    Retrieve audit history with filtering and pagination.
    
    Args:
        dataset_name: Optional dataset name filter
        validation_type: Optional validation type filter
        status: Optional status filter
        triggered_by: Optional triggered_by filter
        environment: Optional environment filter
        limit: Number of items to return
        offset: Number of items to skip
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
        db: Database session
        
    Returns:
        AuditHistoryResponse with audit records
    """
    logger.info("Audit history request received")
    logger.info(f"Filters: dataset={dataset_name}, type={validation_type}, status={status}, "
                f"triggered_by={triggered_by}, environment={environment}")
    logger.info(f"Pagination: limit={limit}, offset={offset}, sort_by={sort_by}, sort_order={sort_order}")
    
    try:
        audit_service = AuditService(db)
        
        # Get audit history
        audit_logs = audit_service.get_audit_history(
            dataset_name=dataset_name,
            validation_type=validation_type,
            status=status,
            triggered_by=triggered_by,
            environment=environment,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Get total count
        total_count = audit_service.get_audit_count(
            dataset_name=dataset_name,
            validation_type=validation_type,
            status=status,
            triggered_by=triggered_by,
            environment=environment
        )
        
        # Convert to response items
        items = [
            AuditHistoryItem(
                id=log.id,
                dataset_name=log.dataset_name,
                validation_type=log.validation_type,
                status=log.status,
                validator_name=log.validator_name,
                total_records=log.total_records,
                failed_records=log.failed_records,
                pass_rate=log.pass_rate,
                execution_time_ms=log.execution_time_ms,
                triggered_by=log.triggered_by,
                environment=log.environment,
                created_at=log.created_at,
                error_summary=log.error_summary
            )
            for log in audit_logs
        ]
        
        logger.info(f"Returning {len(items)} audit records (total: {total_count})")
        
        return AuditHistoryResponse(
            total_count=total_count,
            items=items,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve audit history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit history: {str(e)}"
        )
