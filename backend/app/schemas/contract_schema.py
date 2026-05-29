"""Schema Contract Pydantic Schemas

Defines request/response models for schema contract validation
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class DataType(str, Enum):
    """Supported data types for schema validation"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    TIMESTAMP = "timestamp"


class ColumnDefinition(BaseModel):
    """Definition of a single column in a schema contract"""
    name: str = Field(..., description="Column name")
    data_type: DataType = Field(..., description="Expected data type")
    required: bool = Field(default=True, description="Whether column is required")
    nullable: bool = Field(default=False, description="Whether column can contain null values")
    
    class Config:
        use_enum_values = True


class SchemaDefinition(BaseModel):
    """Schema definition containing column specifications"""
    columns: List[ColumnDefinition] = Field(..., description="List of column definitions")


class SchemaContractCreate(BaseModel):
    """Schema for creating a new schema contract"""
    name: str = Field(..., description="Unique contract name")
    description: Optional[str] = Field(None, description="Contract description")
    dataset_name: str = Field(..., description="Dataset name this contract applies to")
    version: str = Field(default="1.0.0", description="Contract version")
    is_active: bool = Field(default=True, description="Whether contract is active")
    schema_definition: SchemaDefinition = Field(..., description="Schema definition")


class SchemaContractResponse(BaseModel):
    """Schema for schema contract response"""
    id: int
    name: str
    description: Optional[str]
    dataset_name: str
    version: str
    is_active: bool
    schema_definition: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ValidationError(BaseModel):
    """Details of a single validation error"""
    error_type: str = Field(..., description="Type of error (e.g., 'missing_column', 'type_mismatch')")
    column_name: Optional[str] = Field(None, description="Column name where error occurred")
    expected: Optional[str] = Field(None, description="Expected value")
    actual: Optional[str] = Field(None, description="Actual value")
    message: str = Field(..., description="Human-readable error message")


class ContractValidationResult(BaseModel):
    """Result of validating a dataset against a schema contract"""
    is_valid: bool = Field(..., description="Whether validation passed")
    contract_name: str = Field(..., description="Name of the contract used")
    dataset_name: str = Field(..., description="Name of the dataset validated")
    errors: List[ValidationError] = Field(default_factory=list, description="List of validation errors")
    validated_at: datetime = Field(default_factory=datetime.utcnow, description="When validation was performed")
    total_columns_expected: int = Field(..., description="Number of columns in contract")
    total_columns_actual: int = Field(..., description="Number of columns in dataset")


class ContractValidationSummary(BaseModel):
    """Summary of contract validation results"""
    total_validations: int = Field(default=0, description="Total number of validations performed")
    passed: int = Field(default=0, description="Number of validations that passed")
    failed: int = Field(default=0, description="Number of validations that failed")
    success_rate: float = Field(default=0.0, description="Percentage of successful validations")


class ValidateDatasetRequest(BaseModel):
    """Request to validate a dataset against a contract"""
    contract_name: str = Field(..., description="Name of the contract to validate against")
    dataset_columns: List[Dict[str, str]] = Field(
        ..., 
        description="List of dataset columns with name and data_type"
    )
    # Example: [{"name": "customer_id", "data_type": "integer"}, ...]
