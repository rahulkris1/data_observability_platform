"""Freshness Schemas

Pydantic models for freshness monitoring API requests and responses
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class FreshnessValidationResult(BaseModel):
    """Result of freshness validation for a dataset"""
    dataset_name: str = Field(..., description="Name of the dataset")
    ingestion_timestamp: datetime = Field(..., description="When data was ingested")
    validation_timestamp: Optional[datetime] = Field(None, description="When validation completed")
    dataset_age_hours: float = Field(..., description="Age of dataset in hours")
    freshness_status: str = Field(..., description="Freshness status: healthy, warning, critical")
    freshness_threshold_hours: float = Field(..., description="Expected freshness threshold in hours")
    is_fresh: bool = Field(..., description="Whether dataset meets freshness criteria")
    message: Optional[str] = Field(None, description="Human-readable status message")
    
    class Config:
        from_attributes = True


class LatencyMetrics(BaseModel):
    """Latency metrics for ingestion and validation"""
    dataset_name: str = Field(..., description="Name of the dataset")
    ingestion_start_time: Optional[datetime] = Field(None, description="Ingestion start time")
    ingestion_end_time: Optional[datetime] = Field(None, description="Ingestion end time")
    ingestion_latency_seconds: Optional[float] = Field(None, description="Ingestion duration in seconds")
    validation_start_time: Optional[datetime] = Field(None, description="Validation start time")
    validation_end_time: Optional[datetime] = Field(None, description="Validation end time")
    validation_latency_seconds: Optional[float] = Field(None, description="Validation duration in seconds")
    total_latency_seconds: Optional[float] = Field(None, description="Total pipeline latency in seconds")
    
    class Config:
        from_attributes = True


class SLAEvaluationResult(BaseModel):
    """Result of SLA evaluation"""
    dataset_name: str = Field(..., description="Name of the dataset")
    sla_threshold_hours: float = Field(..., description="SLA threshold in hours")
    actual_latency_hours: float = Field(..., description="Actual latency in hours")
    sla_status: str = Field(..., description="SLA status: compliant or breached")
    compliance_percentage: Optional[float] = Field(None, description="SLA compliance percentage")
    breach_duration_hours: Optional[float] = Field(None, description="Duration of SLA breach in hours")
    
    class Config:
        from_attributes = True


class FreshnessMetricResponse(BaseModel):
    """Complete freshness metric record"""
    id: int
    dataset_name: str
    ingestion_timestamp: datetime
    validation_timestamp: Optional[datetime]
    dataset_age_hours: float
    freshness_status: str
    freshness_threshold_hours: float
    ingestion_start_time: Optional[datetime]
    ingestion_end_time: Optional[datetime]
    ingestion_latency_seconds: Optional[float]
    validation_start_time: Optional[datetime]
    validation_end_time: Optional[datetime]
    validation_latency_seconds: Optional[float]
    sla_threshold_hours: Optional[float]
    sla_status: Optional[str]
    dag_id: Optional[str]
    task_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FreshnessMetricsSummary(BaseModel):
    """Summary of freshness metrics"""
    total_datasets: int = Field(..., description="Total number of datasets monitored")
    healthy_count: int = Field(..., description="Number of healthy datasets")
    warning_count: int = Field(..., description="Number of datasets in warning state")
    critical_count: int = Field(..., description="Number of critical datasets")
    sla_compliant_count: int = Field(..., description="Number of SLA compliant datasets")
    sla_breached_count: int = Field(..., description="Number of SLA breached datasets")
    avg_ingestion_latency_seconds: Optional[float] = Field(None, description="Average ingestion latency")
    avg_validation_latency_seconds: Optional[float] = Field(None, description="Average validation latency")
    avg_dataset_age_hours: Optional[float] = Field(None, description="Average dataset age")


class FreshnessTimeSeriesPoint(BaseModel):
    """Time series data point for freshness metrics"""
    timestamp: datetime
    dataset_name: str
    dataset_age_hours: float
    freshness_status: str
    ingestion_latency_seconds: Optional[float]
    validation_latency_seconds: Optional[float]


class FreshnessMetricsListResponse(BaseModel):
    """Response containing list of freshness metrics"""
    metrics: List[FreshnessMetricResponse]
    total: int
    summary: Optional[FreshnessMetricsSummary]


class FreshnessTimeSeriesResponse(BaseModel):
    """Response containing time series data"""
    data_points: List[FreshnessTimeSeriesPoint]
    dataset_name: Optional[str]
    start_time: datetime
    end_time: datetime
