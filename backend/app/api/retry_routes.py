"""Retry API Routes

API endpoints for managing manual validation retries
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_db
from app.services.retry_service import RetryService
from app.services.failure_recovery_service import FailureRecoveryService
from app.services.retry_audit_service import RetryAuditService
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/retries",
    tags=["retries"]
)


# Request/Response Models
class CreateRetryRequest(BaseModel):
    """Request model for creating a retry"""
    validation_log_id: int = Field(..., description="ID of the failed validation log")
    initiated_by: str = Field(..., description="User initiating the retry")
    retry_reason: Optional[str] = Field(None, description="Reason for retry request")
    max_retries: int = Field(3, description="Maximum number of retry attempts")


class ExecuteRetryRequest(BaseModel):
    """Request model for executing a retry"""
    executor: Optional[str] = Field(None, description="User executing the retry")


class BulkExecuteRetryRequest(BaseModel):
    """Request model for bulk retry execution"""
    retry_ids: List[int] = Field(..., description="List of retry IDs to execute")
    executor: Optional[str] = Field(None, description="User executing the retries")


class CancelRetryRequest(BaseModel):
    """Request model for cancelling a retry"""
    cancelled_by: str = Field(..., description="User cancelling the retry")


class RetryResponse(BaseModel):
    """Response model for retry operations"""
    retry_id: int
    validation_log_id: int
    retry_status: str
    retry_count: int
    max_retries: int
    initiated_by: str
    created_at: str
    is_retryable: bool


# Endpoints
@router.post("/", response_model=RetryResponse, status_code=status.HTTP_201_CREATED)
async def create_retry_request(
    request: CreateRetryRequest,
    db: Session = Depends(get_db)
):
    """Create a manual retry request for a failed validation
    
    This endpoint creates a retry request but does NOT execute it.
    Use the execute endpoint to manually trigger the retry.
    """
    try:
        retry_service = RetryService(db)
        retry_entry = retry_service.create_retry_request(
            validation_log_id=request.validation_log_id,
            initiated_by=request.initiated_by,
            retry_reason=request.retry_reason,
            max_retries=request.max_retries
        )
        
        return RetryResponse(
            retry_id=retry_entry.id,
            validation_log_id=retry_entry.validation_log_id,
            retry_status=retry_entry.retry_status,
            retry_count=retry_entry.retry_count,
            max_retries=retry_entry.max_retries,
            initiated_by=retry_entry.initiated_by,
            created_at=retry_entry.created_at.isoformat(),
            is_retryable=retry_entry.is_retryable()
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create retry request: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/{retry_id}/execute", status_code=status.HTTP_200_OK)
async def execute_retry(
    retry_id: int,
    request: ExecuteRetryRequest,
    db: Session = Depends(get_db)
):
    """Execute a manual retry for a failed validation
    
    This endpoint manually triggers the retry execution.
    """
    try:
        recovery_service = FailureRecoveryService(db)
        result = recovery_service.execute_retry(
            retry_id=retry_id,
            executor=request.executor
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute retry: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/execute-bulk", status_code=status.HTTP_200_OK)
async def execute_bulk_retries(
    request: BulkExecuteRetryRequest,
    db: Session = Depends(get_db)
):
    """Execute multiple retries in batch"""
    try:
        recovery_service = FailureRecoveryService(db)
        results = recovery_service.bulk_execute_retries(
            retry_ids=request.retry_ids,
            executor=request.executor
        )
        return results
    except Exception as e:
        logger.error(f"Failed to execute bulk retries: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{retry_id}", response_model=RetryResponse)
async def get_retry_status(
    retry_id: int,
    db: Session = Depends(get_db)
):
    """Get status of a retry request"""
    retry_service = RetryService(db)
    retry_entry = retry_service.get_retry_status(retry_id)
    
    if not retry_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Retry not found")
    
    return RetryResponse(
        retry_id=retry_entry.id,
        validation_log_id=retry_entry.validation_log_id,
        retry_status=retry_entry.retry_status,
        retry_count=retry_entry.retry_count,
        max_retries=retry_entry.max_retries,
        initiated_by=retry_entry.initiated_by,
        created_at=retry_entry.created_at.isoformat(),
        is_retryable=retry_entry.is_retryable()
    )


@router.post("/{retry_id}/cancel", response_model=RetryResponse)
async def cancel_retry(
    retry_id: int,
    request: CancelRetryRequest,
    db: Session = Depends(get_db)
):
    """Cancel a pending retry request"""
    try:
        retry_service = RetryService(db)
        retry_entry = retry_service.cancel_retry(retry_id, request.cancelled_by)
        
        return RetryResponse(
            retry_id=retry_entry.id,
            validation_log_id=retry_entry.validation_log_id,
            retry_status=retry_entry.retry_status,
            retry_count=retry_entry.retry_count,
            max_retries=retry_entry.max_retries,
            initiated_by=retry_entry.initiated_by,
            created_at=retry_entry.created_at.isoformat(),
            is_retryable=retry_entry.is_retryable()
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to cancel retry: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/validation/{validation_log_id}/history")
async def get_validation_retry_history(
    validation_log_id: int,
    db: Session = Depends(get_db)
):
    """Get all retry attempts for a specific validation"""
    retry_service = RetryService(db)
    retries = retry_service.get_retries_for_validation(validation_log_id)
    
    return {
        "validation_log_id": validation_log_id,
        "total_retries": len(retries),
        "retries": [
            {
                "retry_id": r.id,
                "retry_status": r.retry_status,
                "retry_count": r.retry_count,
                "max_retries": r.max_retries,
                "initiated_by": r.initiated_by,
                "retry_reason": r.retry_reason,
                "created_at": r.created_at.isoformat(),
                "last_retry_at": r.last_retry_at.isoformat() if r.last_retry_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "is_retryable": r.is_retryable()
            }
            for r in retries
        ]
    }


@router.get("/validation/{validation_log_id}/timeline")
async def get_retry_timeline(
    validation_log_id: int,
    db: Session = Depends(get_db)
):
    """Get chronological timeline of retry attempts"""
    audit_service = RetryAuditService(db)
    timeline = audit_service.get_retry_timeline(validation_log_id)
    
    return {
        "validation_log_id": validation_log_id,
        "timeline": timeline
    }


@router.get("/pending")
async def get_pending_retries(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get all pending retry requests"""
    retry_service = RetryService(db)
    retries = retry_service.get_pending_retries(limit=limit)
    
    return {
        "total": len(retries),
        "retries": [
            {
                "retry_id": r.id,
                "validation_log_id": r.validation_log_id,
                "retry_status": r.retry_status,
                "retry_count": r.retry_count,
                "max_retries": r.max_retries,
                "initiated_by": r.initiated_by,
                "retry_reason": r.retry_reason,
                "created_at": r.created_at.isoformat()
            }
            for r in retries
        ]
    }


