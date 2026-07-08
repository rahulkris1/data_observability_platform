"""
Centralized exception handling for the Data Observability Platform.

This module provides:
- Custom exception classes
- Standard API response models
- Global exception handlers
- Request validation error handling
- Error logging and tracing
"""

import logging
import traceback
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Union

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

# Configure logger
logger = logging.getLogger(__name__)


# ============================================================================
# Standard API Response Models
# ============================================================================

class ErrorDetail(BaseModel):
    """Detailed error information"""
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    type: Optional[str] = Field(None, description="Error type")


class ErrorResponse(BaseModel):
    """Standard error response model"""
    success: bool = Field(False, description="Always False for errors")
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code for client handling")
    details: Optional[list[ErrorDetail]] = Field(None, description="Detailed error information")
    trace_id: str = Field(..., description="Unique trace ID for debugging")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    path: Optional[str] = Field(None, description="Request path that caused the error")


class SuccessResponse(BaseModel):
    """Standard success response model"""
    success: bool = Field(True, description="Always True for successful responses")
    data: Any = Field(..., description="Response data")
    message: Optional[str] = Field(None, description="Optional success message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


# ============================================================================
# Custom Exception Classes
# ============================================================================

class AppException(Exception):
    """Base application exception"""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None,
        details: Optional[list[ErrorDetail]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)


class ValidationException(AppException):
    """Validation error exception"""
    def __init__(self, message: str, details: Optional[list[ErrorDetail]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details
        )


class NotFoundException(AppException):
    """Resource not found exception"""
    def __init__(self, message: str, resource_type: Optional[str] = None):
        error_code = f"{resource_type.upper()}_NOT_FOUND" if resource_type else "NOT_FOUND"
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=error_code
        )


class UnauthorizedException(AppException):
    """Unauthorized access exception"""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED"
        )


class ForbiddenException(AppException):
    """Forbidden access exception"""
    def __init__(self, message: str = "Forbidden"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN"
        )


class ConflictException(AppException):
    """Conflict exception (e.g., duplicate resource)"""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT"
        )


class BadRequestException(AppException):
    """Bad request exception"""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="BAD_REQUEST"
        )


class ServiceUnavailableException(AppException):
    """Service unavailable exception"""
    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="SERVICE_UNAVAILABLE"
        )


# ============================================================================
# Error Response Builder
# ============================================================================

def build_error_response(
    error: str,
    status_code: int,
    error_code: Optional[str] = None,
    details: Optional[list[ErrorDetail]] = None,
    trace_id: Optional[str] = None,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """Build a standardized error response"""
    if trace_id is None:
        trace_id = str(uuid.uuid4())
    
    response = ErrorResponse(
        error=error,
        error_code=error_code,
        details=details,
        trace_id=trace_id,
        path=path
    )
    
    # Convert to dict with datetime as ISO string
    return response.model_dump(mode='json')


def build_success_response(
    data: Any,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """Build a standardized success response"""
    response = SuccessResponse(
        data=data,
        message=message
    )
    
    # Convert to dict with datetime as ISO string
    return response.model_dump(mode='json')


# ============================================================================
# Exception Handlers
# ============================================================================

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions"""
    trace_id = str(uuid.uuid4())
    
    # Log error with trace ID
    logger.error(
        f"[{trace_id}] Application error: {exc.message}",
        extra={
            "trace_id": trace_id,
            "path": str(request.url.path),
            "method": request.method,
            "error_code": exc.error_code,
            "status_code": exc.status_code
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_response(
            error=exc.message,
            status_code=exc.status_code,
            error_code=exc.error_code,
            details=exc.details,
            trace_id=trace_id,
            path=str(request.url.path)
        )
    )


async def http_exception_handler(
    request: Request, 
    exc: StarletteHTTPException
) -> JSONResponse:
    """Handle HTTP exceptions"""
    trace_id = str(uuid.uuid4())
    
    # Log HTTP errors
    logger.warning(
        f"[{trace_id}] HTTP error: {exc.detail}",
        extra={
            "trace_id": trace_id,
            "path": str(request.url.path),
            "method": request.method,
            "status_code": exc.status_code
        }
    )
    
    # Map status codes to error codes
    error_code_mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT"
    }
    
    error_code = error_code_mapping.get(exc.status_code, "UNKNOWN_ERROR")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_response(
            error=str(exc.detail),
            status_code=exc.status_code,
            error_code=error_code,
            trace_id=trace_id,
            path=str(request.url.path)
        )
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors"""
    trace_id = str(uuid.uuid4())
    
    # Convert validation errors to ErrorDetail objects
    error_details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"][1:]) if len(error["loc"]) > 1 else str(error["loc"][0])
        error_details.append(
            ErrorDetail(
                field=field,
                message=error["msg"],
                type=error["type"]
            )
        )
    
    # Log validation errors
    logger.warning(
        f"[{trace_id}] Validation error",
        extra={
            "trace_id": trace_id,
            "path": str(request.url.path),
            "method": request.method,
            "errors": [e.model_dump() for e in error_details]
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=build_error_response(
            error="Validation error",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=error_details,
            trace_id=trace_id,
            path=str(request.url.path)
        )
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions"""
    trace_id = str(uuid.uuid4())
    
    # Log the full exception with traceback
    logger.error(
        f"[{trace_id}] Unhandled exception: {str(exc)}",
        extra={
            "trace_id": trace_id,
            "path": str(request.url.path),
            "method": request.method,
            "exception_type": type(exc).__name__
        },
        exc_info=True
    )
    
    # In production, don't expose internal error details
    error_message = "An internal error occurred. Please try again later."
    
    # In development, include more details
    if logger.level == logging.DEBUG:
        error_message = f"{type(exc).__name__}: {str(exc)}"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=build_error_response(
            error=error_message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERNAL_SERVER_ERROR",
            trace_id=trace_id,
            path=str(request.url.path)
        )
    )


# ============================================================================
# Setup Function
# ============================================================================

def configure_exception_handlers(app: FastAPI) -> None:
    """
    Configure all exception handlers for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Custom application exceptions
    app.add_exception_handler(AppException, app_exception_handler)
    
    # HTTP exceptions
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # Request validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # Catch-all for unhandled exceptions
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Exception handlers configured successfully")


# ============================================================================
# Utility Functions
# ============================================================================

def raise_not_found(resource_type: str, identifier: Union[str, int]) -> None:
    """Raise a not found exception"""
    raise NotFoundException(
        message=f"{resource_type} with identifier '{identifier}' not found",
        resource_type=resource_type
    )


def raise_validation_error(message: str, field: Optional[str] = None) -> None:
    """Raise a validation exception"""
    details = None
    if field:
        details = [ErrorDetail(field=field, message=message, type="value_error")]
    raise ValidationException(message=message, details=details)


def raise_conflict(message: str) -> None:
    """Raise a conflict exception"""
    raise ConflictException(message=message)


def raise_bad_request(message: str) -> None:
    """Raise a bad request exception"""
    raise BadRequestException(message=message)
