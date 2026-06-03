"""Audit Log API Router

Endpoints for managing and retrieving audit history
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.audit_schema import (
    AuditLogCreate,
    AuditLogResponse,
    AuditHistoryResponse,
    AuditStatisticsResponse,
    AuditFilterOptions,
)
from app.services.audit_service import AuditService
from app.models.audit_log import AuditLog


router = APIRouter(prefix="/api/v1/audit", tags=["Audit Logs"])


@router.post("/", response_model=AuditLogResponse, status_code=201)
async def create_audit_record(
    audit_data: AuditLogCreate,
    db: Session = Depends(get_db)
):
    """Create a new audit log record"""
    service = AuditService(db)
    
    try:
        audit_log = service.create_audit_record(
            dataset_name=audit_data.dataset_name,
            validation_type=audit_data.validation_type,
            status=audit_data.status,
            execution_time_ms=audit_data.execution_time_ms,
            total_records=audit_data.total_records,
            failed_records=audit_data.failed_records,
            pass_rate=audit_data.pass_rate,
            validator_name=audit_data.validator_name,
            triggered_by=audit_data.triggered_by,
            environment=audit_data.environment,
            metadata=audit_data.metadata,
            error_summary=audit_data.error_summary,
            details=audit_data.details,
        )
        return AuditLogResponse.from_orm(audit_log)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create audit record: {str(e)}")


@router.get("/history", response_model=AuditHistoryResponse)
async def get_audit_history(
    dataset_name: Optional[str] = Query(None, description="Filter by dataset name (partial match)"),
    validation_type: Optional[str] = Query(None, description="Filter by validation type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Filter records on or after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter records on or before this date"),
    triggered_by: Optional[str] = Query(None, description="Filter by who triggered the validation"),
    environment: Optional[str] = Query(None, description="Filter by environment"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip (for pagination)"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order (asc or desc)"),
    db: Session = Depends(get_db)
):
    """Get audit history with optional filtering and sorting"""
    service = AuditService(db)
    
    try:
        # Get audit records
        audits = service.get_audit_history(
            dataset_name=dataset_name,
            validation_type=validation_type,
            status=status,
            start_date=start_date,
            end_date=end_date,
            triggered_by=triggered_by,
            environment=environment,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        
        # Get total count
        total_count = service.get_audit_count(
            dataset_name=dataset_name,
            validation_type=validation_type,
            status=status,
            start_date=start_date,
            end_date=end_date,
            triggered_by=triggered_by,
            environment=environment,
        )
        
        # Convert to response models
        audit_responses = [AuditLogResponse.from_orm(audit) for audit in audits]
        
        return AuditHistoryResponse(
            total_count=total_count,
            page=offset // limit,
            page_size=limit,
            audits=audit_responses,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve audit history: {str(e)}")


@router.get("/{audit_id}", response_model=AuditLogResponse)
async def get_audit_by_id(
    audit_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific audit record by ID"""
    service = AuditService(db)
    
    audit = service.get_audit_by_id(audit_id)
    
    if not audit:
        raise HTTPException(
            status_code=404,
            detail=f"Audit record with ID {audit_id} not found"
        )
    
    return AuditLogResponse.from_orm(audit)


@router.get("/statistics/summary", response_model=AuditStatisticsResponse)
async def get_audit_statistics(
    dataset_name: Optional[str] = Query(None, description="Filter by dataset name"),
    start_date: Optional[datetime] = Query(None, description="Filter records on or after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter records on or before this date"),
    db: Session = Depends(get_db)
):
    """Get aggregated statistics from audit logs"""
    service = AuditService(db)
    
    try:
        stats = service.get_audit_statistics(
            dataset_name=dataset_name,
            start_date=start_date,
            end_date=end_date,
        )
        
        return AuditStatisticsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve statistics: {str(e)}")


@router.get("/filters/options", response_model=AuditFilterOptions)
async def get_filter_options(
    db: Session = Depends(get_db)
):
    """Get available filter options from existing audit records"""
    try:
        # Get distinct values for each filter field
        datasets = db.query(AuditLog.dataset_name).distinct().all()
        validation_types = db.query(AuditLog.validation_type).distinct().all()
        statuses = db.query(AuditLog.status).distinct().all()
        triggered_by_list = db.query(AuditLog.triggered_by).distinct().all()
        environments = db.query(AuditLog.environment).distinct().all()
        
        return AuditFilterOptions(
            datasets=[d[0] for d in datasets if d[0]],
            validation_types=[v[0] for v in validation_types if v[0]],
            statuses=[s[0] for s in statuses if s[0]],
            triggered_by=[t[0] for t in triggered_by_list if t[0]],
            environments=[e[0] for e in environments if e[0]],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve filter options: {str(e)}")


@router.get("/recent/list", response_model=List[AuditLogResponse])
async def get_recent_audits(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of recent records to return"),
    db: Session = Depends(get_db)
):
    """Get the most recent audit records"""
    service = AuditService(db)
    
    try:
        audits = service.get_recent_audits(limit=limit)
        return [AuditLogResponse.from_orm(audit) for audit in audits]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recent audits: {str(e)}")
