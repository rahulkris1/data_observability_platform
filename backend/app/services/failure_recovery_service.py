"""Failure Recovery Service

Recovers failed validation executions by re-running validations
"""
from typing import Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import time

from app.models.retry_queue import RetryQueue
from app.models.validation_log import ValidationLog
from app.validators.base_validator import ValidationStatus

logger = logging.getLogger(__name__)


class FailureRecoveryService:
    """Service for recovering from failed validation executions
    
    IMPORTANT: This service ONLY executes manual retries.
    It does NOT perform automatic retries.
    """
    
    def __init__(self, db: Session):
        """Initialize the failure recovery service
        
        Args:
            db: Database session
        """
        self.db = db
    
    def execute_retry(
        self,
        retry_id: int,
        executor: Optional[str] = None
    ) -> Dict:
        """Execute a manual retry for a failed validation
        
        This method re-runs the validation that previously failed.
        
        Args:
            retry_id: ID of the retry queue entry
            executor: Optional user executing the retry
            
        Returns:
            Dictionary containing retry execution results
            
        Raises:
            ValueError: If retry not found or not executable
        """
        logger.info(f"Executing retry: retry_id={retry_id}, executor={executor}")
        
        # Get retry entry
        retry_entry = self.db.query(RetryQueue).filter(
            RetryQueue.id == retry_id
        ).first()
        
        if not retry_entry:
            raise ValueError(f"Retry entry not found: {retry_id}")
        
        # Check if retry is allowed
        if not retry_entry.is_retryable():
            raise ValueError(
                f"Retry not allowed - status: {retry_entry.retry_status}, "
                f"count: {retry_entry.retry_count}/{retry_entry.max_retries}"
            )
        
        # Get original validation log
        original_validation = self.db.query(ValidationLog).filter(
            ValidationLog.id == retry_entry.validation_log_id
        ).first()
        
        if not original_validation:
            raise ValueError(f"Original validation not found: {retry_entry.validation_log_id}")
        
        # Mark retry as in progress
        retry_entry.retry_status = "in_progress"
        self.db.commit()
        
        start_time = time.time()
        retry_result = {
            "retry_id": retry_id,
            "validation_log_id": retry_entry.validation_log_id,
            "success": False,
            "message": "",
            "new_validation_log_id": None,
            "execution_time_ms": 0
        }
        
        try:
            # Re-run the validation
            # NOTE: In a real implementation, this would reconstruct and re-execute
            # the validator with the same parameters. For now, we'll create a
            # placeholder that simulates the retry.
            
            validation_result = self._rerun_validation(original_validation)
            
            # Create new validation log for the retry attempt
            new_validation_log = ValidationLog(
                dataset_name=original_validation.dataset_name,
                validation_type=original_validation.validation_type,
                status=validation_result["status"],
                total_records=validation_result.get("total_records", 0),
                failed_records=validation_result.get("failed_records", 0),
                pass_rate=validation_result.get("pass_rate", 0.0),
                execution_time_ms=validation_result.get("execution_time_ms"),
                validator_name=original_validation.validator_name,
                message=f"Retry attempt {retry_entry.retry_count + 1} - {validation_result.get('message', '')}",
                details={
                    "retry_id": retry_id,
                    "original_validation_id": original_validation.id,
                    "retry_attempt": retry_entry.retry_count + 1,
                    **validation_result.get("details", {})
                },
                errors=validation_result.get("errors", [])
            )
            
            self.db.add(new_validation_log)
            self.db.flush()
            
            # Record retry attempt
            retry_entry.record_retry_attempt({
                "status": validation_result["status"],
                "validation_log_id": new_validation_log.id,
                "message": validation_result.get("message", ""),
                "executor": executor
            })
            
            # Check if retry succeeded
            success = validation_result["status"] in ["passed", "warning"]
            
            if success:
                retry_entry.mark_completed(
                    success=True,
                    message=f"Validation passed on retry attempt {retry_entry.retry_count}"
                )
                retry_result["success"] = True
                retry_result["message"] = "Retry succeeded - validation passed"
            elif retry_entry.retry_count >= retry_entry.max_retries:
                # Max retries reached
                retry_entry.mark_completed(
                    success=False,
                    message=f"Max retries reached ({retry_entry.max_retries})"
                )
                retry_result["message"] = "Max retries reached - validation still failing"
            else:
                # Can retry again
                retry_entry.retry_status = "failed"
                retry_result["message"] = f"Retry failed - {retry_entry.max_retries - retry_entry.retry_count} attempts remaining"
            
            retry_result["new_validation_log_id"] = new_validation_log.id
            
            self.db.commit()
            
            logger.info(
                f"Retry executed: retry_id={retry_id}, "
                f"success={success}, new_validation_id={new_validation_log.id}"
            )
            
        except Exception as e:
            logger.error(f"Retry execution failed: retry_id={retry_id}, error={str(e)}")
            
            # Record failure
            retry_entry.record_retry_attempt({
                "status": "error",
                "message": str(e),
                "executor": executor
            })
            
            if retry_entry.retry_count >= retry_entry.max_retries:
                retry_entry.mark_completed(
                    success=False,
                    message=f"Max retries reached with errors: {str(e)}"
                )
            else:
                retry_entry.retry_status = "failed"
            
            retry_result["message"] = f"Retry execution error: {str(e)}"
            
            self.db.commit()
            raise
        
        finally:
            retry_result["execution_time_ms"] = (time.time() - start_time) * 1000
        
        return retry_result
    
    def _rerun_validation(self, original_validation: ValidationLog) -> Dict:
        """Re-run a validation based on the original validation log
        
        NOTE: This is a placeholder implementation. In production, this would:
        1. Load the appropriate validator class
        2. Reconstruct the validation parameters from original_validation.details
        3. Load the dataset
        4. Execute the validator
        5. Return the ValidationResult
        
        For now, this simulates a retry by returning mock results.
        
        Args:
            original_validation: Original validation log
            
        Returns:
            Dictionary with validation results
        """
        logger.info(
            f"Re-running validation: dataset={original_validation.dataset_name}, "
            f"type={original_validation.validation_type}"
        )
        
        try:
            # Import services for validation re-execution
            from app.services.ingestion_service import IngestionService
            from app.services.validation_aggregator import ValidationAggregator
            from app.utils.spark_utils import get_spark
            import pandas as pd
            
            # Load dataset from storage
            ingestion_service = IngestionService()
            dataset_path = original_validation.dataset_name
            
            try:
                dataset_data = ingestion_service.load_processed_dataset(dataset_path)
            except FileNotFoundError:
                # Try raw bucket if processed not found
                raw_data = ingestion_service.load_raw_dataset(dataset_path)
                if dataset_path.endswith('.csv'):
                    from app.utils.csv_parser import parse_csv_bytes
                    dataset_data = parse_csv_bytes(raw_data)
                elif dataset_path.endswith('.json'):
                    from app.utils.json_parser import parse_json_bytes
                    dataset_data = parse_json_bytes(raw_data)
                else:
                    raise ValueError(f"Unsupported file format: {dataset_path}")
            
            # Convert to Spark DataFrame
            spark = get_spark()
            pandas_df = pd.DataFrame(dataset_data)
            df = spark.createDataFrame(pandas_df)
            
            # Execute validation
            validation_aggregator = ValidationAggregator()
            result = validation_aggregator.validate_with_defaults(
                df=df,
                dataset_name=original_validation.dataset_name,
                null_threshold=5.0
            )
            
            # Return validation results
            return {
                "status": "passed" if result.overall_passed else "failed",
                "total_records": result.total_records,
                "failed_records": result.failed_validators,
                "pass_rate": (result.passed_validators / result.total_validators * 100) if result.total_validators > 0 else 0,
                "execution_time_ms": result.total_execution_time_ms,
                "message": f"Validation re-executed: {result.passed_validators}/{result.total_validators} validators passed",
                "details": {
                    "overall_status": result.overall_status.value if hasattr(result.overall_status, 'value') else result.overall_status,
                    "validators": result.total_validators,
                    "passed": result.passed_validators,
                    "failed": result.failed_validators
                },
                "errors": [v.message for v in result.validators if not v.passed]
            }
            
        except Exception as e:
            logger.error(f"Error re-executing validation: {str(e)}")
            return {
                "status": "error",
                "total_records": original_validation.total_records,
                "failed_records": 0,
                "pass_rate": 0.0,
                "execution_time_ms": 0.0,
                "message": f"Validation re-execution failed: {str(e)}",
                "details": {"error": str(e)},
                "errors": [str(e)]
            }
    
    def bulk_execute_retries(
        self,
        retry_ids: list[int],
        executor: Optional[str] = None
    ) -> Dict:
        """Execute multiple retries in batch
        
        Args:
            retry_ids: List of retry queue entry IDs
            executor: Optional user executing the retries
            
        Returns:
            Dictionary with bulk execution results
        """
        results = {
            "total": len(retry_ids),
            "succeeded": 0,
            "failed": 0,
            "errors": [],
            "details": []
        }
        
        for retry_id in retry_ids:
            try:
                result = self.execute_retry(retry_id, executor)
                if result["success"]:
                    results["succeeded"] += 1
                else:
                    results["failed"] += 1
                results["details"].append(result)
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "retry_id": retry_id,
                    "error": str(e)
                })
                logger.error(f"Bulk retry failed for retry_id={retry_id}: {str(e)}")
        
        return results
