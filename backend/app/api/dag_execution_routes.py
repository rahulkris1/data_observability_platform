"""DAG Execution Routes

API endpoints for managing and querying DAG execution metadata
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.dag_execution_service import DAGExecutionService
from app.models.dag_execution import DAGExecution


router = APIRouter(prefix="/dag-executions", tags=["dag-executions"])


class DAGExecutionResponse(BaseModel):
    """Response model for DAG execution"""
    id: int
    dag_id: str
    dag_run_id: str
    execution_date: datetime
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    state: str
    run_type: Optional[str]
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    duration_seconds: Optional[float]
    conf: Optional[dict]
    task_details: Optional[dict]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DAGExecutionSummaryResponse(BaseModel):
    """Response model for DAG execution summary"""
    total_executions: int
    successful: int
    failed: int
    running: int
    average_duration_seconds: float
    success_rate: float


class DAGExecutionListResponse(BaseModel):
    """Response model for list of DAG executions"""
    executions: List[DAGExecutionResponse]
    total: int
    limit: int
    offset: int


@router.get("/", response_model=DAGExecutionListResponse)
async def list_dag_executions(
    dag_id: Optional[str] = Query(None, description="Filter by DAG ID"),
    state: Optional[str] = Query(None, description="Filter by state (running, success, failed)"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date (after)"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date (before)"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """
    List DAG executions with optional filters.
    
    - **dag_id**: Filter by specific DAG
    - **state**: Filter by execution state
    - **start_date**: Filter executions after this date
    - **end_date**: Filter executions before this date
    - **limit**: Maximum number of results (default 50)
    - **offset**: Pagination offset (default 0)
    """
    service = DAGExecutionService(db)
    executions = service.list_executions(
        dag_id=dag_id,
        state=state,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    
    # Get total count for pagination
    total_query = db.query(DAGExecution)
    if dag_id:
        total_query = total_query.filter(DAGExecution.dag_id == dag_id)
    if state:
        total_query = total_query.filter(DAGExecution.state == state)
    if start_date:
        total_query = total_query.filter(DAGExecution.execution_date >= start_date)
    if end_date:
        total_query = total_query.filter(DAGExecution.execution_date <= end_date)
    
    total = total_query.count()
    
    return DAGExecutionListResponse(
        executions=[DAGExecutionResponse.from_orm(exec) for exec in executions],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/summary", response_model=DAGExecutionSummaryResponse)
async def get_dag_execution_summary(
    dag_id: Optional[str] = Query(None, description="Filter by DAG ID"),
    db: Session = Depends(get_db)
):
    """
    Get summary statistics for DAG executions.
    
    - **dag_id**: Optional filter by specific DAG
    """
    service = DAGExecutionService(db)
    summary = service.get_execution_summary(dag_id=dag_id)
    return DAGExecutionSummaryResponse(**summary)


@router.get("/{dag_run_id}", response_model=DAGExecutionResponse)
async def get_dag_execution(
    dag_run_id: str,
    db: Session = Depends(get_db)
):
    """
    Get details of a specific DAG execution by run ID.
    
    - **dag_run_id**: Unique DAG run identifier
    """
    service = DAGExecutionService(db)
    execution = service.get_execution_by_run_id(dag_run_id)
    
    if not execution:
        raise HTTPException(status_code=404, detail=f"DAG execution not found: {dag_run_id}")
    
    return DAGExecutionResponse.from_orm(execution)
