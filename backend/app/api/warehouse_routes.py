"""Warehouse API routes for data warehouse operations"""

import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.warehouse_schema import (
    WarehouseLoadRequest,
    WarehouseLoadResponse,
    WarehouseValidationRequest,
    WarehouseValidationResponse,
    WarehouseStatisticsResponse,
    WarehouseLoadHistoryResponse,
    DatasetHealthResponse,
    WarehouseProcessedDataResponse,
    ValidationResultResponse
)
from app.warehouse.warehouse_service import WarehouseReadService, WarehouseWriteService
from app.warehouse.batch_loader import BatchLoader, BatchLoaderConfig
from app.warehouse.audit_logger import WarehouseAuditLogger
from app.warehouse.validator import WarehouseValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/warehouse",
    tags=["warehouse"]
)


@router.post(
    "/load",
    response_model=WarehouseLoadResponse,
    status_code=status.HTTP_200_OK,
    summary="Load data to warehouse",
    description="Execute a batch load of records to the warehouse with transaction management"
)
async def load_data_to_warehouse(
    request: WarehouseLoadRequest,
    db: Session = Depends(get_db)
):
    """
    Load a batch of records to the warehouse.
    
    Args:
        request: Warehouse load request with records and configuration
        db: Database session
        
    Returns:
        WarehouseLoadResponse with load execution results
    """
    try:
        # Create batch loader with configuration
        config = BatchLoaderConfig(
            batch_size=request.batch_size or 1000,
            enable_deduplication=request.enable_deduplication,
            skip_duplicates=request.skip_duplicates,
            enable_validation=True,
            enable_staging=False
        )
        
        loader = BatchLoader(db=db, config=config)
        
        # Execute load
        logger.info(f"Starting warehouse load for dataset: {request.dataset_name}")
        result = loader.load_batch(
            records=request.records,
            dataset_name=request.dataset_name,
            source_system=request.source_system,
            load_type=request.load_type,
            metadata=request.metadata
        )
        
        return WarehouseLoadResponse(**result)
        
    except Exception as e:
        logger.error(f"Error loading data to warehouse: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load data to warehouse: {str(e)}"
        )


@router.get(
    "/statistics",
    response_model=WarehouseStatisticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get warehouse statistics",
    description="Retrieve overall warehouse statistics and metrics"
)
async def get_warehouse_statistics(
    db: Session = Depends(get_db)
):
    """
    Get overall warehouse statistics.
    
    Args:
        db: Database session
        
    Returns:
        WarehouseStatisticsResponse with warehouse metrics
    """
    try:
        read_service = WarehouseReadService(db)
        stats = read_service.get_warehouse_statistics()
        
        return WarehouseStatisticsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error retrieving warehouse statistics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve warehouse statistics: {str(e)}"
        )


@router.get(
    "/load-history",
    response_model=List[WarehouseLoadHistoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get warehouse load history",
    description="Retrieve warehouse load execution history with optional filters"
)
async def get_warehouse_load_history(
    dataset_name: Optional[str] = Query(None, description="Filter by dataset name"),
    status: Optional[str] = Query(None, description="Filter by load status"),
    load_type: Optional[str] = Query(None, description="Filter by load type"),
    limit: int = Query(50, description="Maximum number of records to return", ge=1, le=500),
    offset: int = Query(0, description="Number of records to skip", ge=0),
    db: Session = Depends(get_db)
):
    """
    Get warehouse load execution history.
    
    Args:
        dataset_name: Optional filter by dataset name
        status: Optional filter by load status
        load_type: Optional filter by load type
        limit: Maximum number of records
        offset: Number of records to skip
        db: Database session
        
    Returns:
        List of WarehouseLoadHistoryResponse
    """
    try:
        read_service = WarehouseReadService(db)
        history = read_service.get_load_history(
            dataset_name=dataset_name,
            status=status,
            load_type=load_type,
            limit=limit,
            offset=offset
        )
        
        return [WarehouseLoadHistoryResponse.from_orm(h) for h in history]
        
    except Exception as e:
        logger.error(f"Error retrieving load history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve load history: {str(e)}"
        )


@router.get(
    "/load-history/{batch_id}",
    response_model=WarehouseLoadHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get load history by batch ID",
    description="Retrieve load history details for a specific batch"
)
async def get_load_by_batch_id(
    batch_id: str,
    db: Session = Depends(get_db)
):
    """
    Get load history by batch ID.
    
    Args:
        batch_id: Batch identifier
        db: Database session
        
    Returns:
        WarehouseLoadHistoryResponse
    """
    try:
        read_service = WarehouseReadService(db)
        load = read_service.get_load_by_batch_id(batch_id)
        
        if not load:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Load history not found for batch_id: {batch_id}"
            )
        
        return WarehouseLoadHistoryResponse.from_orm(load)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving load by batch ID: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve load: {str(e)}"
        )


