"""
Standard API response schemas for consistent API responses.

Provides:
- Standard success response model
- Standard error response model
- Helper functions to build responses
"""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class StandardSuccessResponse(BaseModel):
    """Standard success response wrapper"""
    success: bool = Field(True, description="Always True for successful responses")
    data: Any = Field(..., description="Response data")
    message: Optional[str] = Field(None, description="Optional success message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"id": 1, "name": "Example"},
                "message": "Operation completed successfully",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class ErrorDetailSchema(BaseModel):
    """Detailed error information"""
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    type: Optional[str] = Field(None, description="Error type")


class StandardErrorResponse(BaseModel):
    """Standard error response wrapper"""
    success: bool = Field(False, description="Always False for errors")
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code for client handling")
    details: Optional[list[ErrorDetailSchema]] = Field(None, description="Detailed error information")
    trace_id: str = Field(..., description="Unique trace ID for debugging")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    path: Optional[str] = Field(None, description="Request path that caused the error")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Resource not found",
                "error_code": "NOT_FOUND",
                "details": None,
                "trace_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "timestamp": "2024-01-01T12:00:00Z",
                "path": "/api/v1/resource/123"
            }
        }


# Re-export from exception_handler for convenience
from app.core.exception_handler import build_success_response, build_error_response

__all__ = [
    "StandardSuccessResponse",
    "StandardErrorResponse",
    "ErrorDetailSchema",
    "build_success_response",
    "build_error_response"
]
