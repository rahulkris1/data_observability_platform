"""Retry Audit Service

Stores and retrieves retry execution history and audit information
"""
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
import logging

from app.models.retry_queue import RetryQueue
from app.models.validation_log import ValidationLog

logger = logging.getLogger(__name__)


class RetryAuditService:
    """Service for auditing and tracking retry execution history"""
    
    def __init__(self, db: Session):
        """Initialize the retry audit service
        
        Args:
            db: Database session
        """
        self.db = db
    
    def get_retry_history(
        self,
        validation_log_id: Optional[int] = None,
        dataset_name: Optional[str] = None,
        status: Optional[str] = None,
        initiated_by: Optional[str] = None,
        days_back: int = 30,
        limit: int = 100,
        offset: int = 0
    ) -> Dict:
        """Get retry execution history with filters
        
        Args:
            validation_log_id: Filter by validation log ID
            dataset_name: Filter by dataset name
            status: Filter by retry status
            initiated_by: Filter by user who initiated
            days_back: Number of days to look back
            limit: Maximum number of records to return
            offset: Pagination offset
            
        Returns:
            Dictionary with retry history and metadata
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Build query with joins
        query = self.db.query(RetryQueue).join(
            ValidationLog,
            RetryQueue.validation_log_id == ValidationLog.id
        ).filter(RetryQueue.created_at >= cutoff_date)
        
        if validation_log_id:
            query = query.filter(RetryQueue.validation_log_id == validation_log_id)
        
        if dataset_name:
            query = query.filter(ValidationLog.dataset_name == dataset_name)
        
        if status:
            query = query.filter(RetryQueue.retry_status == status)
        
        if initiated_by:
            query = query.filter(RetryQueue.initiated_by == initiated_by)
        
        # Get total count
        total_count = query.count()
        
        # Get paginated results
        retries = query.order_by(
            RetryQueue.created_at.desc()
        ).limit(limit).offset(offset).all()
        
        return {
            "retries": [self._format_retry_entry(retry) for retry in retries],
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count
        }
    
    def get_retry_timeline(
        self,
        validation_log_id: int
    ) -> List[Dict]:
        """Get chronological timeline of retry attempts for a validation
        
        Args:
            validation_log_id: ID of the validation log
            
        Returns:
            List of retry attempts in chronological order
        """
        retries = self.db.query(RetryQueue).filter(
            RetryQueue.validation_log_id == validation_log_id
        ).order_by(RetryQueue.created_at).all()
        
        timeline = []
        for retry in retries:
            timeline.append({
                "retry_id": retry.id,
                "status": retry.retry_status,
                "attempt_number": retry.retry_count,
                "created_at": retry.created_at.isoformat(),
                "last_retry_at": retry.last_retry_at.isoformat() if retry.last_retry_at else None,
                "completed_at": retry.completed_at.isoformat() if retry.completed_at else None,
                "initiated_by": retry.initiated_by,
                "retry_reason": retry.retry_reason,
                "results": retry.retry_results or []
            })
        
        return timeline
    
    def get_retry_metrics(
        self,
        dataset_name: Optional[str] = None,
        days_back: int = 7
    ) -> Dict:
        """Get retry metrics and statistics
        
        Args:
            dataset_name: Optional filter by dataset name
            days_back: Number of days to analyze
            
        Returns:
            Dictionary with retry metrics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        query = self.db.query(RetryQueue).filter(
            RetryQueue.created_at >= cutoff_date
        )
        
        if dataset_name:
            query = query.join(ValidationLog).filter(
                ValidationLog.dataset_name == dataset_name
            )
        
        total_retries = query.count()
        
        # Status breakdown
        status_counts = {}
        for status in ["pending", "in_progress", "completed", "failed", "cancelled"]:
            count = query.filter(RetryQueue.retry_status == status).count()
            status_counts[status] = count
        
        # Success metrics
        completed_retries = self.db.query(RetryQueue).filter(
            and_(
                RetryQueue.created_at >= cutoff_date,
                RetryQueue.retry_status == "completed"
            )
        )
        
        if dataset_name:
            completed_retries = completed_retries.join(ValidationLog).filter(
                ValidationLog.dataset_name == dataset_name
            )
        
        successful_first_attempt = completed_retries.filter(
            RetryQueue.retry_count == 1
        ).count()
        
        # Average retry count for successful retries
        avg_retry_count = self.db.query(
            func.avg(RetryQueue.retry_count)
        ).filter(
            and_(
                RetryQueue.created_at >= cutoff_date,
                RetryQueue.retry_status == "completed"
            )
        )
        
        if dataset_name:
            avg_retry_count = avg_retry_count.join(ValidationLog).filter(
                ValidationLog.dataset_name == dataset_name
            )
        
        avg_count = avg_retry_count.scalar() or 0
        
        # Most retried validations
        most_retried = self.db.query(
            ValidationLog.dataset_name,
            ValidationLog.validation_type,
            func.count(RetryQueue.id).label("retry_count")
        ).join(RetryQueue).filter(
            RetryQueue.created_at >= cutoff_date
        ).group_by(
            ValidationLog.dataset_name,
            ValidationLog.validation_type
        ).order_by(
            func.count(RetryQueue.id).desc()
        ).limit(10).all()
        
        return {
            "total_retries": total_retries,
            "status_breakdown": status_counts,
            "success_rate": (status_counts["completed"] / total_retries * 100) if total_retries > 0 else 0,
            "first_attempt_success_rate": (successful_first_attempt / status_counts["completed"] * 100) if status_counts["completed"] > 0 else 0,
            "average_retry_count": round(avg_count, 2),
            "most_retried_validations": [
                {
                    "dataset_name": row[0],
                    "validation_type": row[1],
                    "retry_count": row[2]
                }
                for row in most_retried
            ],
            "period_days": days_back
        }
    
    def get_user_retry_activity(
        self,
        days_back: int = 30
    ) -> List[Dict]:
        """Get retry activity grouped by user
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            List of user activity statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        user_stats = self.db.query(
            RetryQueue.initiated_by,
            func.count(RetryQueue.id).label("total_retries"),
            func.sum(
                func.case((RetryQueue.retry_status == "completed", 1), else_=0)
            ).label("successful_retries"),
            func.sum(
                func.case((RetryQueue.retry_status == "failed", 1), else_=0)
            ).label("failed_retries"),
            func.sum(
                func.case((RetryQueue.retry_status == "pending", 1), else_=0)
            ).label("pending_retries")
        ).filter(
            RetryQueue.created_at >= cutoff_date
        ).group_by(
            RetryQueue.initiated_by
        ).all()
        
        return [
            {
                "user": row[0],
                "total_retries": row[1],
                "successful_retries": row[2] or 0,
                "failed_retries": row[3] or 0,
                "pending_retries": row[4] or 0,
                "success_rate": (row[2] / row[1] * 100) if row[1] > 0 and row[2] else 0
            }
            for row in user_stats
        ]
    
    def get_failure_insights(
        self,
        dataset_name: Optional[str] = None,
        days_back: int = 7
    ) -> Dict:
        """Get insights about validation failures and retry patterns
        
        Args:
            dataset_name: Optional filter by dataset name
            days_back: Number of days to analyze
            
        Returns:
            Dictionary with failure insights
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Get failed validations that have retries
        query = self.db.query(ValidationLog).join(RetryQueue).filter(
            and_(
                ValidationLog.status.in_(["failed", "error"]),
                RetryQueue.created_at >= cutoff_date
            )
        )
        
        if dataset_name:
            query = query.filter(ValidationLog.dataset_name == dataset_name)
        
        # Common failure reasons
        failure_patterns = {}
        for validation in query.all():
            if validation.message:
                # Extract failure pattern (simplified)
                pattern = validation.message[:100]  # First 100 chars
                if pattern not in failure_patterns:
                    failure_patterns[pattern] = {
                        "count": 0,
                        "validation_type": validation.validation_type,
                        "example_errors": []
                    }
                failure_patterns[pattern]["count"] += 1
                if validation.errors and len(failure_patterns[pattern]["example_errors"]) < 3:
                    failure_patterns[pattern]["example_errors"].extend(validation.errors[:3])
        
        # Sort by count
        top_patterns = sorted(
            [{"pattern": k, **v} for k, v in failure_patterns.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:10]
        
        return {
            "common_failure_patterns": top_patterns,
            "total_unique_patterns": len(failure_patterns),
            "analysis_period_days": days_back
        }
    
    def _format_retry_entry(self, retry: RetryQueue) -> Dict:
        """Format retry queue entry for API response
        
        Args:
            retry: RetryQueue entry
            
        Returns:
            Formatted dictionary
        """
        return {
            "retry_id": retry.id,
            "validation_log_id": retry.validation_log_id,
            "retry_status": retry.retry_status,
            "retry_count": retry.retry_count,
            "max_retries": retry.max_retries,
            "initiated_by": retry.initiated_by,
            "retry_reason": retry.retry_reason,
            "created_at": retry.created_at.isoformat(),
            "last_retry_at": retry.last_retry_at.isoformat() if retry.last_retry_at else None,
            "completed_at": retry.completed_at.isoformat() if retry.completed_at else None,
            "error_message": retry.error_message,
            "retry_results": retry.retry_results or [],
            "is_retryable": retry.is_retryable()
        }
