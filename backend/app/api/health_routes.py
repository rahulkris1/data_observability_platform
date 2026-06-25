"""Health Score API routes for calculating and retrieving pipeline health scores."""

import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.pipeline_health_service import PipelineHealthService
from app.tasks.health_score_tasks import calculate_pipeline_health_async, calculate_all_pipeline_health_async

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/health",
    tags=["health-scores"]
)


# Pydantic schemas
class HealthScoreResponse(BaseModel):
    """Response model for a single health score"""
    id: int
    pipeline_name: str
    overall_score: float
    validation_score: float
    freshness_score: float
    latency_score: float
    status: str
    timestamp: datetime
    validation_pass_rate: Optional[float] = None
    freshness_violations: Optional[float] = None
    avg_latency_seconds: Optional[float] = None
    total_validations: Optional[float] = None
    passed_validations: Optional[float] = None
    failed_validations: Optional[float] = None
    score_metadata: Optional[dict] = None
    
    class Config:
        from_attributes = True


class HealthScoreCalculateRequest(BaseModel):
    """Request model for calculating health scores"""
    pipeline_name: str = Field(..., description="Name of the pipeline to score")
    lookback_hours: int = Field(default=24, ge=1, le=720, description="Hours to look back for data")
    async_execution: bool = Field(default=False, description="Execute asynchronously using Celery")


class BulkHealthScoreRequest(BaseModel):
    """Request model for bulk health score calculation"""
    pipeline_names: List[str] = Field(..., description="List of pipeline names to score")
    lookback_hours: int = Field(default=24, ge=1, le=720, description="Hours to look back for data")


class AsyncTaskResponse(BaseModel):
    """Response model for async task submission"""
    task_id: str
    status: str
    message: str


class HealthScoreSummaryResponse(BaseModel):
    """Response model for health score summary"""
    total_pipelines: int
    healthy_count: int
    degraded_count: int
    unhealthy_count: int
    average_overall_score: float
    pipelines: List[HealthScoreResponse]


@router.post(
    "/calculate",
    response_model=HealthScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate pipeline health score"
)
def calculate_health_score(
    request: HealthScoreCalculateRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate health score for a pipeline based on validation, freshness, and latency metrics.
    
    - **pipeline_name**: Name of the pipeline to score
    - **lookback_hours**: Number of hours to look back for data (default: 24)
    - **async_execution**: If true, executes asynchronously via Celery
    """
    try:
        if request.async_execution:
            # Submit to Celery for async processing
            task = calculate_pipeline_health_async.delay(
                pipeline_name=request.pipeline_name,
                lookback_hours=request.lookback_hours
            )
            
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail={
                    "message": "Health score calculation submitted",
                    "task_id": task.id,
                    "status": "pending"
                }
            )
        
        # Synchronous calculation
        service = PipelineHealthService(db)
        health_score = service.calculate_pipeline_health(
            pipeline_name=request.pipeline_name,
            lookback_hours=request.lookback_hours
        )
        
        logger.info(f"Calculated health score for pipeline '{request.pipeline_name}': {health_score.overall_score}")
        
        return HealthScoreResponse.from_orm(health_score)
        
    except Exception as e:
        logger.error(f"Error calculating health score: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate health score: {str(e)}"
        )


@router.get(
    "/pipeline/{pipeline_name}",
    response_model=HealthScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Get latest health score for a pipeline"
)
def get_pipeline_health_score(
    pipeline_name: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve the most recent health score for a specific pipeline.
    
    - **pipeline_name**: Name of the pipeline
    """
    try:
        service = PipelineHealthService(db)
        health_score = service.get_latest_health_score(pipeline_name)
        
        if not health_score:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No health score found for pipeline '{pipeline_name}'"
            )
        
        return HealthScoreResponse.from_orm(health_score)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving health score: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve health score: {str(e)}"
        )


@router.get(
    "/pipeline/{pipeline_name}/history",
    response_model=List[HealthScoreResponse],
    status_code=status.HTTP_200_OK,
    summary="Get health score history for a pipeline"
)
def get_pipeline_health_history(
    pipeline_name: str,
    lookback_hours: int = Query(default=168, ge=1, le=8760, description="Hours of history to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Retrieve health score history for a specific pipeline.
    
    - **pipeline_name**: Name of the pipeline
    - **lookback_hours**: Hours of history to retrieve (default: 168 = 7 days)
    """
    try:
        service = PipelineHealthService(db)
        history = service.get_health_score_history(pipeline_name, lookback_hours)
        
        return [HealthScoreResponse.from_orm(score) for score in history]
        
    except Exception as e:
        logger.error(f"Error retrieving health score history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve health score history: {str(e)}"
        )


@router.get(
    "/all",
    response_model=HealthScoreSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all pipeline health scores"
)
def get_all_pipeline_health(
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of pipelines"),
    db: Session = Depends(get_db)
):
    """
    Retrieve latest health scores for all pipelines with summary statistics.
    
    - **limit**: Maximum number of pipelines to return (default: 100)
    """
    try:
        service = PipelineHealthService(db)
        scores = service.get_all_pipeline_health(limit)
        
        # Calculate summary statistics
        total = len(scores)
        healthy = sum(1 for s in scores if s.status == 'healthy')
        degraded = sum(1 for s in scores if s.status == 'degraded')
        unhealthy = sum(1 for s in scores if s.status == 'unhealthy')
        avg_score = sum(s.overall_score for s in scores) / total if total > 0 else 0.0
        
        return HealthScoreSummaryResponse(
            total_pipelines=total,
            healthy_count=healthy,
            degraded_count=degraded,
            unhealthy_count=unhealthy,
            average_overall_score=round(avg_score, 2),
            pipelines=[HealthScoreResponse.from_orm(score) for score in scores]
        )
        
    except Exception as e:
        logger.error(f"Error retrieving all health scores: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve health scores: {str(e)}"
        )


@router.post(
    "/calculate/bulk",
    response_model=AsyncTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Calculate health scores for multiple pipelines"
)
def calculate_bulk_health_scores(
    request: BulkHealthScoreRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate health scores for multiple pipelines asynchronously.
    
    - **pipeline_names**: List of pipeline names to score
    - **lookback_hours**: Number of hours to look back for data (default: 24)
    """
    try:
        # Submit to Celery for async processing
        task = calculate_all_pipeline_health_async.delay(
            pipeline_names=request.pipeline_names,
            lookback_hours=request.lookback_hours
        )
        
        logger.info(f"Submitted bulk health score calculation for {len(request.pipeline_names)} pipelines")
        
        return AsyncTaskResponse(
            task_id=task.id,
            status="pending",
            message=f"Health score calculation submitted for {len(request.pipeline_names)} pipelines"
        )
        
    except Exception as e:
        logger.error(f"Error submitting bulk calculation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit bulk calculation: {str(e)}"
        )