@router.get("/failed-validations")
async def get_failed_validations(
    dataset_name: Optional[str] = Query(None),
    validation_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get failed validations that can be retried"""
    retry_service = RetryService(db)
    validations = retry_service.get_failed_validations(
        dataset_name=dataset_name,
        validation_type=validation_type,
        limit=limit
    )
    
    return {
        "total": len(validations),
        "validations": [
            {
                "validation_log_id": v.id,
                "dataset_name": v.dataset_name,
                "validation_type": v.validation_type,
                "status": v.status,
                "total_records": v.total_records,
                "failed_records": v.failed_records,
                "pass_rate": v.pass_rate,
                "validator_name": v.validator_name,
                "message": v.message,
                "created_at": v.created_at.isoformat(),
                "errors": v.errors
            }
            for v in validations
        ]
    }


@router.get("/history")
async def get_retry_history(
    validation_log_id: Optional[int] = Query(None),
    dataset_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    initiated_by: Optional[str] = Query(None),
    days_back: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get retry execution history with filters and pagination"""
    audit_service = RetryAuditService(db)
    history = audit_service.get_retry_history(
        validation_log_id=validation_log_id,
        dataset_name=dataset_name,
        status=status,
        initiated_by=initiated_by,
        days_back=days_back,
        limit=limit,
        offset=offset
    )
    return history


@router.get("/metrics")
async def get_retry_metrics(
    dataset_name: Optional[str] = Query(None),
    days_back: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get retry metrics and statistics"""
    audit_service = RetryAuditService(db)
    metrics = audit_service.get_retry_metrics(
        dataset_name=dataset_name,
        days_back=days_back
    )
    return metrics


@router.get("/user-activity")
async def get_user_retry_activity(
    days_back: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get retry activity grouped by user"""
    audit_service = RetryAuditService(db)
    activity = audit_service.get_user_retry_activity(days_back=days_back)
    return {
        "users": activity,
        "period_days": days_back
    }


@router.get("/failure-insights")
async def get_failure_insights(
    dataset_name: Optional[str] = Query(None),
    days_back: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get insights about validation failures and retry patterns"""
    audit_service = RetryAuditService(db)
    insights = audit_service.get_failure_insights(
        dataset_name=dataset_name,
        days_back=days_back
    )
    return insights


@router.get("/statistics")
async def get_retry_statistics(
    validation_log_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get retry statistics"""
    retry_service = RetryService(db)
    stats = retry_service.get_retry_statistics(validation_log_id=validation_log_id)
    return stats
