"""Metrics API routes for collecting and retrieving metrics data."""

import logging
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.metrics_schema import (
    MetricRecord,
    MetricsSummary,
    DailyAggregationResponse,
    ValidationTypeAggregationResponse,
    DatasetAggregationResponse,
    TimeSeriesResponse,
    MetricsListResponse,
)
from app.services.metrics_service import MetricsService
from app.observability.metrics_repository import MetricsRepository

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/metrics",
    tags=["metrics"]
)


@router.get(
    "/summary",
    response_model=MetricsSummary,
    status_code=status.HTTP_200_OK,
    summary="Get metrics summary",
    description="Get comprehensive summary of all key metrics including validation, ingestion, and performance metrics"
)
async def get_metrics_summary(
    start_date: Optional[str] = Query(None, description="Start date (ISO format, defaults to 7 days ago)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format, defaults to now)"),
    dataset_name: Optional[str] = Query(None, description="Filter by dataset name"),
    validation_type: Optional[str] = Query(None, description="Filter by validation type"),
    db: Session = Depends(get_db)
) -> MetricsSummary:
    """Get comprehensive metrics summary"""
    try:
        # Parse dates
        end_dt = datetime.fromisoformat(end_date) if end_date else datetime.utcnow()
        start_dt = datetime.fromisoformat(start_date) if start_date else end_dt - timedelta(days=7)
        
        # Get metrics service and fetch summary
        metrics_service = MetricsService(db)
        summary = metrics_service.get_summary_metrics(
            start_date=start_dt,
            end_date=end_dt,
            dataset_name=dataset_name,
            validation_type=validation_type
        )
        
        return MetricsSummary(**summary)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error fetching metrics summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch metrics summary: {str(e)}"
        )


@router.get(
    "/daily",
    response_model=DailyAggregationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get daily aggregated metrics",
    description="Get metrics aggregated by day for a specific metric name"
)
async def get_daily_metrics(
    metric_name: str = Query(..., description="Name of the metric to aggregate"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format, defaults to 30 days ago)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format, defaults to now)"),
    dataset_name: Optional[str] = Query(None, description="Filter by dataset name"),
    validation_type: Optional[str] = Query(None, description="Filter by validation type"),
    db: Session = Depends(get_db)
) -> DailyAggregationResponse:
    """Get daily aggregated metrics"""
    try:
        # Parse dates
        end_dt = datetime.fromisoformat(end_date) if end_date else datetime.utcnow()
        start_dt = datetime.fromisoformat(start_date) if start_date else end_dt - timedelta(days=30)
        
        # Get metrics service and fetch aggregations
        metrics_service = MetricsService(db)
        aggregations = metrics_service.aggregate_by_day(
            metric_name=metric_name,
            start_date=start_dt,
            end_date=end_dt,
            dataset_name=dataset_name,
            validation_type=validation_type
        )
        
        return DailyAggregationResponse(
            metric_name=metric_name,
            aggregations=aggregations,
            total_days=len(aggregations)
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error fetching daily metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch daily metrics: {str(e)}"
        )


@router.get(
    "/by-validation-type",
    response_model=ValidationTypeAggregationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get metrics by validation type",
    description="Get metrics aggregated by validation type"
)
async def get_metrics_by_validation_type(
    metric_name: str = Query(..., description="Name of the metric to aggregate"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format, defaults to 30 days ago)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format, defaults to now)"),
    dataset_name: Optional[str] = Query(None, description="Filter by dataset name"),
    db: Session = Depends(get_db)
) -> ValidationTypeAggregationResponse:
    """Get metrics aggregated by validation type"""
    try:
        # Parse dates
        end_dt = datetime.fromisoformat(end_date) if end_date else datetime.utcnow()
        start_dt = datetime.fromisoformat(start_date) if start_date else end_dt - timedelta(days=30)
        
        # Get metrics service and fetch aggregations
        metrics_service = MetricsService(db)
        aggregations = metrics_service.aggregate_by_validation_type(
            metric_name=metric_name,
            start_date=start_dt,
            end_date=end_dt,
            dataset_name=dataset_name
        )
        
        return ValidationTypeAggregationResponse(
            metric_name=metric_name,
            aggregations=aggregations,
            total_types=len(aggregations)
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error fetching metrics by validation type: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch metrics by validation type: {str(e)}"
        )


