"""DAG Execution Service

Provides functionality for storing and retrieving DAG execution metadata
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from app.models.dag_execution import DAGExecution


class DAGExecutionService:
    """Service for managing DAG execution records in PostgreSQL"""
    
    def __init__(self, db: Session):
        """
        Initialize the DAG execution service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create_execution_record(
        self,
        dag_id: str,
        dag_run_id: str,
        execution_date: datetime,
        state: str = "running",
        run_type: str = "manual",
        conf: Optional[Dict[str, Any]] = None,
        start_date: Optional[datetime] = None
    ) -> DAGExecution:
        """
        Create a new DAG execution record.
        
        Args:
            dag_id: DAG identifier
            dag_run_id: Unique run identifier
            execution_date: Logical execution date
            state: Execution state (running, success, failed)
            run_type: Type of run (manual, scheduled)
            conf: DAG run configuration
            start_date: Actual start time
            
        Returns:
            Created DAGExecution record
        """
        execution = DAGExecution(
            dag_id=dag_id,
            dag_run_id=dag_run_id,
            execution_date=execution_date,
            start_date=start_date or datetime.utcnow(),
            state=state,
            run_type=run_type,
            conf=conf or {},
            total_tasks=0,
            completed_tasks=0,
            failed_tasks=0
        )
        
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        return execution
    
    def update_execution_record(
        self,
        dag_run_id: str,
        state: Optional[str] = None,
        end_date: Optional[datetime] = None,
        total_tasks: Optional[int] = None,
        completed_tasks: Optional[int] = None,
        failed_tasks: Optional[int] = None,
        task_details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> Optional[DAGExecution]:
        """
        Update an existing DAG execution record.
        
        Args:
            dag_run_id: Unique run identifier
            state: New execution state
            end_date: Execution end time
            total_tasks: Total number of tasks
            completed_tasks: Number of completed tasks
            failed_tasks: Number of failed tasks
            task_details: Task-level execution details
            error_message: Error message if failed
            
        Returns:
            Updated DAGExecution record or None if not found
        """
        execution = self.db.query(DAGExecution).filter(
            DAGExecution.dag_run_id == dag_run_id
        ).first()
        
        if not execution:
            return None
        
        if state is not None:
            execution.state = state
        if end_date is not None:
            execution.end_date = end_date
            if execution.start_date:
                execution.duration_seconds = (end_date - execution.start_date).total_seconds()
        if total_tasks is not None:
            execution.total_tasks = total_tasks
        if completed_tasks is not None:
            execution.completed_tasks = completed_tasks
        if failed_tasks is not None:
            execution.failed_tasks = failed_tasks
        if task_details is not None:
            execution.task_details = task_details
        if error_message is not None:
            execution.error_message = error_message
        
        self.db.commit()
        self.db.refresh(execution)
        return execution
    
    def get_execution_by_run_id(self, dag_run_id: str) -> Optional[DAGExecution]:
        """
        Get a DAG execution by run ID.
        
        Args:
            dag_run_id: Unique run identifier
            
        Returns:
            DAGExecution record or None
        """
        return self.db.query(DAGExecution).filter(
            DAGExecution.dag_run_id == dag_run_id
        ).first()
    
    def list_executions(
        self,
        dag_id: Optional[str] = None,
        state: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[DAGExecution]:
        """
        List DAG executions with optional filters.
        
        Args:
            dag_id: Filter by DAG ID
            state: Filter by execution state
            start_date: Filter by start date (after)
            end_date: Filter by end date (before)
            limit: Maximum number of records
            offset: Number of records to skip
            
        Returns:
            List of DAGExecution records
        """
        query = self.db.query(DAGExecution)
        
        if dag_id:
            query = query.filter(DAGExecution.dag_id == dag_id)
        if state:
            query = query.filter(DAGExecution.state == state)
        if start_date:
            query = query.filter(DAGExecution.execution_date >= start_date)
        if end_date:
            query = query.filter(DAGExecution.execution_date <= end_date)
        
        return query.order_by(desc(DAGExecution.execution_date)).limit(limit).offset(offset).all()
    
    def get_execution_summary(self, dag_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get execution summary statistics.
        
        Args:
            dag_id: Optional DAG ID filter
            
        Returns:
            Dictionary with summary statistics
        """
        query = self.db.query(DAGExecution)
        
        if dag_id:
            query = query.filter(DAGExecution.dag_id == dag_id)
        
        total = query.count()
        success = query.filter(DAGExecution.state == 'success').count()
        failed = query.filter(DAGExecution.state == 'failed').count()
        running = query.filter(DAGExecution.state == 'running').count()
        
        # Average duration for successful runs
        avg_duration = self.db.query(
            func.avg(DAGExecution.duration_seconds)
        ).filter(
            and_(
                DAGExecution.state == 'success',
                DAGExecution.duration_seconds.isnot(None)
            )
        )
        
        if dag_id:
            avg_duration = avg_duration.filter(DAGExecution.dag_id == dag_id)
        
        avg_duration_result = avg_duration.scalar()
        
        return {
            "total_executions": total,
            "successful": success,
            "failed": failed,
            "running": running,
            "average_duration_seconds": float(avg_duration_result) if avg_duration_result else 0.0,
            "success_rate": (success / total * 100) if total > 0 else 0.0
        }
