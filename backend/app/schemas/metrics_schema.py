"""Metrics API response schemas."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class MetricRecord(BaseModel):
    """Single metric record."""
    
    id: int = Field(..., description="Metric ID")
    metric_name: str = Field(..., description="Name of the metric")
    metric_value: float = Field(..., description="Numeric value of the metric")
    metric_type: str = Field(..., description="Type of metric (counter, gauge, histogram)")
    execution_time: Optional[float] = Field(None, description="Duration in milliseconds")
    timestamp: datetime = Field(..., description="When the metric was recorded")
    dataset_name: Optional[str] = Field(None, description="Associated dataset")
    validation_type: Optional[str] = Field(None, description="Associated validation type")
    dag_id: Optional[str] = Field(None, description="Associated DAG ID")
    task_id: Optional[str] = Field(None, description="Associated task ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    created_at: datetime = Field(..., description="Record creation timestamp")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DailyAggregation(BaseModel):
    """Daily aggregated metrics."""
    
    date: str = Field(..., description="Date (YYYY-MM-DD)")
    total: float = Field(..., description="Total sum of metric values")
    count: int = Field(..., description="Number of metric occurrences")
    average: float = Field(..., description="Average metric value")
    minimum: float = Field(..., description="Minimum metric value")
    maximum: float = Field(..., description="Maximum metric value")


class ValidationTypeAggregation(BaseModel):
    """Metrics aggregated by validation type."""
    
    validation_type: str = Field(..., description="Validation type")
    total: float = Field(..., description="Total sum of metric values")
    count: int = Field(..., description="Number of metric occurrences")
    average: float = Field(..., description="Average metric value")


class DatasetAggregation(BaseModel):
    """Metrics aggregated by dataset."""
    
    dataset_name: str = Field(..., description="Dataset name")
    total: float = Field(..., description="Total sum of metric values")
    count: int = Field(..., description="Number of metric occurrences")
    average: float = Field(..., description="Average metric value")


class TimeSeriesPoint(BaseModel):
    """Single time series data point."""
    
    timestamp: str = Field(..., description="Timestamp (ISO format)")
    total: float = Field(..., description="Total sum of metric values")
    count: int = Field(..., description="Number of metric occurrences")
    average: float = Field(..., description="Average metric value")


class ValidationMetricsSummary(BaseModel):
    """Summary of validation metrics."""
    
    total: int = Field(..., description="Total number of validations")
    success: int = Field(..., description="Number of successful validations")
    failure: int = Field(..., description="Number of failed validations")
    warning: int = Field(..., description="Number of validations with warnings")
    success_rate: float = Field(..., description="Success rate percentage")


class IngestionMetricsSummary(BaseModel):
    """Summary of ingestion metrics."""
    
    total_executions: int = Field(..., description="Total number of ingestion executions")
    success: int = Field(..., description="Number of successful ingestions")
    failure: int = Field(..., description="Number of failed ingestions")
    success_rate: float = Field(..., description="Success rate percentage")


class PerformanceMetricsSummary(BaseModel):
    """Summary of performance metrics."""
    
    avg_validation_duration_ms: float = Field(..., description="Average validation duration in ms")
    avg_ingestion_duration_ms: float = Field(..., description="Average ingestion duration in ms")
    avg_api_duration_ms: float = Field(..., description="Average API request duration in ms")


class PeriodInfo(BaseModel):
    """Information about the aggregation period."""
    
    start_date: str = Field(..., description="Start date (ISO format)")
    end_date: str = Field(..., description="End date (ISO format)")
    days: int = Field(..., description="Number of days in the period")


class FilterInfo(BaseModel):
    """Information about applied filters."""
    
    dataset_name: Optional[str] = Field(None, description="Dataset filter")
    validation_type: Optional[str] = Field(None, description="Validation type filter")


class MetricsSummary(BaseModel):
    """Comprehensive metrics summary."""
    
    period: PeriodInfo = Field(..., description="Aggregation period information")
    filters: FilterInfo = Field(..., description="Applied filters")
    validation: ValidationMetricsSummary = Field(..., description="Validation metrics summary")
    ingestion: IngestionMetricsSummary = Field(..., description="Ingestion metrics summary")
    performance: PerformanceMetricsSummary = Field(..., description="Performance metrics summary")


class DailyAggregationResponse(BaseModel):
    """Response for daily aggregations."""
    
    metric_name: str = Field(..., description="Name of the aggregated metric")
    aggregations: List[DailyAggregation] = Field(..., description="Daily aggregations")
    total_days: int = Field(..., description="Total number of days in the result")


class ValidationTypeAggregationResponse(BaseModel):
    """Response for validation type aggregations."""
    
    metric_name: str = Field(..., description="Name of the aggregated metric")
    aggregations: List[ValidationTypeAggregation] = Field(..., description="Validation type aggregations")
    total_types: int = Field(..., description="Total number of validation types")


class DatasetAggregationResponse(BaseModel):
    """Response for dataset aggregations."""
    
    metric_name: str = Field(..., description="Name of the aggregated metric")
    aggregations: List[DatasetAggregation] = Field(..., description="Dataset aggregations")
    total_datasets: int = Field(..., description="Total number of datasets")


class TimeSeriesResponse(BaseModel):
    """Response for time series data."""
    
    metric_name: str = Field(..., description="Name of the metric")
    data_points: List[TimeSeriesPoint] = Field(..., description="Time series data points")
    total_points: int = Field(..., description="Total number of data points")


class MetricRecordResponse(BaseModel):
    """Response for metric recording."""
    
    success: bool = Field(..., description="Whether the operation was successful")
    metric_id: int = Field(..., description="ID of the created metric")
    message: str = Field(..., description="Response message")


class MetricsListResponse(BaseModel):
    """Response for listing metrics."""
    
    metrics: List[MetricRecord] = Field(..., description="List of metrics")
    total: int = Field(..., description="Total number of metrics")
    limit: int = Field(..., description="Limit applied to the query")
