"""
Request logging middleware for FastAPI.
Logs incoming requests, responses, and exceptions.
"""
import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .logger import get_logger
from .metrics_service import MetricsService

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests and responses."""
    
    def __init__(self, app: ASGIApp, metrics_service: MetricsService = None):
        super().__init__(app)
        self.metrics_service = metrics_service
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log details.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler
            
        Returns:
            HTTP response
        """
        # Generate request ID
        request_id = request.headers.get("X-Request-ID", f"req-{int(time.time() * 1000)}")
        
        # Extract request details
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        client_host = request.client.host if request.client else "unknown"
        
        # Start timer
        start_time = time.time()
        
        # Log incoming request
        logger.info(
            f"Incoming request: {method} {path}",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "query_params": query_params,
                "client_host": client_host,
                "user_agent": request.headers.get("user-agent", "unknown"),
            },
        )
        
        # Process request
        response = None
        error = None
        status_code = 500
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            logger.info(
                f"Request completed: {method} {path} - {status_code}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )
            
            # Track metrics
            if self.metrics_service:
                self.metrics_service.increment_api_request(
                    method=method,
                    path=path,
                    status_code=status_code,
                    duration_ms=duration_ms,
                )
            
            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log exception
            logger.error(
                f"Request failed: {method} {path}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration_ms": round(duration_ms, 2),
                },
                exc_info=True,
            )
            
            # Track metrics
            if self.metrics_service:
                self.metrics_service.increment_api_request(
                    method=method,
                    path=path,
                    status_code=500,
                    duration_ms=duration_ms,
                    error=True,
                )
            
            # Re-raise the exception to be handled by FastAPI
            raise
