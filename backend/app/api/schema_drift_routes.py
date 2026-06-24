"""Schema Drift API Routes

Provides endpoints for schema drift detection and management
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.schema_drift_service import SchemaDriftService
from app.schemas.schema_drift_schemas import (
    SchemaVersionResponse,
    RegisterSchemaRequest,
    SchemaDriftResponse,
    AcknowledgeDriftRequest,
    SchemaComparisonRequest,
    SchemaComparisonResponse,
    DriftAlertResponse,
    SchemaTimelineItem
)

router = APIRouter(prefix="/api/schema-drift", tags=["Schema Drift"])


@router.post("/register", response_model=dict)
async def register_schema(
    request: RegisterSchemaRequest,
    db: Session = Depends(get_db)
):
    """Register a new schema version and detect drift
    
    Args:
        request: Schema registration request
        db: Database session
        
    Returns:
        Dictionary with schema version and optional drift information
    """
    service = SchemaDriftService(db)
    
    try:
        schema_version, drift_record = service.register_schema(
            dataset_name=request.dataset_name,
            schema_definition=request.schema_definition,
            source=request.source,
            metadata=request.metadata
        )
        
        return {
            "schema_version": SchemaVersionResponse.from_orm(schema_version),
            "drift_detected": drift_record is not None,
            "drift_record": SchemaDriftResponse.from_orm(drift_record) if drift_record else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register schema: {str(e)}")


@router.get("/versions/{dataset_name}", response_model=List[SchemaVersionResponse])
async def get_schema_versions(
    dataset_name: str,
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all schema versions for a dataset
    
    Args:
        dataset_name: Name of the dataset
        limit: Maximum number of versions to return
        db: Database session
        
    Returns:
        List of schema versions
    """
    service = SchemaDriftService(db)
    versions = service.get_all_versions(dataset_name, limit)
    return [SchemaVersionResponse.from_orm(v) for v in versions]


@router.get("/versions/{dataset_name}/latest", response_model=SchemaVersionResponse)
async def get_latest_schema_version(
    dataset_name: str,
    db: Session = Depends(get_db)
):
    """Get the latest schema version for a dataset
    
    Args:
        dataset_name: Name of the dataset
        db: Database session
        
    Returns:
        Latest schema version
    """
    service = SchemaDriftService(db)
    version = service.get_latest_version(dataset_name)
    
    if not version:
        raise HTTPException(status_code=404, detail=f"No schema versions found for dataset '{dataset_name}'")
    
    return SchemaVersionResponse.from_orm(version)


@router.get("/versions/{dataset_name}/{version_number}", response_model=SchemaVersionResponse)
async def get_schema_version(
    dataset_name: str,
    version_number: int,
    db: Session = Depends(get_db)
):
    """Get a specific schema version
    
    Args:
        dataset_name: Name of the dataset
        version_number: Version number
        db: Database session
        
    Returns:
        Schema version
    """
    service = SchemaDriftService(db)
    version = service.get_version_by_number(dataset_name, version_number)
    
    if not version:
        raise HTTPException(
            status_code=404, 
            detail=f"Schema version {version_number} not found for dataset '{dataset_name}'"
        )
    
    return SchemaVersionResponse.from_orm(version)


@router.get("/drift-history", response_model=List[SchemaDriftResponse])
async def get_drift_history(
    dataset_name: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None, regex="^(info|warning|critical)$"),
    acknowledged: Optional[bool] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get drift history with optional filters
    
    Args:
        dataset_name: Filter by dataset name
        severity: Filter by severity (info, warning, critical)
        acknowledged: Filter by acknowledged status
        limit: Maximum number of records to return
        db: Database session
        
    Returns:
        List of drift records
    """
    service = SchemaDriftService(db)
    drift_records = service.get_drift_history(
        dataset_name=dataset_name,
        severity=severity,
        acknowledged=acknowledged,
        limit=limit
    )
    return [SchemaDriftResponse.from_orm(d) for d in drift_records]


@router.get("/drift-history/{dataset_name}", response_model=List[SchemaDriftResponse])
async def get_dataset_drift_history(
    dataset_name: str,
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get drift history for a specific dataset
    
    Args:
        dataset_name: Name of the dataset
        limit: Maximum number of records to return
        db: Database session
        
    Returns:
        List of drift records for the dataset
    """
    service = SchemaDriftService(db)
    drift_records = service.get_drift_history(dataset_name=dataset_name, limit=limit)
    return [SchemaDriftResponse.from_orm(d) for d in drift_records]


