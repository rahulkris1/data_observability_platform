"""Profiling API routes for executing dataset profiling and retrieving results."""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from celery.result import AsyncResult

from app.core.database import get_db
from app.services.dataset_profiling_service import DatasetProfilingService
from app.tasks.async_profiling_task import profile_dataset_async
from app.models.profiling_result import ProfilingResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/profiling",
    tags=["profiling"]
)


# Response models
from pydantic import BaseModel, Field
from datetime import datetime


class ProfilingExecutionRequest(BaseModel):
    """Request model for executing dataset profiling"""
    dataset_name: str = Field(..., description="Name of the dataset to profile")
    bucket_name: str = Field(..., description="MinIO bucket name")
    object_name: str = Field(..., description="Object name in MinIO")
    profiled_by: str = Field(default='system', description="User initiating profiling")


class ProfilingExecutionResponse(BaseModel):
    """Response model for profiling execution"""
    task_id: str = Field(..., description="Celery task ID")
    dataset_name: str = Field(..., description="Dataset name")
    status: str = Field(..., description="Task status")
    message: str = Field(..., description="Status message")


class ColumnStatistics(BaseModel):
    """Column statistics model"""
    column_name: str
    data_type: str
    null_count: int
    null_percentage: float
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None


class ColumnDistribution(BaseModel):
    """Column distribution model"""
    column_name: str
    unique_count: int
    top_values: List[dict]


class ProfilingResultResponse(BaseModel):
    """Response model for profiling result"""
    id: int
    dataset_name: str
    status: str
    row_count: Optional[int]
    column_count: Optional[int]
    execution_time_ms: Optional[float]
    column_statistics: Optional[dict]
    column_distributions: Optional[dict]
    error_message: Optional[str]
    profiled_by: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProfilingHistoryResponse(BaseModel):
    """Response model for profiling history"""
    total: int
    results: List[ProfilingResultResponse]


class TaskStatusResponse(BaseModel):
    """Response model for task status"""
    task_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None


@router.post(
    "/execute",
    response_model=ProfilingExecutionResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def execute_profiling(
    request: ProfilingExecutionRequest,
    db: Session = Depends(get_db)
):
    """
    Execute dataset profiling asynchronously.
    
    Args:
        request: Profiling execution request
        db: Database session
        
    Returns:
        Task execution details
    """
    try:
        logger.info(f"Starting profiling for dataset: {request.dataset_name}")
        
        # Execute async profiling task
        task = profile_dataset_async.delay(
            dataset_name=request.dataset_name,
            bucket_name=request.bucket_name,
            object_name=request.object_name,
            profiled_by=request.profiled_by
        )
        
        return ProfilingExecutionResponse(
            task_id=task.id,
            dataset_name=request.dataset_name,
            status="pending",
            message=f"Profiling task submitted for dataset: {request.dataset_name}"
        )
        
    except Exception as e:
        logger.error(f"Failed to start profiling: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start profiling: {str(e)}"
        )


@router.get(
    "/task/{task_id}",
    response_model=TaskStatusResponse
)
async def get_task_status(task_id: str):
    """
    Get status of a profiling task.
    
    Args:
        task_id: Celery task ID
        
    Returns:
        Task status and result
    """
    try:
        task_result = AsyncResult(task_id)
        
        response = TaskStatusResponse(
            task_id=task_id,
            status=task_result.state
        )
        
        if task_result.state == 'SUCCESS':
            response.result = task_result.result
        elif task_result.state == 'FAILURE':
            response.error = str(task_result.info)
        elif task_result.state in ['PENDING', 'RUNNING']:
            response.result = task_result.info if task_result.info else {}
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to get task status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.get(
    "/results/latest/{dataset_name}",
    response_model=ProfilingResultResponse
)
async def get_latest_profiling(
    dataset_name: str,
    db: Session = Depends(get_db)
):
    """
    Get the latest profiling result for a dataset.
    
    Args:
        dataset_name: Name of the dataset
        db: Database session
        
    Returns:
        Latest profiling result
    """
    try:
        service = DatasetProfilingService(db)
        result = service.get_latest_profiling(dataset_name)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No profiling results found for dataset: {dataset_name}"
            )
        
        return ProfilingResultResponse.from_orm(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get latest profiling: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profiling results: {str(e)}"
        )


@router.get(
    "/results/{profiling_id}",
    response_model=ProfilingResultResponse
)
async def get_profiling_by_id(
    profiling_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific profiling result by ID.
    
    Args:
        profiling_id: Profiling result ID
        db: Database session
        
    Returns:
        Profiling result
    """
    try:
        service = DatasetProfilingService(db)
        result = service.get_profiling_by_id(profiling_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profiling result not found: {profiling_id}"
            )
        
        return ProfilingResultResponse.from_orm(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profiling result: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profiling result: {str(e)}"
        )


@router.get(
    "/history",
    response_model=ProfilingHistoryResponse
)
async def get_profiling_history(
    dataset_name: Optional[str] = Query(None, description="Filter by dataset name"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """
    Get profiling history, optionally filtered by dataset.
    
    Args:
        dataset_name: Optional dataset name filter
        limit: Maximum number of results
        db: Database session
        
    Returns:
        List of profiling results
    """
    try:
        service = DatasetProfilingService(db)
        results = service.get_profiling_history(
            dataset_name=dataset_name,
            limit=limit
        )
        
        return ProfilingHistoryResponse(
            total=len(results),
            results=[ProfilingResultResponse.from_orm(r) for r in results]
        )
        
    except Exception as e:
        logger.error(f"Failed to get profiling history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profiling history: {str(e)}"
        )
