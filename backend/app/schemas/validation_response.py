"""Validation response schemas for API endpoints."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ValidationExecutionRequest(BaseModel):
    """Request model for validation execution."""
    
    dataset_name: str = Field(..., description="Name of the dataset to validate", min_length=1)
    dataset_path: Optional[str] = Field(None, description="Optional MinIO path to dataset")
    validation_types: Optional[List[str]] = Field(
        None,
        description="Optional list of specific validation types to run (e.g., 'schema', 'null', 'datatype')"
    )
    schema_contract_id: Optional[int] = Field(None, description="Optional schema contract ID to validate against")
    null_threshold: Optional[float] = Field(5.0, description="Maximum allowed null percentage", ge=0, le=100)
    
    class Config:
        schema_extra = {
            "example": {
                "dataset_name": "customers.csv",
                "validation_types": ["schema", "null", "datatype"],
                "null_threshold": 5.0
            }
        }


class ValidatorResultResponse(BaseModel):
    """Response model for individual validator result."""
    
    validator_name: str = Field(..., description="Name of the validator")
    status: str = Field(..., description="Validation status (passed/failed/warning/error)")
    passed: bool = Field(..., description="Whether validation passed")
    total_records: int = Field(0, description="Total number of records validated")
    failed_records: int = Field(0, description="Number of records that failed")
    pass_rate: float = Field(0.0, description="Percentage of records that passed (0-100)")
    message: str = Field("", description="Validation message")
    execution_time_ms: Optional[float] = Field(None, description="Execution time in milliseconds")
    errors: List[str] = Field(default_factory=list, description="List of errors encountered")


class ValidationExecutionResponse(BaseModel):
    """Response model for validation execution."""
    
    dataset_name: str = Field(..., description="Name of the validated dataset")
    validation_timestamp: datetime = Field(..., description="When validation was performed")
    overall_status: str = Field(..., description="Overall validation status")
    overall_passed: bool = Field(..., description="Whether all validations passed")
    total_validators: int = Field(0, description="Total number of validators executed")
    passed_validators: int = Field(0, description="Number of validators that passed")
    failed_validators: int = Field(0, description="Number of validators that failed")
    warning_validators: int = Field(0, description="Number of validators with warnings")
    error_validators: int = Field(0, description="Number of validators with errors")
    total_records: int = Field(0, description="Total records in dataset")
    total_execution_time_ms: float = Field(0.0, description="Total execution time in milliseconds")
    validators: List[ValidatorResultResponse] = Field(default_factory=list, description="Individual validator results")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "dataset_name": "customers.csv",
                "validation_timestamp": "2026-06-04T10:30:00",
                "overall_status": "passed",
                "overall_passed": True,
                "total_validators": 3,
                "passed_validators": 3,
                "failed_validators": 0,
                "warning_validators": 0,
                "error_validators": 0,
                "total_records": 1000,
                "total_execution_time_ms": 245.5,
                "validators": [
                    {
                        "validator_name": "SchemaValidator",
                        "status": "passed",
                        "passed": True,
                        "total_records": 1000,
                        "failed_records": 0,
                        "pass_rate": 100.0,
                        "message": "All columns match schema",
                        "execution_time_ms": 85.2,
                        "errors": []
                    }
                ],
                "metadata": {}
            }
        }


class AuditHistoryItem(BaseModel):
    """Response model for a single audit history item."""
    
    id: int = Field(..., description="Audit log ID")
    dataset_name: str = Field(..., description="Name of the dataset")
    validation_type: str = Field(..., description="Type of validation")
    status: str = Field(..., description="Execution status")
    validator_name: str = Field("", description="Name of the validator")
    total_records: int = Field(0, description="Total records processed")
    failed_records: int = Field(0, description="Failed records")
    pass_rate: float = Field(0.0, description="Pass rate percentage")
    execution_time_ms: Optional[float] = Field(None, description="Execution time in milliseconds")
    triggered_by: str = Field("system", description="User or system that triggered validation")
    environment: str = Field("dev", description="Environment where validation was executed")
    created_at: datetime = Field(..., description="When the audit log was created")
    error_summary: Optional[str] = Field(None, description="Summary of errors")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AuditHistoryResponse(BaseModel):
    """Response model for audit history."""
    
    total_count: int = Field(..., description="Total number of audit records matching filters")
    items: List[AuditHistoryItem] = Field(..., description="List of audit history items")
    limit: int = Field(..., description="Number of items per page")
    offset: int = Field(..., description="Offset for pagination")
    
    class Config:
        schema_extra = {
            "example": {
                "total_count": 150,
                "items": [
                    {
                        "id": 1,
                        "dataset_name": "customers.csv",
                        "validation_type": "schema",
                        "status": "passed",
                        "validator_name": "SchemaValidator",
                        "total_records": 1000,
                        "failed_records": 0,
                        "pass_rate": 100.0,
                        "execution_time_ms": 85.2,
                        "triggered_by": "system",
                        "environment": "dev",
                        "created_at": "2026-06-04T10:30:00",
                        "error_summary": None
                    }
                ],
                "limit": 100,
                "offset": 0
            }
        }


class APIErrorDetail(BaseModel):
    """Detailed error information."""
    
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    type: Optional[str] = Field(None, description="Error type")


class APIErrorResponse(BaseModel):
    """API error response model."""
    
    status_code: int = Field(..., description="HTTP status code")
    error: str = Field(..., description="Error type or category")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[List[APIErrorDetail]] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the error occurred")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "status_code": 400,
                "error": "ValidationError",
                "message": "Invalid request parameters",
                "details": [
                    {
                        "field": "dataset_name",
                        "message": "Field required",
                        "type": "value_error.missing"
                    }
                ],
                "timestamp": "2026-06-04T10:30:00"
            }
        }