@router.post("/drift-history/{drift_id}/acknowledge", response_model=SchemaDriftResponse)
async def acknowledge_drift(
    drift_id: int,
    request: AcknowledgeDriftRequest,
    db: Session = Depends(get_db)
):
    """Acknowledge a drift event
    
    Args:
        drift_id: ID of the drift record
        request: Acknowledgment request
        db: Database session
        
    Returns:
        Updated drift record
    """
    service = SchemaDriftService(db)
    
    try:
        drift = service.acknowledge_drift(
            drift_id=drift_id,
            acknowledged_by=request.acknowledged_by,
            notes=request.notes
        )
        return SchemaDriftResponse.from_orm(drift)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge drift: {str(e)}")


@router.post("/compare", response_model=SchemaComparisonResponse)
async def compare_schemas(
    request: SchemaComparisonRequest,
    db: Session = Depends(get_db)
):
    """Compare two schema versions
    
    Args:
        request: Comparison request
        db: Database session
        
    Returns:
        Comparison results
    """
    service = SchemaDriftService(db)
    
    try:
        comparison = service.compare_schemas(
            dataset_name=request.dataset_name,
            version1=request.version1,
            version2=request.version2
        )
        return SchemaComparisonResponse(**comparison)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare schemas: {str(e)}")


@router.get("/alerts/{dataset_name}", response_model=DriftAlertResponse)
async def get_drift_alerts(
    dataset_name: str,
    db: Session = Depends(get_db)
):
    """Get drift alerts for a dataset
    
    Args:
        dataset_name: Name of the dataset
        db: Database session
        
    Returns:
        Drift alert summary
    """
    service = SchemaDriftService(db)
    
    # Get all drift records for the dataset
    all_drifts = service.get_drift_history(dataset_name=dataset_name, limit=1000)
    unacknowledged = [d for d in all_drifts if not d.acknowledged]
    
    critical = [d for d in unacknowledged if d.severity == "critical"]
    warning = [d for d in unacknowledged if d.severity == "warning"]
    info = [d for d in unacknowledged if d.severity == "info"]
    
    latest_drift = all_drifts[0] if all_drifts else None
    
    return DriftAlertResponse(
        dataset_name=dataset_name,
        total_drifts=len(all_drifts),
        unacknowledged_count=len(unacknowledged),
        critical_count=len(critical),
        warning_count=len(warning),
        info_count=len(info),
        latest_drift=SchemaDriftResponse.from_orm(latest_drift) if latest_drift else None
    )


@router.get("/timeline/{dataset_name}", response_model=List[SchemaTimelineItem])
async def get_schema_timeline(
    dataset_name: str,
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get schema evolution timeline for a dataset
    
    Args:
        dataset_name: Name of the dataset
        limit: Maximum number of timeline items
        db: Database session
        
    Returns:
        List of timeline items showing schema evolution
    """
    service = SchemaDriftService(db)
    
    # Get all versions
    versions = service.get_all_versions(dataset_name, limit)
    
    # Get all drift records
    drifts = service.get_drift_history(dataset_name=dataset_name, limit=limit)
    drift_by_version = {d.current_version_id: d for d in drifts}
    
    timeline = []
    for version in versions:
        drift = drift_by_version.get(version.id)
        timeline.append(SchemaTimelineItem(
            version_number=version.version_number,
            detected_at=version.detected_at,
            source=version.source,
            drift_occurred=drift is not None,
            drift_type=drift.drift_type if drift else None,
            severity=drift.severity if drift else None
        ))
    
    return timeline
