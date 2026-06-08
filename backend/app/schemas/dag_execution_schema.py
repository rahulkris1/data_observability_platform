"""Pydantic schemas for DAG execution API responses"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class DAGExecutionBase(BaseModel):
    """Base schema for DAG execution"""
    dag_id: str
    dag_run_id: str
    execution_date: datetime
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    state: str
    run_type: Optional[str] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    duration_seconds: Optional[float] = None
    conf: Optional[Dict[str, Any]] = None
    task_details: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class DAGExecutionCreate(DAGExecutionBase):
    """Schema for creating a DAG execution record"""
    pass


class DAGExecutionUpdate(BaseModel):
    """Schema for updating a DAG execution record"""
    state: Optional[str] = None
    end_date: Optional[datetime] = None
    total_tasks: Optional[int] = None
    completed_tasks: Optional[int] = None
    failed_tasks: Optional[int] = None
    task_details: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class DAGExecutionResponse(DAGExecutionBase):
    """Schema for DAG execution response"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DAGExecutionListResponse(BaseModel):
    """Schema for list of DAG executions"""
    executions: list[DAGExecutionResponse]
    total: int
    limit: int
    offset: int


class DAGExecutionSummary(BaseModel):
    """Schema for DAG execution summary statistics"""
    total_executions: int
    successful: int
    failed: int
    running: int
    average_duration_seconds: float
    success_rate: float
