"""Audit Log Schemas

Pydantic schemas for audit log API requests and responses.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class AuditLogBase(BaseModel):
    """Base audit log schema with common fields"""
    
    dataset_name: str = Field(..., description="Name of the dataset")
    validation_type: str = Field(..., description="Type of validation executed")
    status: str = Field(..., description="Validation status (passed, failed, warning, error)")
    execution_time_ms: Optional[float] = Field(None, description="Execution time in milliseconds")
    total_records: int = Field(0, description="Total number of records processed")
    failed_records: int = Field(0, description="Number of records that failed")
    pass_rate: float = Field(0.0, description="Percentage of records that passed (0-100)")
    validator_name: str = Field(..., description="Name of the validator")
    triggered_by: Optional[str] = Field("system", description="User or system that triggered validation")
    environment: Optional[str] = Field("dev", description="Environment (dev, staging, production)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional audit metadata")
    error_summary: Optional[str] = Field(None, description="Summary of errors encountered")
    details: Optional[Dict[str, Any]] = Field(None, description="Detailed execution results")


class AuditLogCreate(AuditLogBase):
    """Schema for creating a new audit log record"""
    pass


class AuditLogResponse(AuditLogBase):
    """Schema for audit log API response"""
    
    id: int = Field(..., description="Unique audit log ID")
    created_at: datetime = Field(..., description="When the audit record was created")
    updated_at: datetime = Field(..., description="When the audit record was last updated")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AuditHistoryRequest(BaseModel):
    """Schema for audit history query parameters"""
    
    dataset_name: Optional[str] = Field(None, description="Filter by dataset name (partial match)")
    validation_type: Optional[str] = Field(None, description="Filter by validation type")
    status: Optional[str] = Field(None, description="Filter by status")
    start_date: Optional[datetime] = Field(None, description="Filter records on or after this date")
    end_date: Optional[datetime] = Field(None, description="Filter records on or before this date")
    triggered_by: Optional[str] = Field(None, description="Filter by who triggered the validation")
    environment: Optional[str] = Field(None, description="Filter by environment")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of records to return")
    offset: int = Field(0, ge=0, description="Number of records to skip (for pagination)")
    sort_by: str = Field("created_at", description="Field to sort by")
    sort_order: str = Field("desc", description="Sort order (asc or desc)")


class AuditHistoryResponse(BaseModel):
    """Schema for audit history API response"""
    
    total_count: int = Field(..., description="Total number of matching records")
    page: int = Field(..., description="Current page number (0-indexed)")
    page_size: int = Field(..., description="Number of records per page")
    audits: List[AuditLogResponse] = Field(..., description="List of audit records")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AuditStatisticsResponse(BaseModel):
    """Schema for audit statistics API response"""
    
    total_audits: int = Field(..., description="Total number of audit records")
    status_distribution: Dict[str, int] = Field(..., description="Count of audits by status")
    validation_type_distribution: Dict[str, int] = Field(..., description="Count of audits by validation type")
    average_execution_time_ms: float = Field(..., description="Average execution time in milliseconds")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AuditFilterOptions(BaseModel):
    """Schema for available filter options"""
    
    datasets: List[str] = Field(..., description="Available dataset names")
    validation_types: List[str] = Field(..., description="Available validation types")
    statuses: List[str] = Field(..., description="Available statuses")
    triggered_by: List[str] = Field(..., description="Available triggered_by values")
    environments: List[str] = Field(..., description="Available environments")
