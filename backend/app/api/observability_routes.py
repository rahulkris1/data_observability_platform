"""
API routes for observability - logs and metrics.
"""
from typing import Optional, List
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from app.observability import parse_log_file, get_log_stats, get_metrics_service
from app.services.cloudwatch_metrics_service import cloudwatch_metrics_service
from app.services.cloudwatch_logs_service import cloudwatch_logs_service
from app.core.config import settings


router = APIRouter(prefix="/api/v1/observability", tags=["observability"])


# Response models
class LogEntry(BaseModel):
    """Single log entry."""
    timestamp: str
    level: str
    logger: str
    message: str
    module: Optional[str] = None
    function: Optional[str] = None
    line: Optional[int] = None
    extra_fields: Optional[dict] = None


class LogsResponse(BaseModel):
    """Response for logs endpoint."""
    logs: List[dict]
    total: int
    page: int
    page_size: int


class LogStatsResponse(BaseModel):
    """Response for log statistics."""
    total_lines: int
    file_size_bytes: int
    levels: dict
    loggers: dict


class MetricsResponse(BaseModel):
    """Response for metrics endpoint."""
    counters: dict
    histograms: dict
    timestamp: str


class CloudWatchStatusResponse(BaseModel):
    """Response for CloudWatch status."""
    metrics_enabled: bool
    metrics_available: bool
    logs_enabled: bool
    logs_available: bool
    namespace: Optional[str] = None
    log_group: Optional[str] = None
    region: Optional[str] = None
    active_log_streams: int = 0
    provider: str


class MetricsProviderResponse(BaseModel):
    """Response for metrics provider status."""
    active_provider: str
    cloudwatch_enabled: bool
    local_enabled: bool
    execution_mode: str


@router.get("/logs", response_model=LogsResponse)
async def get_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    logger: Optional[str] = Query(None, description="Filter by logger name"),
    search: Optional[str] = Query(None, description="Search in log messages"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
):
    """
    Get application logs with filtering and pagination.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of logs per page
        level: Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        logger: Filter by logger name
        search: Search text in log messages
        start_date: Filter logs after this date (ISO format)
        end_date: Filter logs before this date (ISO format)
        
    Returns:
        Paginated log entries
    """
    # Get log file path
    log_file = Path("logs/app.log")
    
    if not log_file.exists():
        return LogsResponse(logs=[], total=0, page=page, page_size=page_size)
    
    # Parse all logs
    all_logs = parse_log_file(str(log_file), max_lines=10000)
    
    # Apply filters
    filtered_logs = all_logs
    
    # Filter by level
    if level:
        filtered_logs = [
            log for log in filtered_logs
            if log.get("level", "").upper() == level.upper()
        ]
    
    # Filter by logger
    if logger:
        filtered_logs = [
            log for log in filtered_logs
            if logger.lower() in log.get("logger", "").lower()
        ]
    
    # Search in message
    if search:
        filtered_logs = [
            log for log in filtered_logs
            if search.lower() in log.get("message", "").lower()
        ]
    
    # Filter by date range
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            filtered_logs = [
                log for log in filtered_logs
                if datetime.fromisoformat(log.get("timestamp", "").replace('Z', '+00:00')) >= start_dt
            ]
        except (ValueError, TypeError):
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            filtered_logs = [
                log for log in filtered_logs
                if datetime.fromisoformat(log.get("timestamp", "").replace('Z', '+00:00')) <= end_dt
            ]
        except (ValueError, TypeError):
            pass
    
    # Sort by timestamp (newest first)
    filtered_logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # Paginate
    total = len(filtered_logs)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_logs = filtered_logs[start_idx:end_idx]
    
    return LogsResponse(
        logs=paginated_logs,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/logs/stats", response_model=LogStatsResponse)
async def get_log_statistics():
    """
    Get statistics about application logs.
    
    Returns:
        Log statistics including counts by level and logger
    """
    log_file = Path("logs/app.log")
    
    if not log_file.exists():
        return LogStatsResponse(
            total_lines=0,
            file_size_bytes=0,
            levels={},
            loggers={},
        )
    
    stats = get_log_stats(str(log_file))
    
    return LogStatsResponse(
        total_lines=stats["total_lines"],
        file_size_bytes=stats["file_size_bytes"],
        levels=stats["levels"],
        loggers=stats["loggers"],
    )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get current application metrics.
    
    Returns:
        Current metrics including counters and histograms
    """
    metrics_service = get_metrics_service()
    metrics = metrics_service.get_all_metrics()
    
    return MetricsResponse(
        counters=metrics["counters"],
        histograms=metrics["histograms"],
        timestamp=metrics["timestamp"],
    )


@router.post("/metrics/reset")
async def reset_metrics():
    """
    Reset all metrics.
    
    Returns:
        Success message
    """
    metrics_service = get_metrics_service()
    metrics_service.reset_metrics()
    
    return {"message": "Metrics reset successfully"}


@router.get("/cloudwatch/status", response_model=CloudWatchStatusResponse)
async def get_cloudwatch_status():
    """
    Get CloudWatch service status including metrics and logs.
    
    Returns:
        CloudWatch status information
    """
    metrics_status = cloudwatch_metrics_service.get_metrics_status()
    logs_status = cloudwatch_logs_service.get_logs_status()
    
    return CloudWatchStatusResponse(
        metrics_enabled=metrics_status["enabled"],
        metrics_available=metrics_status["available"],
        logs_enabled=logs_status["enabled"],
        logs_available=logs_status["available"],
        namespace=metrics_status.get("namespace"),
        log_group=logs_status.get("log_group"),
        region=metrics_status.get("region"),
        active_log_streams=logs_status.get("active_streams", 0),
        provider=metrics_status.get("provider", "local")
    )


@router.get("/metrics/provider", response_model=MetricsProviderResponse)
async def get_metrics_provider():
    """
    Get active metrics provider status.
    
    Returns:
        Information about active metrics provider (CloudWatch or local)
    """
    cloudwatch_enabled = settings.CLOUDWATCH_ENABLED
    cloudwatch_available = cloudwatch_metrics_service.is_available()
    
    # Determine active provider
    if cloudwatch_available:
        active_provider = "cloudwatch"
    else:
        active_provider = "local"
    
    return MetricsProviderResponse(
        active_provider=active_provider,
        cloudwatch_enabled=cloudwatch_enabled,
        local_enabled=True,  # Local metrics always available
        execution_mode=settings.EXECUTION_MODE
    )
