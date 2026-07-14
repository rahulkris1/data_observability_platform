"""Schemas for referential integrity validation results."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.validators.base_validator import ValidationStatus


class FailedRowRecord(BaseModel):
    """Single failed row record from integrity validation."""
    
    row_data: Dict[str, Any] = Field(..., description="The actual row data that failed validation")
    failure_type: str = Field(..., description="Type of failure (duplicate_primary_key, orphan_foreign_key)")
    failure_details: Dict[str, Any] = Field(default_factory=dict, description="Additional failure context")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FailedRowsResponse(BaseModel):
    """Response model for failed row extraction."""
    
    dataset_name: str = Field(..., description="Name of the dataset")
    validation_type: str = Field(..., description="Type of validation that failed")
    total_failed_rows: int = Field(0, description="Total number of failed rows")
    failed_rows: List[FailedRowRecord] = Field(default_factory=list, description="List of failed row records")
    extracted_at: datetime = Field(default_factory=datetime.utcnow, description="When failed rows were extracted")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DuplicateKeyInfo(BaseModel):
    """Information about a duplicate primary key."""
    
    key_values: Dict[str, Any] = Field(..., description="The duplicate key column values")
    occurrence_count: int = Field(..., description="Number of times this key appears")


class OrphanForeignKeyInfo(BaseModel):
    """Information about orphan foreign key records."""
    
    foreign_key_column: str = Field(..., description="Name of the foreign key column")
    parent_dataset: str = Field(..., description="Name of the parent dataset")
    parent_key_column: str = Field(..., description="Name of the parent key column")
    orphan_count: int = Field(0, description="Number of orphan records")
    sample_orphan_values: List[Any] = Field(default_factory=list, description="Sample orphan values")


class PrimaryKeyValidationResult(BaseModel):
    """Result of primary key uniqueness validation."""
    
    has_duplicates: bool = Field(..., description="Whether duplicates were found")
    duplicate_count: int = Field(0, description="Number of duplicate records")
    unique_duplicate_keys: int = Field(0, description="Number of unique duplicate key combinations")
    duplicate_keys: List[Dict[str, Any]] = Field(default_factory=list, description="Sample duplicate keys")


class ForeignKeyValidationResult(BaseModel):
    """Result of foreign key validation."""
    
    foreign_key_column: str = Field(..., description="Foreign key column name")
    valid: bool = Field(..., description="Whether foreign key validation passed")
    orphan_count: int = Field(0, description="Number of orphan records")
    parent_dataset: Optional[str] = Field(None, description="Parent dataset name")
    parent_key_column: Optional[str] = Field(None, description="Parent key column name")
    orphan_values: List[Any] = Field(default_factory=list, description="Sample orphan values")
    error: Optional[str] = Field(None, description="Error message if validation failed")


class IntegrityValidationSummary(BaseModel):
    """Summary of integrity validation execution."""
    
    dataset_name: str = Field(..., description="Name of the validated dataset")
    validation_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When validation was performed")
    
    status: ValidationStatus = Field(..., description="Overall validation status")
    passed: bool = Field(..., description="Whether validation passed")
    
    total_records: int = Field(0, description="Total records validated")
    failed_records: int = Field(0, description="Number of records that failed")
    pass_rate: float = Field(0.0, description="Percentage of records that passed")
    
    primary_key_validation: Optional[PrimaryKeyValidationResult] = Field(None, description="Primary key validation result")
    foreign_key_validations: List[ForeignKeyValidationResult] = Field(default_factory=list, description="Foreign key validation results")
    
    execution_time_ms: Optional[float] = Field(None, description="Execution time in milliseconds")
    errors: List[str] = Field(default_factory=list, description="List of errors")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        use_enum_values = True


class IntegrityViolation(BaseModel):
    """Single integrity violation record for display."""
    
    id: int = Field(..., description="Violation ID")
    dataset_name: str = Field(..., description="Dataset name")
    validation_type: str = Field(..., description="Type of integrity validation")
    violation_type: str = Field(..., description="Specific violation (duplicate_pk, orphan_fk)")
    
    status: str = Field(..., description="Validation status")
    failed_records: int = Field(0, description="Number of failed records")
    
    failure_reason: str = Field(..., description="Human-readable failure reason")
    failure_details: Dict[str, Any] = Field(default_factory=dict, description="Detailed failure information")
    
    executed_at: datetime = Field(..., description="When the validation was executed")
    execution_time_ms: Optional[float] = Field(None, description="Execution time")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        from_attributes = True


class IntegrityViolationsResponse(BaseModel):
    """Response model for integrity violations listing."""
    
    total_violations: int = Field(0, description="Total number of violations")
    violations: List[IntegrityViolation] = Field(default_factory=list, description="List of integrity violations")
    
    filters_applied: Dict[str, Any] = Field(default_factory=dict, description="Filters that were applied")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
