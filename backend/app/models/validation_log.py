"""Validation Log ORM Model

Stores validation execution results and history
"""
from sqlalchemy import Column, String, Float, Integer, Text, JSON
from app.models.base import BaseModel


class ValidationLog(BaseModel):
    """Validation Log model for storing validation execution results
    
    Attributes:
        dataset_name: Name of the validated dataset
        validation_type: Type of validation (e.g., 'schema', 'null', 'datatype', 'checksum', 'aggregated')
        status: Validation status ('passed', 'failed', 'warning', 'error')
        total_records: Total number of records validated
        failed_records: Number of records that failed validation
        pass_rate: Percentage of records that passed (0-100)
        execution_time_ms: Execution time in milliseconds
        validator_name: Name of the validator that executed
        message: Human-readable validation message
        details: JSON structure with detailed validation results
        errors: JSON array of error messages
    """
    __tablename__ = "validation_logs"
    
    dataset_name = Column(String(255), nullable=False, index=True)
    validation_type = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)
    
    total_records = Column(Integer, nullable=False, default=0)
    failed_records = Column(Integer, nullable=False, default=0)
    pass_rate = Column(Float, nullable=False, default=0.0)
    execution_time_ms = Column(Float, nullable=True)
    
    validator_name = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)
    errors = Column(JSON, nullable=True)
    
    def __repr__(self) -> str:
        """String representation of the validation log"""
        return (
            f"<ValidationLog(dataset={self.dataset_name}, "
            f"type={self.validation_type}, status={self.status}, "
            f"executed_at={self.created_at})>"
        )
