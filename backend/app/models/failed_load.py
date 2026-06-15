"""Failed Load ORM Model

Tracks failed warehouse loads with failure reasons and details
"""
from sqlalchemy import Column, String, Integer, Text, JSON, DateTime, Boolean
from datetime import datetime
from app.models.base import BaseModel


class FailedLoad(BaseModel):
    """Failed Load model for tracking failed warehouse batch loads
    
    Attributes:
        batch_id: Unique identifier for the failed batch load
        dataset_name: Name of the dataset that failed to load
        source_system: System from which data originated
        load_started_at: When the load operation started
        load_failed_at: When the load operation failed
        failure_reason: Primary reason for failure
        error_message: Detailed error message or stack trace
        source_record_count: Number of records in source
        warehouse_record_count: Number of records successfully loaded to warehouse
        failed_record_count: Number of records that failed to load
        retry_count: Number of retry attempts made
        can_retry: Flag indicating if load can be retried
        retry_validated_at: When retry validation was last performed
        retry_validated_by: User who validated the retry
        metadata: Additional context and diagnostic information
    """
    __tablename__ = "failed_loads"
    
    batch_id = Column(String(100), nullable=False, unique=True, index=True)
    dataset_name = Column(String(255), nullable=False, index=True)
    source_system = Column(String(255), nullable=True)
    
    load_started_at = Column(DateTime, nullable=True)
    load_failed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    failure_reason = Column(String(500), nullable=False)
    error_message = Column(Text, nullable=True)
    
    source_record_count = Column(Integer, nullable=True)
    warehouse_record_count = Column(Integer, nullable=True)
    failed_record_count = Column(Integer, nullable=True)
    
    retry_count = Column(Integer, default=0, nullable=False)
    can_retry = Column(Boolean, default=False, nullable=False)
    retry_validated_at = Column(DateTime, nullable=True)
    retry_validated_by = Column(String(255), nullable=True)
    
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self) -> str:
        """String representation of the failed load record"""
        return (
            f"<FailedLoad(batch_id={self.batch_id}, "
            f"dataset={self.dataset_name}, retries={self.retry_count})>"
        )


class LoadAuditLog(BaseModel):
    """Load Audit Log model for tracking all batch execution events
    
    Attributes:
        batch_id: Unique identifier for the batch load
        dataset_name: Name of the dataset being loaded
        source_system: System from which data originated
        load_status: Status of the load (started, completed, failed, retrying)
        load_started_at: When the load operation started
        load_completed_at: When the load operation completed
        source_record_count: Number of records in source
        warehouse_record_count: Number of records loaded to warehouse
        records_inserted: Number of new records inserted
        records_updated: Number of existing records updated
        records_failed: Number of records that failed
        execution_time_seconds: Total execution time in seconds
        triggered_by: User or system that triggered the load
        notes: Additional notes or context
        metadata: Additional diagnostic information
    """
    __tablename__ = "load_audit_logs"
    
    batch_id = Column(String(100), nullable=False, index=True)
    dataset_name = Column(String(255), nullable=False, index=True)
    source_system = Column(String(255), nullable=True)
    
    load_status = Column(String(50), nullable=False, index=True)  # started, completed, failed, retrying
    load_started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    load_completed_at = Column(DateTime, nullable=True)
    
    source_record_count = Column(Integer, nullable=True)
    warehouse_record_count = Column(Integer, nullable=True)
    records_inserted = Column(Integer, nullable=True)
    records_updated = Column(Integer, nullable=True)
    records_failed = Column(Integer, nullable=True)
    
    execution_time_seconds = Column(Integer, nullable=True)
    triggered_by = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self) -> str:
        """String representation of the audit log record"""
        return (
            f"<LoadAuditLog(batch_id={self.batch_id}, "
            f"status={self.load_status}, dataset={self.dataset_name})>"
        )
