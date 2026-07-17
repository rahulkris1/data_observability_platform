"""Load Monitoring API Routes

Endpoints for warehouse load monitoring, verification, and retry validation
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.services.load_verification_service import LoadVerificationService
from app.services.load_audit_service import LoadAuditService
from app.services.retry_validation_service import RetryValidationService

router = APIRouter(prefix="/load-monitoring", tags=["Load Monitoring"])


# Pydantic schemas
class LoadStartRequest(BaseModel):
    batch_id: str
    dataset_name: str
    source_system: Optional[str] = None
    source_record_count: Optional[int] = None
    triggered_by: Optional[str] = None
    metadata: Optional[dict] = None


class LoadCompletionRequest(BaseModel):
    batch_id: str
    warehouse_record_count: int
    records_inserted: Optional[int] = None
    records_updated: Optional[int] = None
    records_failed: Optional[int] = None
    notes: Optional[str] = None
    metadata: Optional[dict] = None


class LoadFailureRequest(BaseModel):
    batch_id: str
    failure_reason: str
    error_message: Optional[str] = None
    warehouse_record_count: Optional[int] = None
    failed_record_count: Optional[int] = None
    notes: Optional[str] = None
    metadata: Optional[dict] = None


class RetryValidationRequest(BaseModel):
    batch_id: str
    validated_by: str
    validation_notes: Optional[str] = None


class RetryRevocationRequest(BaseModel):
    batch_id: str
    revoked_by: str
    reason: Optional[str] = None


# Load Audit Endpoints
@router.post("/audit/start")
def log_load_start(
    request: LoadStartRequest,
    db: Session = Depends(get_db)
):
    """Log the start of a batch load operation"""
    try:
        service = LoadAuditService(db)
        audit_log = service.log_load_start(
            batch_id=request.batch_id,
            dataset_name=request.dataset_name,
            source_system=request.source_system,
            source_record_count=request.source_record_count,
            triggered_by=request.triggered_by,
            metadata=request.metadata
        )
        
        return {
            "status": "success",
            "message": "Load start logged successfully",
            "audit_log_id": audit_log.id,
            "batch_id": audit_log.batch_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audit/complete")
def log_load_completion(
    request: LoadCompletionRequest,
    db: Session = Depends(get_db)
):
    """Log the successful completion of a batch load operation"""
    try:
        service = LoadAuditService(db)
        audit_log = service.log_load_completion(
            batch_id=request.batch_id,
            warehouse_record_count=request.warehouse_record_count,
            records_inserted=request.records_inserted,
            records_updated=request.records_updated,
            records_failed=request.records_failed,
            notes=request.notes,
            metadata=request.metadata
        )
        
        return {
            "status": "success",
            "message": "Load completion logged successfully",
            "audit_log_id": audit_log.id,
            "execution_time_seconds": audit_log.execution_time_seconds
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audit/fail")
def log_load_failure(
    request: LoadFailureRequest,
    db: Session = Depends(get_db)
):
    """Log a failed batch load operation"""
    try:
        service = LoadAuditService(db)
        audit_log, failed_load = service.log_load_failure(
            batch_id=request.batch_id,
            failure_reason=request.failure_reason,
            error_message=request.error_message,
            warehouse_record_count=request.warehouse_record_count,
            failed_record_count=request.failed_record_count,
            notes=request.notes,
            metadata=request.metadata
        )
        
        return {
            "status": "success",
            "message": "Load failure logged successfully",
            "audit_log_id": audit_log.id,
            "failed_load_id": failed_load.id,
            "batch_id": failed_load.batch_id
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/history")
def get_load_history(
    dataset_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get load history with optional filters"""
    try:
        service = LoadAuditService(db)
        history = service.get_load_history(
            dataset_name=dataset_name,
            status=status,
            days=days,
            limit=limit
        )
        
        return {
            "status": "success",
            "count": len(history),
            "history": [
                {
                    "id": log.id,
                    "batch_id": log.batch_id,
                    "dataset_name": log.dataset_name,
                    "load_status": log.load_status,
                    "load_started_at": log.load_started_at.isoformat() if log.load_started_at else None,
                    "load_completed_at": log.load_completed_at.isoformat() if log.load_completed_at else None,
                    "source_record_count": log.source_record_count,
                    "warehouse_record_count": log.warehouse_record_count,
                    "records_inserted": log.records_inserted,
                    "records_updated": log.records_updated,
                    "records_failed": log.records_failed,
                    "execution_time_seconds": log.execution_time_seconds,
                    "triggered_by": log.triggered_by,
                    "notes": log.notes
                }
                for log in history
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/statistics")
def get_load_statistics(
    dataset_name: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """Get load statistics and metrics"""
    try:
        service = LoadAuditService(db)
        stats = service.get_load_statistics(
            dataset_name=dataset_name,
            days=days
        )
        
        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Load Verification Endpoints
@router.get("/verify/batch/{batch_id}")
def verify_batch_load(
    batch_id: str,
    dataset_name: str = Query(...),
    source_record_count: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Verify that a batch load completed successfully"""
    try:
        service = LoadVerificationService(db)
        result = service.verify_batch_load(
            batch_id=batch_id,
            dataset_name=dataset_name,
            source_record_count=source_record_count
        )
        
        return {
            "status": "success",
            "verification": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verify/failed-records/{batch_id}")
def get_failed_records_details(
    batch_id: str,
    dataset_name: str = Query(...),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get details of failed records for a batch"""
    try:
        service = LoadVerificationService(db)
        failed_records = service.get_failed_records_details(
            batch_id=batch_id,
            dataset_name=dataset_name,
            limit=limit
        )
        
        return {
            "status": "success",
            "count": len(failed_records),
            "failed_records": failed_records
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verify/dataset/{dataset_name}")
def verify_dataset_completeness(
    dataset_name: str,
    date_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Verify completeness across all batches for a dataset"""
    try:
        date_obj = None
        if date_filter:
            date_obj = datetime.fromisoformat(date_filter)
        
        service = LoadVerificationService(db)
        result = service.verify_dataset_completeness(
            dataset_name=dataset_name,
            date_filter=date_obj
        )
        
        return {
            "status": "success",
            "verification": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Retry Validation Endpoints
@router.post("/retry/validate")
def validate_for_retry(
    request: RetryValidationRequest,
    db: Session = Depends(get_db)
):
    """Validate a failed load and mark it as ready for manual retry"""
    try:
        service = RetryValidationService(db)
        result = service.validate_for_retry(
            batch_id=request.batch_id,
            validated_by=request.validated_by,
            validation_notes=request.validation_notes
        )
        
        return {
            "status": "success",
            "message": "Retry validation completed",
            "validation": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retry/revoke")
def revoke_retry_approval(
    request: RetryRevocationRequest,
    db: Session = Depends(get_db)
):
    """Revoke retry approval for a failed load"""
    try:
        service = RetryValidationService(db)
        failed_load = service.revoke_retry_approval(
            batch_id=request.batch_id,
            revoked_by=request.revoked_by,
            reason=request.reason
        )
        
        return {
            "status": "success",
            "message": "Retry approval revoked",
            "batch_id": failed_load.batch_id
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retry/ready")
def get_retry_ready_loads(
    dataset_name: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get list of failed loads that are validated and ready for manual retry"""
    try:
        service = RetryValidationService(db)
        loads = service.get_retry_ready_loads(
            dataset_name=dataset_name,
            limit=limit
        )
        
        return {
            "status": "success",
            "count": len(loads),
            "retry_ready_loads": [
                {
                    "id": load.id,
                    "batch_id": load.batch_id,
                    "dataset_name": load.dataset_name,
                    "failure_reason": load.failure_reason,
                    "retry_count": load.retry_count,
                    "load_failed_at": load.load_failed_at.isoformat() if load.load_failed_at else None,
                    "retry_validated_at": load.retry_validated_at.isoformat() if load.retry_validated_at else None,
                    "retry_validated_by": load.retry_validated_by
                }
                for load in loads
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retry/summary")
def get_failed_loads_summary(
    dataset_name: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get summary of all failed loads grouped by status"""
    try:
        service = RetryValidationService(db)
        summary = service.get_failed_loads_summary(
            dataset_name=dataset_name
        )
        
        return {
            "status": "success",
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retry/validation-history/{batch_id}")
def get_validation_history(
    batch_id: str,
    db: Session = Depends(get_db)
):
    """Get validation history for a failed load"""
    try:
        service = RetryValidationService(db)
        history = service.get_validation_history(batch_id=batch_id)
        
        return {
            "status": "success",
            "validation_history": history
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
