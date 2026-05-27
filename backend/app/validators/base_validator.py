"""Base validator interface for data quality checks."""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from pyspark.sql import DataFrame


class ValidationStatus(str, Enum):
    """Validation status enumeration."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    ERROR = "error"


class ValidationResult(BaseModel):
    """Reusable validation response model."""
    
    validator_name: str = Field(..., description="Name of the validator")
    status: ValidationStatus = Field(..., description="Validation status")
    passed: bool = Field(..., description="Whether validation passed")
    total_records: int = Field(0, description="Total number of records validated")
    failed_records: int = Field(0, description="Number of records that failed validation")
    pass_rate: float = Field(0.0, description="Percentage of records that passed (0-100)")
    
    message: str = Field("", description="Human-readable validation message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional validation details")
    errors: List[str] = Field(default_factory=list, description="List of errors encountered")
    
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Validation timestamp")
    execution_time_ms: Optional[float] = Field(None, description="Execution time in milliseconds")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BaseValidator(ABC):
    """
    Abstract base class for all data validators.
    
    Provides a standard interface for implementing validation logic
    with PySpark DataFrames.
    """
    
    def __init__(self, name: Optional[str] = None):
        """
        Initialize the validator.
        
        Args:
            name: Optional custom name for the validator
        """
        self.name = name or self.__class__.__name__
    
    @abstractmethod
    def validate(self, df: DataFrame, **kwargs) -> ValidationResult:
        """
        Validate the given DataFrame.
        
        Args:
            df: PySpark DataFrame to validate
            **kwargs: Additional validation parameters
            
        Returns:
            ValidationResult containing validation outcome and details
        """
        pass
    
    def _create_result(
        self,
        status: ValidationStatus,
        passed: bool,
        total_records: int = 0,
        failed_records: int = 0,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        errors: Optional[List[str]] = None,
        execution_time_ms: Optional[float] = None
    ) -> ValidationResult:
        """
        Helper method to create a ValidationResult.
        
        Args:
            status: Validation status
            passed: Whether validation passed
            total_records: Total number of records
            failed_records: Number of failed records
            message: Validation message
            details: Additional details dictionary
            errors: List of errors
            execution_time_ms: Execution time in milliseconds
            
        Returns:
            ValidationResult instance
        """
        pass_rate = 0.0
        if total_records > 0:
            pass_rate = ((total_records - failed_records) / total_records) * 100
        
        return ValidationResult(
            validator_name=self.name,
            status=status,
            passed=passed,
            total_records=total_records,
            failed_records=failed_records,
            pass_rate=round(pass_rate, 2),
            message=message,
            details=details or {},
            errors=errors or [],
            execution_time_ms=execution_time_ms
        )
