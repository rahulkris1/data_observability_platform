"""Audit Log ORM Model

Stores audit records for all validation executions and dataset operations
"""
from sqlalchemy import Column, String, Float, Integer, Text, JSON
from app.models.base import BaseModel


class AuditLog(BaseModel):
    """Audit Log model for tracking validation execution history
    
    Attributes:
        dataset_name: Name of the dataset being validated or processed
        validation_type: Type of validation executed (e.g., 'schema', 'null', 'datatype', 'checksum', 'integrity', 'aggregated')
        status: Execution status ('passed', 'failed', 'warning', 'error')
        execution_time_ms: Execution time in milliseconds
        total_records: Total number of records processed
        failed_records: Number of records that failed validation
        pass_rate: Percentage of records that passed (0-100)
        validator_name: Name of the validator that executed
        triggered_by: User or system that triggered the validation (e.g., 'system', 'scheduler', 'manual')
        environment: Environment where validation executed (e.g., 'dev', 'staging', 'production')
        extra_metadata: JSON structure with additional audit metadata (tags, context, configuration)
        error_summary: Summary of errors encountered
        details: JSON structure with detailed execution results
    """
    __tablename__ = "audit_logs"
    
    # Core audit fields
    dataset_name = Column(String(255), nullable=False, index=True)
    validation_type = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)
    execution_time_ms = Column(Float, nullable=True)
    
    # Validation metrics
    total_records = Column(Integer, nullable=False, default=0)
    failed_records = Column(Integer, nullable=False, default=0)
    pass_rate = Column(Float, nullable=False, default=0.0)
    
    # Validator information
    validator_name = Column(String(255), nullable=False)
    triggered_by = Column(String(100), nullable=True, default='system')
    environment = Column(String(50), nullable=True, default='dev')
    
    # Extended audit metadata
    extra_metadata = Column(JSON, nullable=True)
    error_summary = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)
    
    def __repr__(self) -> str:
        """String representation of the audit log"""
        return (
            f"<AuditLog(dataset={self.dataset_name}, "
            f"type={self.validation_type}, status={self.status}, "
            f"executed_at={self.created_at})>"
        )
