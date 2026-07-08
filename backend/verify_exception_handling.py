"""
Verification script for exception handling and standardized API responses.

This script tests:
1. Standardized success responses
2. Standardized error responses
3. Validation error handling
4. Custom exception handling
5. Request validation errors
6. Global exception handling
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_standardized_success_response():
    """Test that success responses follow the standard format"""
    print("\n=== Testing Standardized Success Response ===")
    
    response = client.get("/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    data = response.json()
    assert response.status_code == 200
    assert data["success"] is True
    assert "data" in data
    assert "timestamp" in data
    print("[PASS] Success response format verified")


def test_standardized_error_response():
    """Test that error responses follow the standard format"""
    print("\n=== Testing Standardized Error Response ===")
    
    # Test 404 error
    response = client.get("/api/v1/nonexistent")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    data = response.json()
    assert response.status_code == 404
    assert data["success"] is False
    assert "error" in data
    assert "error_code" in data
    assert "trace_id" in data
    assert "timestamp" in data
    assert "path" in data
    print("[PASS] Error response format verified")


def test_validation_error_handling():
    """Test validation error responses"""
    print("\n=== Testing Validation Error Handling ===")
    
    # This would require a route with validation
    # For now, we'll just verify the schema is available
    from app.core.exception_handler import ValidationException, ErrorDetail
    
    try:
        raise ValidationException(
            message="Invalid input",
            details=[
                ErrorDetail(
                    field="email",
                    message="Invalid email format",
                    type="value_error.email"
                )
            ]
        )
    except ValidationException as e:
        assert e.message == "Invalid input"
        assert e.status_code == 422
        assert e.error_code == "VALIDATION_ERROR"
        assert len(e.details) == 1
        print("[PASS] Validation exception handling verified")


def test_custom_exceptions():
    """Test custom exception classes"""
    print("\n=== Testing Custom Exceptions ===")
    
    from app.core.exception_handler import (
        NotFoundException,
        UnauthorizedException,
        ForbiddenException,
        ConflictException,
        BadRequestException,
        ServiceUnavailableException
    )
    
    exceptions = [
        (NotFoundException("Resource not found", "user"), 404, "USER_NOT_FOUND"),
        (UnauthorizedException(), 401, "UNAUTHORIZED"),
        (ForbiddenException(), 403, "FORBIDDEN"),
        (ConflictException("Duplicate entry"), 409, "CONFLICT"),
        (BadRequestException("Invalid request"), 400, "BAD_REQUEST"),
        (ServiceUnavailableException(), 503, "SERVICE_UNAVAILABLE"),
    ]
    
    for exc, expected_status, expected_code in exceptions:
        assert exc.status_code == expected_status
        assert exc.error_code == expected_code
        print(f"[PASS] {exc.__class__.__name__} verified")


def test_response_builders():
    """Test response builder functions"""
    print("\n=== Testing Response Builders ===")
    
    from app.core.exception_handler import build_success_response, build_error_response
    
    # Test success response builder
    success = build_success_response(
        data={"id": 1, "name": "Test"},
        message="Success"
    )
    assert success["success"] is True
    assert success["data"]["id"] == 1
    assert success["message"] == "Success"
    print("[PASS] Success response builder verified")
    
    # Test error response builder
    error = build_error_response(
        error="Error message",
        status_code=400,
        error_code="TEST_ERROR",
        trace_id="test-trace-id"
    )
    assert error["success"] is False
    assert error["error"] == "Error message"
    assert error["error_code"] == "TEST_ERROR"
    assert error["trace_id"] == "test-trace-id"
    print("[PASS] Error response builder verified")


def test_health_endpoint():
    """Test health endpoint uses standardized response"""
    print("\n=== Testing Health Endpoint ===")
    
    response = client.get("/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    data = response.json()
    assert response.status_code == 200
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"
    print("[PASS] Health endpoint verified")


def test_exception_handler_configuration():
    """Test that exception handlers are configured"""
    print("\n=== Testing Exception Handler Configuration ===")
    
    from app.main import app
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException
    from app.core.exception_handler import AppException
    
    # Check that exception handlers are registered
    exception_handlers = app.exception_handlers
    
    # These should be registered
    assert RequestValidationError in exception_handlers
    assert StarletteHTTPException in exception_handlers
    assert AppException in exception_handlers
    assert Exception in exception_handlers
    
    print("[PASS] Exception handlers configured correctly")


def run_all_tests():
    """Run all verification tests"""
    print("=" * 60)
    print("Exception Handling Verification")
    print("=" * 60)
    
    try:
        test_standardized_success_response()
        test_standardized_error_response()
        test_validation_error_handling()
        test_custom_exceptions()
        test_response_builders()
        test_health_endpoint()
        test_exception_handler_configuration()
        
        print("\n" + "=" * 60)
        print("[PASS] ALL TESTS PASSED")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n[FAIL] UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
