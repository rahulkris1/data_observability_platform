"""Freshness Monitoring API Routes

API endpoints for freshness, latency, and SLA monitoring
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.freshness_schema import (
    FreshnessValidationResult,
    LatencyMetrics,
    SLAEvaluationResult,
    FreshnessMetricResponse,
    FreshnessMetricsSummary,
    FreshnessMetricsListResponse,
    FreshnessTimeSeriesResponse,
    FreshnessTimeSeriesPoint,
)
from app.services.freshness_service import FreshnessService
from app.services.latency_service import LatencyService
from app.services.sla_service import SLAService
from app.services.freshness_aggregator import FreshnessAggregator
from app.services.freshness_metrics_repository import FreshnessMetricsRepository

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/freshness",
    tags=["freshness"]
)


@router.get(
    "/metrics",
    response_model=FreshnessMetricsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get freshness metrics",
    description="Get freshness metrics with optional filters"
)
async def get_freshness_metrics(
    dataset_name: Optional[str] = Query(None, description="Filter by dataset name"),
    freshness_status: Optional[str] = Query(None, description="Filter by freshness status (healthy, warning, critical)"),
    sla_status: Optional[str] = Query(None, description="Filter by SLA status (compliant, breached)"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format, defaults to 7 days ago)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format, defaults to now)"),
    limit: int = Query(100, description="Maximum number of records", ge=1, le=1000),
    offset: int = Query(0, description="Number of records to skip", ge=0),
    db: Session = Depends(get_db)
) -> FreshnessMetricsListResponse:
    """Get freshness metrics with optional filters"""
    try:
        # Parse dates
        end_dt = datetime.fromisoformat(end_date) if end_date else datetime.utcnow()
        start_dt = datetime.fromisoformat(start_date) if start_date else end_dt - timedelta(days=7)
        
        # Get repository and fetch metrics
        repository = FreshnessMetricsRepository(db)
        
        metrics = repository.get_all(
            dataset_name=dataset_name,
            freshness_status=freshness_status,
            sla_status=sla_status,
            start_date=start_dt,
            end_date=end_dt,
            limit=limit,
            offset=offset
        )
        
        total = repository.get_count(
            dataset_name=dataset_name,
            freshness_status=freshness_status,
            sla_status=sla_status,
            start_date=start_dt,
            end_date=end_dt
        )
        
        # Get summary stats
        summary_stats = repository.get_summary_stats(start_dt, end_dt)
        summary = FreshnessMetricsSummary(**summary_stats)
        
        # Convert to response models
        metric_responses = [FreshnessMetricResponse.from_orm(m) for m in metrics]
        
        return FreshnessMetricsListResponse(
            metrics=metric_responses,
            total=total,
            summary=summary
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error fetching freshness metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch freshness metrics: {str(e)}"
        )


@router.get(
    "/summary",
    response_model=FreshnessMetricsSummary,
    status_code=status.HTTP_200_OK,
    summary="Get freshness summary",
    description="Get summary statistics for freshness metrics"
)
async def get_freshness_summary(
    start_date: Optional[str] = Query(None, description="Start date (ISO format, defaults to 7 days ago)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format, defaults to now)"),
    db: Session = Depends(get_db)
) -> FreshnessMetricsSummary:
    """Get freshness summary statistics"""
    try:
        # Parse dates
        end_dt = datetime.fromisoformat(end_date) if end_date else datetime.utcnow()
        start_dt = datetime.fromisoformat(start_date) if start_date else end_dt - timedelta(days=7)
        
        # Get repository and fetch summary
        repository = FreshnessMetricsRepository(db)
        summary_stats = repository.get_summary_stats(start_dt, end_dt)
        
        return FreshnessMetricsSummary(**summary_stats)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error fetching freshness summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch freshness summary: {str(e)}"
        )


@router.get(
    "/time-series",
    response_model=FreshnessTimeSeriesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get freshness time series",
    description="Get time series data for freshness metrics"
)
async def get_freshness_time_series(
    dataset_name: Optional[str] = Query(None, description="Filter by dataset name"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format, defaults to 7 days ago)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format, defaults to now)"),
    db: Session = Depends(get_db)
) -> FreshnessTimeSeriesResponse:
    """Get time series data for freshness metrics"""
    try:
        # Parse dates
        end_dt = datetime.fromisoformat(end_date) if end_date else datetime.utcnow()
        start_dt = datetime.fromisoformat(start_date) if start_date else end_dt - timedelta(days=7)
        
        # Get repository and fetch time series
        repository = FreshnessMetricsRepository(db)
        metrics = repository.get_time_series(
            dataset_name=dataset_name,
            start_date=start_dt,
            end_date=end_dt
        )
        
        # Convert to time series points
        data_points = [
            FreshnessTimeSeriesPoint(
                timestamp=m.ingestion_timestamp,
                dataset_name=m.dataset_name,
                dataset_age_hours=m.dataset_age_hours,
                freshness_status=m.freshness_status,
                ingestion_latency_seconds=m.ingestion_latency_seconds,
                validation_latency_seconds=m.validation_latency_seconds
            )
            for m in metrics
        ]
        
        return FreshnessTimeSeriesResponse(
            data_points=data_points,
            dataset_name=dataset_name,
            start_time=start_dt,
            end_time=end_dt
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error fetching freshness time series: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch freshness time series: {str(e)}"
        )


@router.get(
    "/latest/{dataset_name}",
    response_model=FreshnessMetricResponse,
    status_code=status.HTTP_200_OK,
    summary="Get latest freshness metric",
    description="Get the latest freshness metric for a specific dataset"
)
async def get_latest_freshness_metric(
    dataset_name: str,
    db: Session = Depends(get_db)
) -> FreshnessMetricResponse:
    """Get latest freshness metric for a dataset"""
    try:
        repository = FreshnessMetricsRepository(db)
        metric = repository.get_latest_by_dataset(dataset_name)
        
        if not metric:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No freshness metrics found for dataset: {dataset_name}"
            )
        
        return FreshnessMetricResponse.from_orm(metric)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest freshness metric: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch latest freshness metric: {str(e)}"
        )


@router.get(
    "/sla/thresholds",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get SLA thresholds",
    description="Get all configured SLA thresholds"
)
async def get_sla_thresholds() -> dict:
    """Get all configured SLA thresholds"""
    try:
        sla_service = SLAService()
        thresholds = sla_service.get_all_sla_thresholds()
        return {"thresholds": thresholds}
        
    except Exception as e:
        logger.error(f"Error fetching SLA thresholds: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch SLA thresholds: {str(e)}"
        )


@router.get(
    "/freshness/thresholds",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get freshness thresholds",
    description="Get freshness threshold configuration for all datasets"
)
async def get_freshness_thresholds() -> dict:
    """Get all configured freshness thresholds"""
    try:
        from app.services.freshness_service import FreshnessThresholds
        thresholds = FreshnessThresholds.DATASET_THRESHOLDS.copy()
        thresholds["_default"] = {
            "healthy": FreshnessThresholds.DEFAULT_HEALTHY,
            "warning": FreshnessThresholds.DEFAULT_WARNING,
        }
        return {"thresholds": thresholds}
        
    except Exception as e:
        logger.error(f"Error fetching freshness thresholds: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch freshness thresholds: {str(e)}"
        )
