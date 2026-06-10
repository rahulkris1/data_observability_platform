"""Metrics ORM Model

Stores operational metrics for monitoring and observability
"""
from sqlalchemy import Column, String, Float, DateTime, JSON, Index
from app.models.base import BaseModel


class Metric(BaseModel):
    """Metric model for storing operational metrics
    
    Attributes:
        metric_name: Name of the metric (e.g., 'validation_success', 'ingestion_duration')
        metric_value: Numeric value of the metric
        metric_type: Type of metric ('counter', 'gauge', 'histogram')
        execution_time: Duration in milliseconds (for duration-based metrics)
        timestamp: Time when the metric was recorded
        dataset_name: Associated dataset (optional)
        validation_type: Associated validation type (optional)
        dag_id: Associated DAG ID (optional)
        task_id: Associated task ID (optional)
        extra_metadata: Additional metadata as JSON
    """
    __tablename__ = "metrics"
    
    metric_name = Column(String(255), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_type = Column(String(50), nullable=False, index=True)  # counter, gauge, histogram
    execution_time = Column(Float, nullable=True)  # in milliseconds
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Optional contextual fields
    dataset_name = Column(String(255), nullable=True, index=True)
    validation_type = Column(String(100), nullable=True, index=True)
    dag_id = Column(String(255), nullable=True)
    task_id = Column(String(255), nullable=True)
    
    # Additional metadata
    extra_metadata = Column(JSON, nullable=True)
    
    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_metric_name_timestamp', 'metric_name', 'timestamp'),
        Index('idx_dataset_timestamp', 'dataset_name', 'timestamp'),
        Index('idx_validation_type_timestamp', 'validation_type', 'timestamp'),
    )
    
    def __repr__(self) -> str:
        """String representation of the metric"""
        return f"<Metric(name={self.metric_name}, value={self.metric_value}, timestamp={self.timestamp})>"
