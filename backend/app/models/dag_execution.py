"""DAG Execution Model

Stores metadata for Airflow DAG executions
"""
from sqlalchemy import Column, String, DateTime, Integer, JSON, Float
from datetime import datetime

from app.models.base import BaseModel


class DAGExecution(BaseModel):
    """Model for tracking DAG execution metadata"""
    
    __tablename__ = "dag_executions"
    
    dag_id = Column(String(255), nullable=False, index=True)
    dag_run_id = Column(String(255), nullable=False, unique=True, index=True)
    execution_date = Column(DateTime, nullable=False, index=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    state = Column(String(50), nullable=False, index=True)  # running, success, failed
    run_type = Column(String(50), nullable=True)  # manual, scheduled
    
    # Task execution details
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    
    # Performance metrics
    duration_seconds = Column(Float, nullable=True)
    
    # Additional metadata
    conf = Column(JSON, nullable=True)  # DAG run configuration
    task_details = Column(JSON, nullable=True)  # Individual task statuses
    error_message = Column(String(1000), nullable=True)
    
    def __repr__(self):
        return f"<DAGExecution(dag_run_id={self.dag_run_id}, state={self.state})>"
