"""
API routes for observability - logs and metrics.
"""
from typing import Optional, List
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from app.observability import parse_log_file, get_log_stats, get_metrics_service


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
