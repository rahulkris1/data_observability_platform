"""Validation summary schemas for aggregated validation results."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from app.validators.base_validator import ValidationStatus


class ValidatorSummary(BaseModel):
    """Summary for a single validator execution."""
    
    validator_name: str = Field(..., description="Name of the validator")
    status: ValidationStatus = Field(..., description="Validation status")
    passed: bool = Field(..., description="Whether validation passed")
    total_records: int = Field(0, description="Total number of records validated")
    failed_records: int = Field(0, description="Number of records that failed")
    pass_rate: float = Field(0.0, description="Percentage of records that passed")
    message: str = Field("", description="Validation message")
    execution_time_ms: Optional[float] = Field(None, description="Execution time in milliseconds")
    errors: List[str] = Field(default_factory=list, description="List of errors")
    
    class Config:
        use_enum_values = True


class ValidationSummary(BaseModel):
    """Aggregated summary of all validation results."""
    
    dataset_name: str = Field(..., description="Name of the validated dataset")
    validation_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When validation was performed")
    
    overall_status: ValidationStatus = Field(..., description="Overall validation status")
    overall_passed: bool = Field(..., description="Whether all validations passed")
    
    total_validators: int = Field(0, description="Total number of validators executed")
    passed_validators: int = Field(0, description="Number of validators that passed")
    failed_validators: int = Field(0, description="Number of validators that failed")
    warning_validators: int = Field(0, description="Number of validators with warnings")
    error_validators: int = Field(0, description="Number of validators with errors")
    
    total_records: int = Field(0, description="Total records in dataset")
    total_execution_time_ms: float = Field(0.0, description="Total execution time in milliseconds")
    
    validators: List[ValidatorSummary] = Field(default_factory=list, description="Individual validator results")
    
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        use_enum_values = True


class ValidationHistoryItem(BaseModel):
    """Single validation history record."""
    
    id: int
    dataset_name: str
    validation_type: str
    status: str
    executed_at: datetime
    execution_time_ms: Optional[float] = None
    total_records: int = 0
    failed_records: int = 0
    pass_rate: float = 0.0
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        from_attributes = True


class ValidationMetrics(BaseModel):
    """Validation metrics for dashboard."""
    
    total_validations: int = Field(0, description="Total validations executed")
    passed_validations: int = Field(0, description="Validations that passed")
    failed_validations: int = Field(0, description="Validations that failed")
    warning_validations: int = Field(0, description="Validations with warnings")
    average_pass_rate: float = Field(0.0, description="Average pass rate percentage")
    
    class Config:
        use_enum_values = True
