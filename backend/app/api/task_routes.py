"""
API routes for Celery task monitoring and management.
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel

from app.services.task_queue_service import get_task_queue_service
from app.tasks.async_validation_task import (
    validate_dataset_async,
    run_validation_rules_async,
    batch_validate_datasets,
)
from app.tasks.async_profiling_task import (
    profile_dataset_async,
    calculate_data_quality_score,
    generate_data_lineage,
)


router = APIRouter(prefix="/tasks", tags=["tasks"])


# Request/Response Models
class TaskSubmitResponse(BaseModel):
    """Response model for task submission"""
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """Response model for task status"""
    task_id: str
    status: str
    ready: bool
    successful: Optional[bool] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    info: Optional[Any] = None


class WorkerStats(BaseModel):
    """Response model for worker statistics"""
    total_workers: int
    workers: List[Dict[str, Any]]
    timestamp: str


class QueueMetrics(BaseModel):
    """Response model for queue metrics"""
    queued_tasks: int
    running_tasks: int
    scheduled_tasks: int
    total_pending: int
    timestamp: str


class ValidationTaskRequest(BaseModel):
    """Request model for validation task"""
    contract_name: str
    dataset_columns: List[Dict[str, Any]]
    dataset_name: str


class ProfilingTaskRequest(BaseModel):
    """Request model for profiling task"""
    dataset_path: str
    dataset_name: str
    columns: Optional[List[str]] = None


class QualityScoreTaskRequest(BaseModel):
    """Request model for quality score calculation"""
    dataset_name: str
    validation_results: Dict[str, Any]
    profiling_results: Dict[str, Any]


# Task Submission Endpoints
@router.post("/validate", response_model=TaskSubmitResponse)
async def submit_validation_task(request: ValidationTaskRequest):
    """
    Submit an async validation task.
    
    Returns the task ID for tracking.
    """
    task = validate_dataset_async.delay(
        contract_name=request.contract_name,
        dataset_columns=request.dataset_columns,
        dataset_name=request.dataset_name,
    )
    
    return TaskSubmitResponse(
        task_id=task.id,
        status="submitted",
        message=f"Validation task submitted for dataset: {request.dataset_name}",
    )


@router.post("/profile", response_model=TaskSubmitResponse)
async def submit_profiling_task(request: ProfilingTaskRequest):
    """
    Submit an async data profiling task.
    
    Returns the task ID for tracking.
    """
    task = profile_dataset_async.delay(
        dataset_path=request.dataset_path,
        dataset_name=request.dataset_name,
        columns=request.columns,
    )
    
    return TaskSubmitResponse(
        task_id=task.id,
        status="submitted",
        message=f"Profiling task submitted for dataset: {request.dataset_name}",
    )


@router.post("/quality-score", response_model=TaskSubmitResponse)
async def submit_quality_score_task(request: QualityScoreTaskRequest):
    """
    Submit an async quality score calculation task.
    
    Returns the task ID for tracking.
    """
    task = calculate_data_quality_score.delay(
        dataset_name=request.dataset_name,
        validation_results=request.validation_results,
        profiling_results=request.profiling_results,
    )
    
    return TaskSubmitResponse(
        task_id=task.id,
        status="submitted",
        message=f"Quality score task submitted for dataset: {request.dataset_name}",
    )


# Task Status and Monitoring Endpoints
@router.get("/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get the status of a specific task.
    
    Returns task state, result (if completed), or error information.
    """
    service = get_task_queue_service()
    
    try:
        status = service.get_task_status(task_id)
        return TaskStatusResponse(**status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.get("/{task_id}/result")
async def get_task_result(
    task_id: str,
    timeout: Optional[float] = Query(None, description="Timeout in seconds to wait for result"),
):
    """
    Get the result of a completed task.
    
    Optionally wait for task completion with timeout.
    """
    service = get_task_queue_service()
    
    try:
        result = service.get_task_result(task_id, timeout=timeout)
        return {"task_id": task_id, "result": result}
    except TimeoutError:
        raise HTTPException(status_code=408, detail="Task not completed within timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task result: {str(e)}")


@router.delete("/{task_id}")
async def cancel_task(task_id: str):
    """
    Cancel a pending or running task.
    """
    service = get_task_queue_service()
    
    try:
        result = service.cancel_task(task_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")


@router.post("/{task_id}/retry", response_model=TaskSubmitResponse)
async def retry_task(task_id: str):
    """
    Retry a failed task.
    
    Note: This creates a new task with the same parameters.
    The original task ID is not reused.
    """
    # This is a placeholder - in production, you would need to store
    # task parameters to enable retries
    raise HTTPException(
        status_code=501,
        detail="Task retry not implemented. Please resubmit the task with original parameters.",
    )


# Worker and Queue Monitoring Endpoints
@router.get("/workers/stats", response_model=WorkerStats)
async def get_worker_stats():
    """
    Get statistics about active Celery workers.
    
    Returns worker count, active tasks, and registered task types.
    """
    service = get_task_queue_service()
    
    try:
        stats = service.get_worker_stats()
        return WorkerStats(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get worker stats: {str(e)}")


@router.get("/queue/metrics", response_model=QueueMetrics)
async def get_queue_metrics():
    """
    Get metrics about task queues.
    
    Returns counts of queued, running, and scheduled tasks.
    """
    service = get_task_queue_service()
    
    try:
        metrics = service.get_queue_metrics()
        return QueueMetrics(**metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get queue metrics: {str(e)}")


@router.get("/active/summary")
async def get_active_task_summary():
    """
    Get a summary of currently active tasks grouped by type.
    """
    service = get_task_queue_service()
    
    try:
        summary = service.get_active_task_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get active task summary: {str(e)}")


@router.post("/queue/purge")
async def purge_queue(queue_name: str = "default"):
    """
    Purge all pending tasks from the queue.
    
    ⚠️ Warning: This will remove all pending tasks that haven't started execution.
    """
    service = get_task_queue_service()
    
    try:
        result = service.purge_queue(queue_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to purge queue: {str(e)}")


@router.post("/bulk/status")
async def get_bulk_task_status(task_ids: List[str] = Body(...)):
    """
    Get status information for multiple tasks at once.
    """
    service = get_task_queue_service()
    
    try:
        results = service.get_task_info_bulk(task_ids)
        return {"tasks": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get bulk task status: {str(e)}")


# Health Check Endpoint
@router.get("/health")
async def task_system_health():
    """
    Check the health of the task system.
    
    Returns worker availability and queue status.
    """
    service = get_task_queue_service()
    
    try:
        worker_stats = service.get_worker_stats()
        queue_metrics = service.get_queue_metrics()
        
        is_healthy = worker_stats["total_workers"] > 0
        
        return {
            "healthy": is_healthy,
            "workers_available": worker_stats["total_workers"],
            "pending_tasks": queue_metrics["total_pending"],
            "status": "operational" if is_healthy else "no_workers",
            "message": (
                "Task system is operational" if is_healthy
                else "No workers available - tasks will queue but not execute"
            ),
        }
    except Exception as e:
        return {
            "healthy": False,
            "status": "error",
            "message": f"Failed to check task system health: {str(e)}",
        }