@router.get(
    "/dataset/{dataset_name}/health",
    response_model=DatasetHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get dataset health metrics",
    description="Retrieve health metrics for a specific dataset"
)
async def get_dataset_health(
    dataset_name: str,
    db: Session = Depends(get_db)
):
    """
    Get health metrics for a specific dataset.
    
    Args:
        dataset_name: Name of the dataset
        db: Database session
        
    Returns:
        DatasetHealthResponse with dataset health metrics
    """
    try:
        read_service = WarehouseReadService(db)
        health = read_service.get_dataset_health(dataset_name)
        
        return DatasetHealthResponse(**health)
        
    except Exception as e:
        logger.error(f"Error retrieving dataset health: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dataset health: {str(e)}"
        )


@router.get(
    "/data",
    response_model=List[WarehouseProcessedDataResponse],
    status_code=status.HTTP_200_OK,
    summary="Get warehouse processed data",
    description="Retrieve processed warehouse data with optional filters"
)
async def get_warehouse_data(
    dataset_name: Optional[str] = Query(None, description="Filter by dataset name"),
    batch_id: Optional[str] = Query(None, description="Filter by batch ID"),
    validation_status: Optional[str] = Query(None, description="Filter by validation status"),
    limit: int = Query(100, description="Maximum number of records to return", ge=1, le=1000),
    offset: int = Query(0, description="Number of records to skip", ge=0),
    db: Session = Depends(get_db)
):
    """
    Get processed warehouse data.
    
    Args:
        dataset_name: Optional filter by dataset name
        batch_id: Optional filter by batch ID
        validation_status: Optional filter by validation status
        limit: Maximum number of records
        offset: Number of records to skip
        db: Database session
        
    Returns:
        List of WarehouseProcessedDataResponse
    """
    try:
        read_service = WarehouseReadService(db)
        data = read_service.get_processed_data(
            dataset_name=dataset_name,
            batch_id=batch_id,
            validation_status=validation_status,
            limit=limit,
            offset=offset
        )
        
        return [WarehouseProcessedDataResponse.from_orm(d) for d in data]
        
    except Exception as e:
        logger.error(f"Error retrieving warehouse data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve warehouse data: {str(e)}"
        )


@router.post(
    "/validate",
    response_model=WarehouseValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate warehouse data",
    description="Validate records before loading to warehouse"
)
async def validate_warehouse_data(
    request: WarehouseValidationRequest,
    db: Session = Depends(get_db)
):
    """
    Validate records before loading to warehouse.
    
    Args:
        request: Warehouse validation request
        db: Database session
        
    Returns:
        WarehouseValidationResponse with validation results
    """
    try:
        validator = WarehouseValidator(db)
        
        # Parse schema if provided
        schema = None
        if request.schema:
            # Convert string type names to actual types
            type_mapping = {
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'dict': dict,
                'list': list
            }
            schema = {
                field: type_mapping.get(type_str, str)
                for field, type_str in request.schema.items()
            }
        
        # Run validations
        results = validator.validate_batch(
            records=request.records,
            dataset_name=request.dataset_name,
            required_columns=request.required_columns,
            unique_keys=request.unique_keys,
            schema=schema
        )
        
        # Convert results to response
        validation_results = [
            ValidationResultResponse(**result.to_dict())
            for result in results
        ]
        
        overall_valid = all(result.is_valid for result in results)
        
        return WarehouseValidationResponse(
            dataset_name=request.dataset_name,
            validation_timestamp=datetime.utcnow(),
            overall_valid=overall_valid,
            total_validations=len(results),
            passed_validations=sum(1 for r in results if r.is_valid),
            failed_validations=sum(1 for r in results if not r.is_valid),
            validation_results=validation_results
        )
        
    except Exception as e:
        logger.error(f"Error validating warehouse data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate warehouse data: {str(e)}"
        )


@router.delete(
    "/load/{batch_id}/rollback",
    status_code=status.HTTP_200_OK,
    summary="Rollback a warehouse load",
    description="Rollback a batch load by deleting loaded records"
)
async def rollback_warehouse_load(
    batch_id: str,
    db: Session = Depends(get_db)
):
    """
    Rollback a warehouse load.
    
    Args:
        batch_id: Batch identifier to rollback
        db: Database session
        
    Returns:
        Rollback result
    """
    try:
        config = BatchLoaderConfig()
        loader = BatchLoader(db=db, config=config)
        
        result = loader.rollback_batch(batch_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Error rolling back warehouse load: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rollback warehouse load: {str(e)}"
        )
