"""Metrics Repository

Handles persistence of metrics data to the database
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.metrics import Metric


class MetricsRepository:
    """Repository for managing metrics persistence"""
    
    def __init__(self, db: Session):
        """Initialize repository with database session
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def record_metric(
        self,
        metric_name: str,
        metric_value: float,
        metric_type: str,
        timestamp: Optional[datetime] = None,
        execution_time: Optional[float] = None,
        dataset_name: Optional[str] = None,
        validation_type: Optional[str] = None,
        dag_id: Optional[str] = None,
        task_id: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> Metric:
        """Record a single metric to the database
        
        Args:
            metric_name: Name of the metric
            metric_value: Numeric value of the metric
            metric_type: Type of metric (counter, gauge, histogram)
            timestamp: When the metric was recorded (defaults to now)
            execution_time: Duration in milliseconds
            dataset_name: Associated dataset
            validation_type: Associated validation type
            dag_id: Associated DAG ID
            task_id: Associated task ID
            extra_metadata: Additional metadata
            
        Returns:
            Created Metric instance
        """
        metric = Metric(
            metric_name=metric_name,
            metric_value=metric_value,
            metric_type=metric_type,
            timestamp=timestamp or datetime.utcnow(),
            execution_time=execution_time,
            dataset_name=dataset_name,
            validation_type=validation_type,
            dag_id=dag_id,
            task_id=task_id,
            extra_metadata=extra_metadata
        )
        
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric
    
    # Validation metrics
    def record_validation_success(
        self,
        dataset_name: str,
        validation_type: str,
        execution_time: Optional[float] = None
    ) -> Metric:
        """Record a validation success metric"""
        return self.record_metric(
            metric_name="validation_success",
            metric_value=1,
            metric_type="counter",
            dataset_name=dataset_name,
            validation_type=validation_type,
            execution_time=execution_time
        )
    
    def record_validation_failure(
        self,
        dataset_name: str,
        validation_type: str,
        execution_time: Optional[float] = None,
        error_message: Optional[str] = None
    ) -> Metric:
        """Record a validation failure metric"""
        extra_metadata = {"error": error_message} if error_message else None
        return self.record_metric(
            metric_name="validation_failure",
            metric_value=1,
            metric_type="counter",
            dataset_name=dataset_name,
            validation_type=validation_type,
            execution_time=execution_time,
            metadata=metadata
        )
    
    def record_validation_warning(
        self,
        dataset_name: str,
        validation_type: str,
        execution_time: Optional[float] = None,
        warning_message: Optional[str] = None
    ) -> Metric:
        """Record a validation warning metric"""
        extra_metadata = {"warning": warning_message} if warning_message else None
        return self.record_metric(
            metric_name="validation_warning",
            metric_value=1,
            metric_type="counter",
            dataset_name=dataset_name,
            validation_type=validation_type,
            execution_time=execution_time,
            metadata=metadata
        )
    
    # Ingestion metrics
    def record_ingestion_execution(
        self,
        dataset_name: str,
        dag_id: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> Metric:
        """Record an ingestion execution count"""
        return self.record_metric(
            metric_name="ingestion_execution",
            metric_value=1,
            metric_type="counter",
            dataset_name=dataset_name,
            dag_id=dag_id,
            task_id=task_id
        )
    
    def record_ingestion_success(
        self,
        dataset_name: str,
        execution_time: Optional[float] = None,
        dag_id: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> Metric:
        """Record an ingestion success metric"""
        return self.record_metric(
            metric_name="ingestion_success",
            metric_value=1,
            metric_type="counter",
            dataset_name=dataset_name,
            execution_time=execution_time,
            dag_id=dag_id,
            task_id=task_id
        )
    
    def record_ingestion_failure(
        self,
        dataset_name: str,
        execution_time: Optional[float] = None,
        dag_id: Optional[str] = None,
        task_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Metric:
        """Record an ingestion failure metric"""
        extra_metadata = {"error": error_message} if error_message else None
        return self.record_metric(
            metric_name="ingestion_failure",
            metric_value=1,
            metric_type="counter",
            dataset_name=dataset_name,
            execution_time=execution_time,
            dag_id=dag_id,
            task_id=task_id,
            metadata=metadata
        )
    
    # Duration metrics
    def record_ingestion_duration(
        self,
        dataset_name: str,
        duration_ms: float,
        dag_id: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> Metric:
        """Record ingestion duration metric"""
        return self.record_metric(
            metric_name="ingestion_duration",
            metric_value=duration_ms,
            metric_type="histogram",
            execution_time=duration_ms,
            dataset_name=dataset_name,
            dag_id=dag_id,
            task_id=task_id
        )
    
    def record_validation_duration(
        self,
        dataset_name: str,
        validation_type: str,
        duration_ms: float
    ) -> Metric:
        """Record validation execution duration metric"""
        return self.record_metric(
            metric_name="validation_duration",
            metric_value=duration_ms,
            metric_type="histogram",
            execution_time=duration_ms,
            dataset_name=dataset_name,
            validation_type=validation_type
        )
    
    def record_api_duration(
        self,
        endpoint: str,
        duration_ms: float,
        method: str = "GET",
        status_code: Optional[int] = None
    ) -> Metric:
        """Record API request duration metric"""
        extra_metadata = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code
        }
        return self.record_metric(
            metric_name="api_request_duration",
            metric_value=duration_ms,
            metric_type="histogram",
            execution_time=duration_ms,
            extra_metadata=extra_metadata
        )
    
    # Query methods
    def get_metrics(
        self,
        metric_name: Optional[str] = None,
        metric_type: Optional[str] = None,
        dataset_name: Optional[str] = None,
        validation_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Metric]:
        """Query metrics with filters
        
        Args:
            metric_name: Filter by metric name
            metric_type: Filter by metric type
            dataset_name: Filter by dataset
            validation_type: Filter by validation type
            start_time: Filter metrics after this time
            end_time: Filter metrics before this time
            limit: Maximum number of results
            
        Returns:
            List of Metric instances
        """
        query = self.db.query(Metric)
        
        if metric_name:
            query = query.filter(Metric.metric_name == metric_name)
        if metric_type:
            query = query.filter(Metric.metric_type == metric_type)
        if dataset_name:
            query = query.filter(Metric.dataset_name == dataset_name)
        if validation_type:
            query = query.filter(Metric.validation_type == validation_type)
        if start_time:
            query = query.filter(Metric.timestamp >= start_time)
        if end_time:
            query = query.filter(Metric.timestamp <= end_time)
        
        return query.order_by(Metric.timestamp.desc()).limit(limit).all()
    
    def count_metrics(
        self,
        metric_name: str,
        dataset_name: Optional[str] = None,
        validation_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> int:
        """Count total metric occurrences
        
        Args:
            metric_name: Metric name to count
            dataset_name: Filter by dataset
            validation_type: Filter by validation type
            start_time: Filter metrics after this time
            end_time: Filter metrics before this time
            
        Returns:
            Total count
        """
        query = self.db.query(func.count(Metric.id)).filter(
            Metric.metric_name == metric_name
        )
        
        if dataset_name:
            query = query.filter(Metric.dataset_name == dataset_name)
        if validation_type:
            query = query.filter(Metric.validation_type == validation_type)
        if start_time:
            query = query.filter(Metric.timestamp >= start_time)
        if end_time:
            query = query.filter(Metric.timestamp <= end_time)
        
        return query.scalar() or 0
    
    def delete_old_metrics(self, days_to_keep: int = 30) -> int:
        """Delete metrics older than specified days
        
        Args:
            days_to_keep: Number of days to retain metrics
            
        Returns:
            Number of deleted metrics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        deleted = self.db.query(Metric).filter(
            Metric.timestamp < cutoff_date
        ).delete()
        
        self.db.commit()
        return deleted
