"""Audit Service

Provides functionality for storing and retrieving audit records for validation executions
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc

from app.models.audit_log import AuditLog


class AuditService:
    """Service for managing audit logs in PostgreSQL"""
    
    def __init__(self, db: Session):
        """
        Initialize the audit service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create_audit_record(
        self,
        dataset_name: str,
        validation_type: str,
        status: str,
        execution_time_ms: Optional[float] = None,
        total_records: int = 0,
        failed_records: int = 0,
        pass_rate: float = 0.0,
        validator_name: str = "",
        triggered_by: str = "system",
        environment: str = "dev",
        metadata: Optional[Dict[str, Any]] = None,
        error_summary: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Create and store a new audit record.
        
        Args:
            dataset_name: Name of the dataset being validated
            validation_type: Type of validation (e.g., 'schema', 'null', 'datatype', 'checksum', 'integrity')
            status: Execution status ('passed', 'failed', 'warning', 'error')
            execution_time_ms: Execution time in milliseconds
            total_records: Total number of records processed
            failed_records: Number of records that failed validation
            pass_rate: Percentage of records that passed (0-100)
            validator_name: Name of the validator that executed
            triggered_by: User or system that triggered the validation
            environment: Environment where validation executed
            metadata: Additional audit metadata (tags, context, configuration)
            error_summary: Summary of errors encountered
            details: Detailed execution results
            
        Returns:
            Created AuditLog instance
        """
        audit_log = AuditLog(
            dataset_name=dataset_name,
            validation_type=validation_type,
            status=status,
            execution_time_ms=execution_time_ms,
            total_records=total_records,
            failed_records=failed_records,
            pass_rate=pass_rate,
            validator_name=validator_name,
            triggered_by=triggered_by,
            environment=environment,
            metadata=metadata,
            error_summary=error_summary,
            details=details
        )
        
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        
        return audit_log
    
    def get_audit_history(
        self,
        dataset_name: Optional[str] = None,
        validation_type: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        triggered_by: Optional[str] = None,
        environment: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[AuditLog]:
        """
        Retrieve audit history with optional filtering and sorting.
        
        Args:
            dataset_name: Filter by dataset name (partial match)
            validation_type: Filter by validation type
            status: Filter by status
            start_date: Filter records created on or after this date
            end_date: Filter records created on or before this date
            triggered_by: Filter by who triggered the validation
            environment: Filter by environment
            limit: Maximum number of records to return
            offset: Number of records to skip (for pagination)
            sort_by: Field to sort by (created_at, dataset_name, validation_type, status, execution_time_ms)
            sort_order: Sort order ('asc' or 'desc')
            
        Returns:
            List of AuditLog instances matching the filters
        """
        query = self.db.query(AuditLog)
        
        # Apply filters
        if dataset_name:
            query = query.filter(AuditLog.dataset_name.ilike(f"%{dataset_name}%"))
        
        if validation_type:
            query = query.filter(AuditLog.validation_type == validation_type)
        
        if status:
            query = query.filter(AuditLog.status == status)
        
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
        
        if triggered_by:
            query = query.filter(AuditLog.triggered_by == triggered_by)
        
        if environment:
            query = query.filter(AuditLog.environment == environment)
        
        # Apply sorting
        sort_column = getattr(AuditLog, sort_by, AuditLog.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    def get_audit_count(
        self,
        dataset_name: Optional[str] = None,
        validation_type: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        triggered_by: Optional[str] = None,
        environment: Optional[str] = None
    ) -> int:
        """
        Get count of audit records matching the filters.
        
        Args:
            dataset_name: Filter by dataset name (partial match)
            validation_type: Filter by validation type
            status: Filter by status
            start_date: Filter records created on or after this date
            end_date: Filter records created on or before this date
            triggered_by: Filter by who triggered the validation
            environment: Filter by environment
            
        Returns:
            Count of matching records
        """
        query = self.db.query(func.count(AuditLog.id))
        
        # Apply filters (same as get_audit_history)
        if dataset_name:
            query = query.filter(AuditLog.dataset_name.ilike(f"%{dataset_name}%"))
        
        if validation_type:
            query = query.filter(AuditLog.validation_type == validation_type)
        
        if status:
            query = query.filter(AuditLog.status == status)
        
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
        
        if triggered_by:
            query = query.filter(AuditLog.triggered_by == triggered_by)
        
        if environment:
            query = query.filter(AuditLog.environment == environment)
        
        return query.scalar()
    
    def get_audit_by_id(self, audit_id: int) -> Optional[AuditLog]:
        """
        Retrieve a specific audit record by ID.
        
        Args:
            audit_id: ID of the audit record
            
        Returns:
            AuditLog instance or None if not found
        """
        return self.db.query(AuditLog).filter(AuditLog.id == audit_id).first()
    
    def get_audit_statistics(
        self,
        dataset_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated statistics from audit logs.
        
        Args:
            dataset_name: Filter by dataset name
            start_date: Filter records created on or after this date
            end_date: Filter records created on or before this date
            
        Returns:
            Dictionary with aggregated statistics
        """
        query = self.db.query(AuditLog)
        
        if dataset_name:
            query = query.filter(AuditLog.dataset_name == dataset_name)
        
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
        
        # Get counts by status
        status_counts = (
            self.db.query(AuditLog.status, func.count(AuditLog.id))
            .filter(AuditLog.id.in_([log.id for log in query.all()]))
            .group_by(AuditLog.status)
            .all()
        )
        
        # Get counts by validation type
        type_counts = (
            self.db.query(AuditLog.validation_type, func.count(AuditLog.id))
            .filter(AuditLog.id.in_([log.id for log in query.all()]))
            .group_by(AuditLog.validation_type)
            .all()
        )
        
        # Get average execution time
        avg_execution_time = (
            self.db.query(func.avg(AuditLog.execution_time_ms))
            .filter(AuditLog.id.in_([log.id for log in query.all()]))
            .scalar()
        )
        
        total_count = query.count()
        
        return {
            "total_audits": total_count,
            "status_distribution": {status: count for status, count in status_counts},
            "validation_type_distribution": {vtype: count for vtype, count in type_counts},
            "average_execution_time_ms": avg_execution_time or 0.0
        }
    
    def get_recent_audits(self, limit: int = 10) -> List[AuditLog]:
        """
        Get the most recent audit records.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of recent AuditLog instances
        """
        return (
            self.db.query(AuditLog)
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
            .all()
        )
    
    def delete_old_audits(self, days: int = 90) -> int:
        """
        Delete audit records older than specified number of days.
        
        Args:
            days: Delete records older than this many days
            
        Returns:
            Number of deleted records
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted_count = (
            self.db.query(AuditLog)
            .filter(AuditLog.created_at < cutoff_date)
            .delete()
        )
        self.db.commit()
        
        return deleted_count
