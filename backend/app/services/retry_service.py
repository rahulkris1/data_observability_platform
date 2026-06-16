"""Retry Service

Manages manual retry mechanism for failed validations
"""
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.models.retry_queue import RetryQueue
from app.models.validation_log import ValidationLog
from app.validators import BaseValidator, ValidationStatus

logger = logging.getLogger(__name__)


class RetryService:
    """Service for managing manual validation retries
    
    IMPORTANT: This service ONLY handles manual retries.
    NO automatic retries are performed.
    """
    
    def __init__(self, db: Session):
        """Initialize the retry service
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create_retry_request(
        self,
        validation_log_id: int,
        initiated_by: str,
        retry_reason: Optional[str] = None,
        max_retries: int = 3,
        retry_config: Optional[Dict] = None
    ) -> RetryQueue:
        """Create a manual retry request for a failed validation
        
        Args:
            validation_log_id: ID of the failed validation log
            initiated_by: User who initiated the retry
            retry_reason: Reason for retry request
            max_retries: Maximum number of retry attempts allowed
            retry_config: Optional configuration for retry behavior
            
        Returns:
            RetryQueue: Created retry queue entry
            
        Raises:
            ValueError: If validation log not found or not retryable
        """
        logger.info(f"Creating retry request: validation_log_id={validation_log_id}, user={initiated_by}")
        
        # Verify validation log exists and is in failed state
        validation_log = self.db.query(ValidationLog).filter(
            ValidationLog.id == validation_log_id
        ).first()
        
        if not validation_log:
            raise ValueError(f"Validation log not found: {validation_log_id}")
        
        if validation_log.status not in ["failed", "error"]:
            raise ValueError(f"Validation is not in failed state: {validation_log.status}")
        
        # Check if retry already exists and is pending/in_progress
        existing_retry = self.db.query(RetryQueue).filter(
            RetryQueue.validation_log_id == validation_log_id,
            RetryQueue.retry_status.in_(["pending", "in_progress"])
        ).first()
        
        if existing_retry:
            logger.warning(f"Retry already exists for validation_log_id={validation_log_id}")
            return existing_retry
        
        # Create retry request
        retry_entry = RetryQueue(
            validation_log_id=validation_log_id,
            retry_status="pending",
            retry_count=0,
            max_retries=max_retries,
            initiated_by=initiated_by,
            retry_reason=retry_reason,
            retry_config=retry_config or {}
        )
        
        self.db.add(retry_entry)
        self.db.commit()
        self.db.refresh(retry_entry)
        
        logger.info(f"Retry request created: retry_id={retry_entry.id}")
        return retry_entry
    
    def get_retry_status(self, retry_id: int) -> Optional[RetryQueue]:
        """Get status of a retry request
        
        Args:
            retry_id: ID of the retry queue entry
            
        Returns:
            RetryQueue entry or None if not found
        """
        return self.db.query(RetryQueue).filter(RetryQueue.id == retry_id).first()
    
    def get_retries_for_validation(self, validation_log_id: int) -> List[RetryQueue]:
        """Get all retry attempts for a validation log
        
        Args:
            validation_log_id: ID of the validation log
            
        Returns:
            List of retry queue entries
        """
        return self.db.query(RetryQueue).filter(
            RetryQueue.validation_log_id == validation_log_id
        ).order_by(RetryQueue.created_at.desc()).all()
    
    def get_pending_retries(self, limit: int = 100) -> List[RetryQueue]:
        """Get pending retry requests
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of pending retry queue entries
        """
        return self.db.query(RetryQueue).filter(
            RetryQueue.retry_status == "pending"
        ).order_by(RetryQueue.created_at).limit(limit).all()
    
    def get_failed_validations(
        self,
        dataset_name: Optional[str] = None,
        validation_type: Optional[str] = None,
        limit: int = 100
    ) -> List[ValidationLog]:
        """Get failed validations that can be retried
        
        Args:
            dataset_name: Optional filter by dataset name
            validation_type: Optional filter by validation type
            limit: Maximum number of entries to return
            
        Returns:
            List of failed validation logs
        """
        query = self.db.query(ValidationLog).filter(
            ValidationLog.status.in_(["failed", "error"])
        )
        
        if dataset_name:
            query = query.filter(ValidationLog.dataset_name == dataset_name)
        
        if validation_type:
            query = query.filter(ValidationLog.validation_type == validation_type)
        
        return query.order_by(ValidationLog.created_at.desc()).limit(limit).all()
    
    def cancel_retry(self, retry_id: int, cancelled_by: str) -> RetryQueue:
        """Cancel a pending retry request
        
        Args:
            retry_id: ID of the retry queue entry
            cancelled_by: User who cancelled the retry
            
        Returns:
            Updated retry queue entry
            
        Raises:
            ValueError: If retry not found or not cancellable
        """
        retry_entry = self.get_retry_status(retry_id)
        
        if not retry_entry:
            raise ValueError(f"Retry not found: {retry_id}")
        
        if retry_entry.retry_status not in ["pending", "in_progress"]:
            raise ValueError(f"Retry cannot be cancelled in state: {retry_entry.retry_status}")
        
        retry_entry.retry_status = "cancelled"
        retry_entry.completed_at = datetime.utcnow()
        retry_entry.error_message = f"Cancelled by {cancelled_by}"
        
        self.db.commit()
        self.db.refresh(retry_entry)
        
        logger.info(f"Retry cancelled: retry_id={retry_id}, cancelled_by={cancelled_by}")
        return retry_entry
    
    def get_retry_statistics(self, validation_log_id: Optional[int] = None) -> Dict:
        """Get retry statistics
        
        Args:
            validation_log_id: Optional filter by validation log ID
            
        Returns:
            Dictionary containing retry statistics
        """
        query = self.db.query(RetryQueue)
        
        if validation_log_id:
            query = query.filter(RetryQueue.validation_log_id == validation_log_id)
        
        total_retries = query.count()
        pending = query.filter(RetryQueue.retry_status == "pending").count()
        in_progress = query.filter(RetryQueue.retry_status == "in_progress").count()
        completed = query.filter(RetryQueue.retry_status == "completed").count()
        failed = query.filter(RetryQueue.retry_status == "failed").count()
        cancelled = query.filter(RetryQueue.retry_status == "cancelled").count()
        
        return {
            "total_retries": total_retries,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "failed": failed,
            "cancelled": cancelled,
            "success_rate": (completed / total_retries * 100) if total_retries > 0 else 0.0
        }
