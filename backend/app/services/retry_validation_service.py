"""Retry Validation Service

Validates failed loads before manual retry - NO automatic retries
"""
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.models.failed_load import FailedLoad
from app.models.warehouse_tables import WarehouseStagingData
from app.services.load_verification_service import LoadVerificationService

logger = logging.getLogger(__name__)


class RetryValidationService:
    """Service for validating failed loads before manual retry
    
    IMPORTANT: This service only validates and marks loads as ready for retry.
    It does NOT perform automatic retries. Retry execution must be manual.
    """
    
    def __init__(self, db: Session):
        """Initialize the retry validation service
        
        Args:
            db: Database session
        """
        self.db = db
        self.verification_service = LoadVerificationService(db)
    
    def validate_for_retry(
        self,
        batch_id: str,
        validated_by: str,
        validation_notes: Optional[str] = None
    ) -> Dict:
        """Validate a failed load and mark it as ready for manual retry
        
        Performs validation checks to ensure the load is safe to retry.
        Does NOT execute the retry - that must be done manually.
        
        Args:
            batch_id: Unique identifier for the failed batch
            validated_by: User performing the validation
            validation_notes: Optional notes about the validation
            
        Returns:
            Dict containing validation results:
                - can_retry: Whether the load can be retried
                - validation_status: Overall validation status
                - checks_passed: List of passed validation checks
                - checks_failed: List of failed validation checks
                - recommendations: List of recommendations before retry
        """
        logger.info(f"Validating failed load for retry: batch_id={batch_id}, validator={validated_by}")
        
        # Get failed load record
        failed_load = self.db.query(FailedLoad).filter(
            FailedLoad.batch_id == batch_id
        ).first()
        
        if not failed_load:
            raise ValueError(f"No failed load found for batch_id: {batch_id}")
        
        # Perform validation checks
        checks_passed = []
        checks_failed = []
        recommendations = []
        
        # Check 1: Verify staging data still exists
        staging_count = self.db.query(WarehouseStagingData).filter(
            WarehouseStagingData.batch_id == batch_id
        ).count()
        
        if staging_count > 0:
            checks_passed.append(f"Staging data exists ({staging_count} records)")
        else:
            checks_failed.append("No staging data found - may need to re-ingest")
            recommendations.append("Re-ingest source data before retry")
        
        # Check 2: Verify failure reason is retryable
        retryable_reasons = [
            "timeout",
            "network_error",
            "temporary_error",
            "resource_limit",
            "connection_error"
        ]
        
        failure_reason_lower = failed_load.failure_reason.lower()
        is_retryable = any(reason in failure_reason_lower for reason in retryable_reasons)
        
        if is_retryable:
            checks_passed.append("Failure reason is retryable")
        else:
            checks_failed.append("Failure reason may not be retryable - review required")
            recommendations.append(f"Review failure reason: {failed_load.failure_reason}")
        
        # Check 3: Check retry count
        if failed_load.retry_count < 3:
            checks_passed.append(f"Retry count acceptable ({failed_load.retry_count}/3)")
        else:
            checks_failed.append(f"Maximum retry attempts reached ({failed_load.retry_count})")
            recommendations.append("Investigate root cause before further retries")
        
        # Check 4: Verify no partial data in warehouse (data integrity)
        warehouse_count = self.verification_service.verify_batch_load(
            batch_id=batch_id,
            dataset_name=failed_load.dataset_name
        ).get("warehouse_count", 0)
        
        if warehouse_count == 0:
            checks_passed.append("No partial data in warehouse (clean retry)")
        else:
            checks_failed.append(f"Partial data exists in warehouse ({warehouse_count} records)")
            recommendations.append("Clean up partial warehouse data before retry")
        
        # Check 5: Time since last failure (cooling-off period)
        hours_since_failure = (datetime.utcnow() - failed_load.load_failed_at).total_seconds() / 3600
        
        if hours_since_failure >= 1:
            checks_passed.append(f"Sufficient time elapsed since failure ({hours_since_failure:.1f}h)")
        else:
            checks_failed.append("Recent failure - consider waiting before retry")
            recommendations.append("Wait at least 1 hour between retry attempts")
        
        # Determine if retry is allowed
        can_retry = len(checks_failed) == 0
        validation_status = "READY_FOR_RETRY" if can_retry else "NOT_READY"
        
        # Update failed load record
        failed_load.can_retry = can_retry
        failed_load.retry_validated_at = datetime.utcnow()
        failed_load.retry_validated_by = validated_by
        
        if failed_load.metadata is None:
            failed_load.metadata = {}
        
        failed_load.metadata.update({
            "validation_status": validation_status,
            "validation_notes": validation_notes,
            "validated_at": datetime.utcnow().isoformat(),
            "validated_by": validated_by
        })
        
        self.db.commit()
        self.db.refresh(failed_load)
        
        result = {
            "batch_id": batch_id,
            "can_retry": can_retry,
            "validation_status": validation_status,
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "recommendations": recommendations,
            "retry_count": failed_load.retry_count,
            "validated_by": validated_by,
            "validated_at": datetime.utcnow().isoformat()
        }
        
        logger.info(
            f"Retry validation complete: batch_id={batch_id}, "
            f"can_retry={can_retry}, status={validation_status}"
        )
        
        return result
    
    def get_retry_ready_loads(
        self,
        dataset_name: Optional[str] = None,
        limit: int = 50
    ) -> List[FailedLoad]:
        """Get list of failed loads that are validated and ready for manual retry
        
        Args:
            dataset_name: Optional filter by dataset name
            limit: Maximum number of records to return
            
        Returns:
            List of FailedLoad instances ready for retry
        """
        query = self.db.query(FailedLoad).filter(
            FailedLoad.can_retry == True
        )
        
        if dataset_name:
            query = query.filter(FailedLoad.dataset_name == dataset_name)
        
        return query.order_by(FailedLoad.load_failed_at).limit(limit).all()
    
    def get_failed_loads_summary(
        self,
        dataset_name: Optional[str] = None
    ) -> Dict:
        """Get summary of all failed loads grouped by status
        
        Args:
            dataset_name: Optional filter by dataset name
            
        Returns:
            Dict containing failed loads summary
        """
        query = self.db.query(FailedLoad)
        
        if dataset_name:
            query = query.filter(FailedLoad.dataset_name == dataset_name)
        
        all_failed = query.all()
        
        total_failed = len(all_failed)
        ready_for_retry = sum(1 for load in all_failed if load.can_retry)
        needs_validation = sum(1 for load in all_failed if not load.can_retry and load.retry_validated_at is None)
        max_retries_reached = sum(1 for load in all_failed if load.retry_count >= 3)
        
        # Group by failure reason
        failure_reasons = {}
        for load in all_failed:
            reason = load.failure_reason
            if reason not in failure_reasons:
                failure_reasons[reason] = 0
            failure_reasons[reason] += 1
        
        return {
            "total_failed_loads": total_failed,
            "ready_for_retry": ready_for_retry,
            "needs_validation": needs_validation,
            "max_retries_reached": max_retries_reached,
            "failure_reasons": failure_reasons,
            "dataset_name": dataset_name
        }
    
    def revoke_retry_approval(
        self,
        batch_id: str,
        revoked_by: str,
        reason: Optional[str] = None
    ) -> FailedLoad:
        """Revoke retry approval for a failed load
        
        Args:
            batch_id: Unique identifier for the batch
            revoked_by: User revoking the approval
            reason: Reason for revocation
            
        Returns:
            Updated FailedLoad instance
        """
        logger.info(f"Revoking retry approval: batch_id={batch_id}, revoked_by={revoked_by}")
        
        failed_load = self.db.query(FailedLoad).filter(
            FailedLoad.batch_id == batch_id
        ).first()
        
        if not failed_load:
            raise ValueError(f"No failed load found for batch_id: {batch_id}")
        
        failed_load.can_retry = False
        failed_load.retry_validated_at = None
        failed_load.retry_validated_by = None
        
        if failed_load.metadata is None:
            failed_load.metadata = {}
        
        failed_load.metadata.update({
            "retry_revoked": True,
            "revoked_at": datetime.utcnow().isoformat(),
            "revoked_by": revoked_by,
            "revocation_reason": reason
        })
        
        self.db.commit()
        self.db.refresh(failed_load)
        
        logger.info(f"Retry approval revoked: batch_id={batch_id}")
        return failed_load
    
    def get_validation_history(
        self,
        batch_id: str
    ) -> Dict:
        """Get validation history for a failed load
        
        Args:
            batch_id: Unique identifier for the batch
            
        Returns:
            Dict containing validation history
        """
        failed_load = self.db.query(FailedLoad).filter(
            FailedLoad.batch_id == batch_id
        ).first()
        
        if not failed_load:
            raise ValueError(f"No failed load found for batch_id: {batch_id}")
        
        return {
            "batch_id": batch_id,
            "dataset_name": failed_load.dataset_name,
            "failure_reason": failed_load.failure_reason,
            "retry_count": failed_load.retry_count,
            "can_retry": failed_load.can_retry,
            "retry_validated_at": failed_load.retry_validated_at.isoformat() if failed_load.retry_validated_at else None,
            "retry_validated_by": failed_load.retry_validated_by,
            "load_failed_at": failed_load.load_failed_at.isoformat() if failed_load.load_failed_at else None,
            "metadata": failed_load.metadata or {}
        }
