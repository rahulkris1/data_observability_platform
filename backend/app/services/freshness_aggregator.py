"""Freshness Metrics Aggregation Service

Service for aggregating and storing freshness metrics in PostgreSQL
"""
from datetime import datetime
from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.models.freshness_metrics import FreshnessMetric
from app.services.freshness_service import FreshnessService
from app.services.latency_service import LatencyService
from app.services.sla_service import SLAService
from app.services.freshness_metrics_repository import FreshnessMetricsRepository


class FreshnessAggregator:
    """Aggregator for freshness and latency metrics
    
    Combines freshness validation, latency tracking, and SLA evaluation
    to create comprehensive freshness metric records.
    """
    
    def __init__(self, db: Session):
        """Initialize aggregator with database session
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.repository = FreshnessMetricsRepository(db)
        self.freshness_service = FreshnessService()
        self.latency_service = LatencyService()
        self.sla_service = SLAService()
    
    def record_freshness_metric(
        self,
        dataset_name: str,
        ingestion_timestamp: datetime,
        validation_timestamp: Optional[datetime] = None,
        ingestion_start_time: Optional[datetime] = None,
        ingestion_end_time: Optional[datetime] = None,
        validation_start_time: Optional[datetime] = None,
        validation_end_time: Optional[datetime] = None,
        dag_id: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> FreshnessMetric:
        """Record a complete freshness metric
        
        Args:
            dataset_name: Name of the dataset
            ingestion_timestamp: When data was ingested
            validation_timestamp: When validation completed
            ingestion_start_time: When ingestion started
            ingestion_end_time: When ingestion ended
            validation_start_time: When validation started
            validation_end_time: When validation ended
            dag_id: Associated DAG ID
            task_id: Associated task ID
            
        Returns:
            Created FreshnessMetric instance
        """
        # Validate freshness
        freshness_result = self.freshness_service.validate_freshness(
            dataset_name=dataset_name,
            ingestion_timestamp=ingestion_timestamp,
            validation_timestamp=validation_timestamp
        )
        
        # Calculate latencies
        ingestion_latency = None
        if ingestion_start_time and ingestion_end_time:
            ingestion_latency = self.latency_service.calculate_ingestion_latency(
                ingestion_start_time,
                ingestion_end_time
            )
        
        validation_latency = None
        if validation_start_time and validation_end_time:
            validation_latency = self.latency_service.calculate_validation_latency(
                validation_start_time,
                validation_end_time
            )
        
        # Evaluate SLA if we have completion timestamp
        sla_threshold = self.sla_service.get_sla_threshold(dataset_name)
        sla_status = None
        
        if validation_timestamp:
            sla_evaluation = self.sla_service.evaluate_sla(
                dataset_name=dataset_name,
                ingestion_timestamp=ingestion_timestamp,
                completion_timestamp=validation_timestamp,
                sla_threshold_hours=sla_threshold
            )
            sla_status = sla_evaluation.sla_status
        
        # Create metric record
        metric_data = {
            "dataset_name": dataset_name,
            "ingestion_timestamp": ingestion_timestamp,
            "validation_timestamp": validation_timestamp,
            "dataset_age_hours": freshness_result.dataset_age_hours,
            "freshness_status": freshness_result.freshness_status,
            "freshness_threshold_hours": freshness_result.freshness_threshold_hours,
            "ingestion_start_time": ingestion_start_time,
            "ingestion_end_time": ingestion_end_time,
            "ingestion_latency_seconds": ingestion_latency,
            "validation_start_time": validation_start_time,
            "validation_end_time": validation_end_time,
            "validation_latency_seconds": validation_latency,
            "sla_threshold_hours": sla_threshold,
            "sla_status": sla_status,
            "dag_id": dag_id,
            "task_id": task_id,
        }
        
        return self.repository.create(metric_data)
    
    def record_ingestion_completion(
        self,
        dataset_name: str,
        ingestion_start_time: datetime,
        ingestion_end_time: datetime,
        dag_id: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> FreshnessMetric:
        """Record freshness metric at ingestion completion
        
        Args:
            dataset_name: Name of the dataset
            ingestion_start_time: When ingestion started
            ingestion_end_time: When ingestion completed
            dag_id: Associated DAG ID
            task_id: Associated task ID
            
        Returns:
            Created FreshnessMetric instance
        """
        return self.record_freshness_metric(
            dataset_name=dataset_name,
            ingestion_timestamp=ingestion_end_time,
            ingestion_start_time=ingestion_start_time,
            ingestion_end_time=ingestion_end_time,
            dag_id=dag_id,
            task_id=task_id
        )
    
    def record_validation_completion(
        self,
        dataset_name: str,
        ingestion_timestamp: datetime,
        validation_start_time: datetime,
        validation_end_time: datetime,
        ingestion_start_time: Optional[datetime] = None,
        ingestion_end_time: Optional[datetime] = None,
        dag_id: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> FreshnessMetric:
        """Record freshness metric at validation completion
        
        Args:
            dataset_name: Name of the dataset
            ingestion_timestamp: When data was ingested
            validation_start_time: When validation started
            validation_end_time: When validation completed
            ingestion_start_time: When ingestion started (optional)
            ingestion_end_time: When ingestion completed (optional)
            dag_id: Associated DAG ID
            task_id: Associated task ID
            
        Returns:
            Created FreshnessMetric instance
        """
        return self.record_freshness_metric(
            dataset_name=dataset_name,
            ingestion_timestamp=ingestion_timestamp,
            validation_timestamp=validation_end_time,
            ingestion_start_time=ingestion_start_time,
            ingestion_end_time=ingestion_end_time,
            validation_start_time=validation_start_time,
            validation_end_time=validation_end_time,
            dag_id=dag_id,
            task_id=task_id
        )
    
    def get_summary_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """Get summary statistics for freshness metrics
        
        Args:
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            Dictionary with summary statistics
        """
        return self.repository.get_summary_stats(start_date, end_date)
