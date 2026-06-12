"""Warehouse response schemas for API endpoints"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class WarehouseLoadRequest(BaseModel):
    """Request model for warehouse load execution"""
    
    dataset_name: str = Field(..., description="Name of the dataset to load", min_length=1)
    records: List[Dict[str, Any]] = Field(..., description="List of records to load")
    source_system: Optional[str] = Field(None, description="Source system name")
    load_type: str = Field('incremental', description="Type of load (incremental, full_refresh, initial)")
    batch_size: Optional[int] = Field(1000, description="Batch size for processing", ge=100, le=10000)
    enable_deduplication: Optional[bool] = Field(True, description="Enable duplicate detection")
    skip_duplicates: Optional[bool] = Field(True, description="Skip duplicates instead of failing")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    class Config:
        schema_extra = {
            "example": {
                "dataset_name": "customers",
                "records": [
                    {"id": "1", "name": "John Doe", "email": "john@example.com"},
                    {"id": "2", "name": "Jane Smith", "email": "jane@example.com"}
                ],
                "source_system": "sales_db",
                "load_type": "incremental",
                "batch_size": 1000
            }
        }


class WarehouseLoadResponse(BaseModel):
    """Response model for warehouse load execution"""
    
    batch_id: str = Field(..., description="Unique batch identifier")
    status: str = Field(..., description="Load status (completed, failed, running, rolled_back)")
    dataset_name: str = Field(..., description="Name of the dataset")
    records_attempted: int = Field(0, description="Total number of records attempted")
    records_loaded: int = Field(0, description="Number of records successfully loaded")
    records_duplicate: int = Field(0, description="Number of duplicate records skipped")
    records_failed: int = Field(0, description="Number of records that failed")
    execution_duration_ms: float = Field(0.0, description="Execution time in milliseconds")
    load_timestamp: datetime = Field(..., description="When the load was executed")
    error_message: Optional[str] = Field(None, description="Error message if load failed")
    errors: Optional[List[str]] = Field(None, description="List of error messages")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "batch_id": "batch_20260612_143025_a3f2e1b9",
                "status": "completed",
                "dataset_name": "customers",
                "records_attempted": 1000,
                "records_loaded": 985,
                "records_duplicate": 10,
                "records_failed": 5,
                "execution_duration_ms": 1234.56,
                "load_timestamp": "2026-06-12T14:30:25"
            }
        }


class WarehouseValidationRequest(BaseModel):
    """Request model for warehouse validation"""
    
    records: List[Dict[str, Any]] = Field(..., description="List of records to validate")
    dataset_name: str = Field(..., description="Name of the dataset")
    required_columns: Optional[List[str]] = Field(None, description="List of required column names")
    unique_keys: Optional[List[str]] = Field(None, description="List of unique key columns")
    schema: Optional[Dict[str, str]] = Field(None, description="Schema with field types")
    
    class Config:
        schema_extra = {
            "example": {
                "dataset_name": "customers",
                "records": [{"id": "1", "name": "John", "email": "john@example.com"}],
                "required_columns": ["id", "name", "email"],
                "unique_keys": ["id"]
            }
        }


class ValidationResultResponse(BaseModel):
    """Response model for individual validation result"""
    
    is_valid: bool = Field(..., description="Whether validation passed")
    validation_type: str = Field(..., description="Type of validation performed")
    message: str = Field(..., description="Validation message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional validation details")


class WarehouseValidationResponse(BaseModel):
    """Response model for warehouse validation execution"""
    
    dataset_name: str = Field(..., description="Name of the dataset")
    validation_timestamp: datetime = Field(..., description="When validation was performed")
    overall_valid: bool = Field(..., description="Whether all validations passed")
    total_validations: int = Field(0, description="Total number of validations performed")
    passed_validations: int = Field(0, description="Number of validations that passed")
    failed_validations: int = Field(0, description="Number of validations that failed")
    validation_results: List[ValidationResultResponse] = Field(
        default_factory=list,
        description="Individual validation results"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "dataset_name": "customers",
                "validation_timestamp": "2026-06-12T14:30:00",
                "overall_valid": True,
                "total_validations": 3,
                "passed_validations": 3,
                "failed_validations": 0,
                "validation_results": [
                    {
                        "is_valid": True,
                        "validation_type": "required_columns",
                        "message": "All required columns present",
                        "details": {"required_columns": ["id", "name", "email"]}
                    }
                ]
            }
        }


class WarehouseStatisticsResponse(BaseModel):
    """Response model for warehouse statistics"""
    
    total_records: int = Field(0, description="Total number of records in warehouse")
    records_by_dataset: Dict[str, int] = Field(
        default_factory=dict,
        description="Record counts by dataset"
    )
    total_loads: int = Field(0, description="Total number of load executions")
    successful_loads: int = Field(0, description="Number of successful loads")
    failed_loads: int = Field(0, description="Number of failed loads")
    latest_load_timestamp: Optional[datetime] = Field(None, description="Timestamp of latest load")
    latest_load_status: Optional[str] = Field(None, description="Status of latest load")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "total_records": 50000,
                "records_by_dataset": {
                    "customers": 10000,
                    "orders": 25000,
                    "products": 15000
                },
                "total_loads": 150,
                "successful_loads": 145,
                "failed_loads": 5,
                "latest_load_timestamp": "2026-06-12T14:30:00",
                "latest_load_status": "completed"
            }
        }


class WarehouseLoadHistoryResponse(BaseModel):
    """Response model for warehouse load history"""
    
    id: int = Field(..., description="Load history ID")
    batch_id: str = Field(..., description="Batch identifier")
    dataset_name: str = Field(..., description="Dataset name")
    source_system: Optional[str] = Field(None, description="Source system name")
    load_type: str = Field(..., description="Type of load")
    status: str = Field(..., description="Load status")
    records_attempted: int = Field(0, description="Records attempted")
    records_loaded: int = Field(0, description="Records loaded")
    records_failed: int = Field(0, description="Records failed")
    records_duplicate: int = Field(0, description="Duplicate records")
    execution_duration_ms: Optional[float] = Field(None, description="Execution duration in ms")
    started_at: datetime = Field(..., description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message")
    validation_summary: Optional[Dict[str, Any]] = Field(None, description="Validation summary")
    
    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DatasetHealthResponse(BaseModel):
    """Response model for dataset health metrics"""
    
    dataset_name: str = Field(..., description="Name of the dataset")
    total_records: int = Field(0, description="Total records in dataset")
    validation_status_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Distribution of validation statuses"
    )
    latest_load_timestamp: Optional[datetime] = Field(None, description="Latest load timestamp")
    latest_load_status: Optional[str] = Field(None, description="Latest load status")
    latest_records_loaded: int = Field(0, description="Records loaded in latest load")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "dataset_name": "customers",
                "total_records": 10000,
                "validation_status_distribution": {
                    "passed": 9500,
                    "warning": 400,
                    "failed": 100
                },
                "latest_load_timestamp": "2026-06-12T14:30:00",
                "latest_load_status": "completed",
                "latest_records_loaded": 500
            }
        }


class WarehouseProcessedDataResponse(BaseModel):
    """Response model for warehouse processed data"""
    
    id: int = Field(..., description="Record ID")
    dataset_name: str = Field(..., description="Dataset name")
    batch_id: str = Field(..., description="Batch identifier")
    source_system: Optional[str] = Field(None, description="Source system")
    source_record_id: Optional[str] = Field(None, description="Source record ID")
    data: Dict[str, Any] = Field(..., description="Record data")
    data_quality_score: Optional[float] = Field(None, description="Data quality score")
    validation_status: Optional[str] = Field(None, description="Validation status")
    load_timestamp: datetime = Field(..., description="Load timestamp")
    
    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
