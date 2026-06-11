"""Freshness Metrics ORM Model

Stores dataset freshness, ingestion latency, and validation latency metrics
"""
from sqlalchemy import Column, String, Float, DateTime, Integer, Index
from app.models.base import BaseModel


class FreshnessMetric(BaseModel):
    """Freshness Metric model for storing dataset freshness and latency data
    
    Attributes:
        dataset_name: Name of the dataset being monitored
        ingestion_timestamp: When the data was ingested
        validation_timestamp: When the validation was completed
        dataset_age_hours: Age of the dataset in hours from ingestion to now
        freshness_status: Current freshness status ('healthy', 'warning', 'critical')
        freshness_threshold_hours: Expected freshness threshold in hours
        ingestion_start_time: When ingestion process started
        ingestion_end_time: When ingestion process completed
        ingestion_latency_seconds: Total ingestion duration in seconds
        validation_start_time: When validation process started
        validation_end_time: When validation process completed
        validation_latency_seconds: Total validation duration in seconds
        sla_threshold_hours: SLA threshold for this dataset in hours
        sla_status: Whether SLA is met ('compliant', 'breached')
        dag_id: Associated DAG ID
        task_id: Associated task ID
    """
    __tablename__ = "freshness_metrics"
    
    # Dataset identification
    dataset_name = Column(String(255), nullable=False, index=True)
    
    # Freshness tracking
    ingestion_timestamp = Column(DateTime, nullable=False, index=True)
    validation_timestamp = Column(DateTime, nullable=True)
    dataset_age_hours = Column(Float, nullable=False)
    freshness_status = Column(String(50), nullable=False, index=True)  # healthy, warning, critical
    freshness_threshold_hours = Column(Float, nullable=False)
    
    # Ingestion latency tracking
    ingestion_start_time = Column(DateTime, nullable=True)
    ingestion_end_time = Column(DateTime, nullable=True)
    ingestion_latency_seconds = Column(Float, nullable=True)
    
    # Validation latency tracking
    validation_start_time = Column(DateTime, nullable=True)
    validation_end_time = Column(DateTime, nullable=True)
    validation_latency_seconds = Column(Float, nullable=True)
    
    # SLA tracking
    sla_threshold_hours = Column(Float, nullable=True)
    sla_status = Column(String(50), nullable=True, index=True)  # compliant, breached
    
    # Optional contextual fields
    dag_id = Column(String(255), nullable=True)
    task_id = Column(String(255), nullable=True)
    
    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_dataset_ingestion_timestamp', 'dataset_name', 'ingestion_timestamp'),
        Index('idx_freshness_status_timestamp', 'freshness_status', 'ingestion_timestamp'),
        Index('idx_sla_status_timestamp', 'sla_status', 'ingestion_timestamp'),
    )
    
    def __repr__(self) -> str:
        """String representation of the freshness metric"""
        return (
            f"<FreshnessMetric(dataset={self.dataset_name}, "
            f"status={self.freshness_status}, "
            f"age={self.dataset_age_hours}h)>"
        )