@router.get(
    "/by-dataset",
    response_model=DatasetAggregationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get metrics by dataset",
    description="Get metrics aggregated by dataset"
)
async def get_metrics_by_dataset(
    metric_name: str = Query(..., description="Name of the metric to aggregate"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format, defaults to 30 days ago)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format, defaults to now)"),
    validation_type: Optional[str] = Query(None, description="Filter by validation type"),
    db: Session = Depends(get_db)
) -> DatasetAggregationResponse:
    """Get metrics aggregated by dataset"""
    try:
        # Parse dates
        end_dt = datetime.fromisoformat(end_date) if end_date else datetime.utcnow()
        start_dt = datetime.fromisoformat(start_date) if start_date else end_dt - timedelta(days=30)
        
        # Get metrics service and fetch aggregations
        metrics_service = MetricsService(db)
        aggregations = metrics_service.aggregate_by_dataset(
            metric_name=metric_name,
            start_date=start_dt,
            end_date=end_dt,
            validation_type=validation_type
        )
        
        return DatasetAggregationResponse(
            metric_name=metric_name,
            aggregations=aggregations,
            total_datasets=len(aggregations)
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error fetching metrics by dataset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch metrics by dataset: {str(e)}"
        )


@router.get(
    "/timeseries",
    response_model=TimeSeriesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get time series metrics",
    description="Get time series data for a specific metric"
)
async def get_time_series_metrics(
    metric_name: str = Query(..., description="Name of the metric"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format, defaults to 24 hours ago)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format, defaults to now)"),
    dataset_name: Optional[str] = Query(None, description="Filter by dataset name"),
    validation_type: Optional[str] = Query(None, description="Filter by validation type"),
    interval_hours: int = Query(1, description="Aggregation interval in hours", ge=1, le=24),
    db: Session = Depends(get_db)
) -> TimeSeriesResponse:
    """Get time series metrics"""
    try:
        # Parse dates
        end_dt = datetime.fromisoformat(end_date) if end_date else datetime.utcnow()
        start_dt = datetime.fromisoformat(start_date) if start_date else end_dt - timedelta(days=1)
        
        # Get metrics service and fetch time series
        metrics_service = MetricsService(db)
        data_points = metrics_service.get_time_series(
            metric_name=metric_name,
            start_date=start_dt,
            end_date=end_dt,
            dataset_name=dataset_name,
            validation_type=validation_type,
            interval_hours=interval_hours
        )
        
        return TimeSeriesResponse(
            metric_name=metric_name,
            data_points=data_points,
            total_points=len(data_points)
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error fetching time series metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch time series metrics: {str(e)}"
        )


@router.get(
    "/list",
    response_model=MetricsListResponse,
    status_code=status.HTTP_200_OK,
    summary="List metrics",
    description="List metrics with optional filters"
)
async def list_metrics(
    metric_name: Optional[str] = Query(None, description="Filter by metric name"),
    metric_type: Optional[str] = Query(None, description="Filter by metric type"),
    dataset_name: Optional[str] = Query(None, description="Filter by dataset name"),
    validation_type: Optional[str] = Query(None, description="Filter by validation type"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    limit: int = Query(100, description="Maximum number of results", ge=1, le=1000),
    db: Session = Depends(get_db)
) -> MetricsListResponse:
    """List metrics with filters"""
    try:
        # Parse dates if provided
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Get metrics repository and fetch metrics
        metrics_repo = MetricsRepository(db)
        metrics = metrics_repo.get_metrics(
            metric_name=metric_name,
            metric_type=metric_type,
            dataset_name=dataset_name,
            validation_type=validation_type,
            start_time=start_dt,
            end_time=end_dt,
            limit=limit
        )
        
        # Convert to response models
        metric_records = [MetricRecord.from_orm(m) for m in metrics]
        
        return MetricsListResponse(
            metrics=metric_records,
            total=len(metric_records),
            limit=limit
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error listing metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list metrics: {str(e)}"
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Metrics API health check",
    description="Check if the metrics API is operational"
)
async def health_check():
    """Health check endpoint for metrics API"""
    return {
        "status": "healthy",
        "service": "metrics-api",
        "timestamp": datetime.utcnow().isoformat()
    }
