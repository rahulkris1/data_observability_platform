"""Retry Queue ORM Model

Stores retry requests and execution history for failed validations
"""
from sqlalchemy import Column, String, Integer, Text, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import BaseModel


class RetryQueue(BaseModel):
    """Retry Queue model for tracking validation retry requests
    
    Attributes:
        validation_log_id: Foreign key to the original failed validation
        retry_status: Current status ('pending', 'in_progress', 'completed', 'failed', 'cancelled')
        retry_count: Number of retry attempts made
        max_retries: Maximum number of retries allowed (default 3)
        initiated_by: User or system that initiated the retry
        retry_reason: Reason for retry request
        last_retry_at: Timestamp of the last retry attempt
        completed_at: Timestamp when retry completed (success or final failure)
        error_message: Error message if retry failed
        retry_config: JSON configuration for retry behavior
        retry_results: JSON array of retry attempt results
    """
    __tablename__ = "retry_queue"
    
    validation_log_id = Column(Integer, ForeignKey("validation_logs.id"), nullable=False, index=True)
    retry_status = Column(String(50), nullable=False, default="pending", index=True)
    
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    
    initiated_by = Column(String(255), nullable=False)
    retry_reason = Column(Text, nullable=True)
    
    last_retry_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    error_message = Column(Text, nullable=True)
    retry_config = Column(JSON, nullable=True)
    retry_results = Column(JSON, nullable=True, default=list)
    
    # Relationship to validation log
    validation_log = relationship("ValidationLog", backref="retry_attempts")
    
    def __repr__(self) -> str:
        """String representation of the retry queue entry"""
        return (
            f"<RetryQueue(validation_log_id={self.validation_log_id}, "
            f"status={self.retry_status}, count={self.retry_count}, "
            f"created_at={self.created_at})>"
        )
    
    def is_retryable(self) -> bool:
        """Check if this entry can be retried
        
        Returns:
            bool: True if retry is allowed, False otherwise
        """
        return (
            self.retry_status in ["pending", "failed"] and
            self.retry_count < self.max_retries
        )
    
    def record_retry_attempt(self, result: dict) -> None:
        """Record a retry attempt result
        
        Args:
            result: Dictionary containing retry attempt details
        """
        self.retry_count += 1
        self.last_retry_at = datetime.utcnow()
        
        if self.retry_results is None:
            self.retry_results = []
        
        self.retry_results.append({
            "attempt": self.retry_count,
            "timestamp": datetime.utcnow().isoformat(),
            **result
        })
    
    def mark_completed(self, success: bool, message: str = None) -> None:
        """Mark the retry as completed
        
        Args:
            success: Whether the retry succeeded
            message: Optional completion message
        """
        self.retry_status = "completed" if success else "failed"
        self.completed_at = datetime.utcnow()
        if message:
            self.error_message = message
