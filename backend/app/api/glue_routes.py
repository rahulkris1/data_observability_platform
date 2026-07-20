"""
Glue Job API Routes

Provides REST API endpoints for managing AWS Glue jobs,
including job execution, status monitoring, and configuration.
"""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, validator

from app.services.glue_service import get_glue_service
from app.core.exception_handler import build_success_response, BadRequestException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/glue", tags=["glue"])


class JobRunRequest(BaseModel):
    """Request model for starting a Glue job run."""
    job_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Name of the Glue job to run")
    arguments: Optional[Dict[str, str]] = Field(None, description="Job arguments as key-value pairs")
    
    @validator('job_name')
    def validate_job_name(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("Job name cannot be empty or whitespace")
        return v
    
    @validator('arguments')
    def validate_arguments(cls, v):
        if v is not None:
            # Validate argument keys and values
            for key, value in v.items():
                if not key or not isinstance(key, str):
                    raise ValueError(f"Invalid argument key: {key}")
                if not isinstance(value, str):
                    raise ValueError(f"Argument value for '{key}' must be a string")
        return v


class JobRunResponse(BaseModel):
    """Response model for Glue job run."""
    job_run_id: str
    job_name: str
    status: str = "SUBMITTED"


class JobStatusResponse(BaseModel):
    """Response model for Glue job status."""
    job_run_id: str
    job_name: str
    state: str
    started_on: Optional[str] = None
    completed_on: Optional[str] = None
    execution_time: int = 0
    error_message: Optional[str] = None


class ExecutionEnvironmentResponse(BaseModel):
    """Response model for execution environment."""
    execution_mode: str
    is_glue_enabled: bool
    glue_job_name: str
    glue_available: bool
    aws_region: str
    storage_provider: str


class ConfigValidationResponse(BaseModel):
    """Response model for configuration validation."""
    is_valid: bool
    issues: list
    warnings: list
    execution_mode: str


@router.get("/environment", response_model=ExecutionEnvironmentResponse)
async def get_execution_environment():
    """
    Get current execution environment information.
    
    Returns:
        Execution environment details
    """
    service = get_glue_service()
    env_info = service.get_execution_environment()
    return env_info


@router.get("/validate-config", response_model=ConfigValidationResponse)
async def validate_configuration():
    """
    Validate Glue configuration.
    
    Returns:
        Validation results with issues and warnings
    """
    service = get_glue_service()
    validation = service.validate_configuration()
    return validation


@router.post("/jobs/run", response_model=JobRunResponse)
async def start_job_run(request: JobRunRequest):
    """
    Start a Glue job run.
    
    Args:
        request: Job run request with optional job name and arguments
    
    Returns:
        Job run information with run ID
    
    Raises:
        HTTPException: If job start fails
    """
    service = get_glue_service()
    
    if not service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Glue service not available. Check AWS credentials and configuration."
        )
    
    job_run_id = service.start_job_run(
        job_name=request.job_name,
        job_arguments=request.arguments
    )
    
    if not job_run_id:
        raise HTTPException(
            status_code=500,
            detail="Failed to start Glue job run"
        )
    
    # Get job name from request or settings
    from app.core.config import settings
    job_name = request.job_name or settings.GLUE_JOB_NAME
    
    return {
        "job_run_id": job_run_id,
        "job_name": job_name,
        "status": "SUBMITTED"
    }


@router.get("/jobs/{job_run_id}/status", response_model=JobStatusResponse)
async def get_job_status(
    job_run_id: str,
    job_name: Optional[str] = Query(None, description="Glue job name")
):
    """
    Get status of a specific Glue job run.
    
    Args:
        job_run_id: Job run ID
        job_name: Optional job name (uses configured name if not provided)
    
    Returns:
        Job run status information
    
    Raises:
        HTTPException: If job run not found or service unavailable
    """
    service = get_glue_service()
    
    if not service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Glue service not available"
        )
    
    status = service.get_job_run_status(
        job_name=job_name,
        job_run_id=job_run_id
    )
    
    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"Job run not found: {job_run_id}"
        )
    
    return status


@router.get("/jobs/history")
async def get_job_history(
    job_name: Optional[str] = Query(None, description="Glue job name"),
    max_results: int = Query(10, ge=1, le=100, description="Maximum results")
):
    """
    Get history of Glue job runs.
    
    Args:
        job_name: Optional job name (uses configured name if not provided)
        max_results: Maximum number of results (1-100)
    
    Returns:
        List of job run information
    
    Raises:
        HTTPException: If service unavailable
    """
    service = get_glue_service()
    
    if not service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Glue service not available"
        )
    
    job_runs = service.get_job_runs_history(
        job_name=job_name,
        max_results=max_results
    )
    
    return {
        "job_runs": job_runs,
        "count": len(job_runs)
    }


@router.post("/jobs/{job_run_id}/stop")
async def stop_job_run(
    job_run_id: str,
    job_name: Optional[str] = Query(None, description="Glue job name")
):
    """
    Stop a running Glue job.
    
    Args:
        job_run_id: Job run ID to stop
        job_name: Optional job name
    
    Returns:
        Success confirmation
    
    Raises:
        HTTPException: If stop operation fails
    """
    service = get_glue_service()
    
    if not service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Glue service not available"
        )
    
    success = service.stop_job_run(
        job_name=job_name,
        job_run_id=job_run_id
    )
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop job run: {job_run_id}"
        )
    
    return {
        "message": f"Job run {job_run_id} stop requested",
        "success": True
    }


@router.get("/health")
async def glue_health_check():
    """
    Health check for Glue service integration.
    
    Returns:
        Health status of Glue service
    """
    service = get_glue_service()
    validation = service.validate_configuration()
    
    return {
        "service": "glue",
        "available": service.is_available(),
        "configuration_valid": validation['is_valid'],
        "execution_mode": validation['execution_mode'],
        "issues": validation['issues'],
        "warnings": validation['warnings']
    }
