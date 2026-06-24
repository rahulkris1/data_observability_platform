"""Pydantic schemas for schema drift API"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ColumnDefinition(BaseModel):
    """Schema for a column definition"""
    name: str
    data_type: str
    nullable: Optional[bool] = True
    position: Optional[int] = None


class SchemaDefinition(BaseModel):
    """Schema for a complete schema definition"""
    columns: List[ColumnDefinition]


class SchemaVersionResponse(BaseModel):
    """Response schema for a schema version"""
    id: int
    dataset_name: str
    version_number: int
    version_hash: str
    schema_definition: Dict[str, Any]
    detected_at: datetime
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RegisterSchemaRequest(BaseModel):
    """Request schema for registering a new schema version"""
    dataset_name: str = Field(..., description="Name of the dataset")
    schema_definition: Dict[str, Any] = Field(..., description="Schema definition with columns")
    source: str = Field(default="manual", description="Source of the schema registration")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class SchemaDriftResponse(BaseModel):
    """Response schema for schema drift history"""
    id: int
    dataset_name: str
    previous_version_id: Optional[int]
    current_version_id: int
    drift_type: str
    severity: str
    changes: Dict[str, Any]
    detected_at: datetime
    acknowledged: bool
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AcknowledgeDriftRequest(BaseModel):
    """Request schema for acknowledging drift"""
    acknowledged_by: str = Field(..., description="User acknowledging the drift")
    notes: Optional[str] = Field(default=None, description="Notes about the acknowledgment")


class SchemaComparisonRequest(BaseModel):
    """Request schema for comparing two schema versions"""
    dataset_name: str = Field(..., description="Name of the dataset")
    version1: int = Field(..., description="First version number")
    version2: int = Field(..., description="Second version number")


class SchemaComparisonResponse(BaseModel):
    """Response schema for schema comparison"""
    dataset_name: str
    version1: int
    version2: int
    version1_detected_at: str
    version2_detected_at: str
    has_drift: bool
    drift_type: Optional[str]
    severity: Optional[str]
    changes: Dict[str, Any]


class DriftAlertResponse(BaseModel):
    """Response schema for drift alerts"""
    dataset_name: str
    total_drifts: int
    unacknowledged_count: int
    critical_count: int
    warning_count: int
    info_count: int
    latest_drift: Optional[SchemaDriftResponse] = None


class SchemaTimelineItem(BaseModel):
    """Schema for timeline item"""
    version_number: int
    detected_at: datetime
    source: Optional[str]
    drift_occurred: bool
    drift_type: Optional[str] = None
    severity: Optional[str] = None
    
    class Config:
        from_attributes = True
