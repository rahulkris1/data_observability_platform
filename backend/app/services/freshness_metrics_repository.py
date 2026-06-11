"""Freshness Metrics Repository

Repository for database operations on freshness metrics
"""
from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.models.freshness_metrics import FreshnessMetric


class FreshnessMetricsRepository:
    """Repository for freshness metrics database operations"""
    
    def __init__(self, db: Session):
        """Initialize repository with database session
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create(self, metric_data: Dict) -> FreshnessMetric:
        """Create a new freshness metric record
        
        Args:
            metric_data: Dictionary with metric data
            
        Returns:
            Created FreshnessMetric instance
        """
        metric = FreshnessMetric(**metric_data)
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric
    
    def get_by_id(self, metric_id: int) -> Optional[FreshnessMetric]:
        """Get freshness metric by ID
        
        Args:
            metric_id: ID of the metric
            
        Returns:
            FreshnessMetric instance or None
        """
        return self.db.query(FreshnessMetric).filter(
            FreshnessMetric.id == metric_id
        ).first()
    
    def get_latest_by_dataset(self, dataset_name: str) -> Optional[FreshnessMetric]:
        """Get the latest freshness metric for a dataset
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            Latest FreshnessMetric instance or None
        """
        return self.db.query(FreshnessMetric).filter(
            FreshnessMetric.dataset_name == dataset_name
        ).order_by(FreshnessMetric.ingestion_timestamp.desc()).first()
    
    def get_all(
        self,
        dataset_name: Optional[str] = None,
        freshness_status: Optional[str] = None,
        sla_status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[FreshnessMetric]:
        """Get freshness metrics with optional filters
        
        Args:
            dataset_name: Filter by dataset name
            freshness_status: Filter by freshness status
            sla_status: Filter by SLA status
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of records
            offset: Number of records to skip
            
        Returns:
            List of FreshnessMetric instances
        """
        query = self.db.query(FreshnessMetric)
        
        if dataset_name:
            query = query.filter(FreshnessMetric.dataset_name == dataset_name)
        
        if freshness_status:
            query = query.filter(FreshnessMetric.freshness_status == freshness_status)
        
        if sla_status:
            query = query.filter(FreshnessMetric.sla_status == sla_status)
        
        if start_date:
            query = query.filter(FreshnessMetric.ingestion_timestamp >= start_date)
        
        if end_date:
            query = query.filter(FreshnessMetric.ingestion_timestamp <= end_date)
        
        return query.order_by(
            FreshnessMetric.ingestion_timestamp.desc()
        ).limit(limit).offset(offset).all()
    
    def get_count(
        self,
        dataset_name: Optional[str] = None,
        freshness_status: Optional[str] = None,
        sla_status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """Get count of freshness metrics with optional filters
        
        Args:
            dataset_name: Filter by dataset name
            freshness_status: Filter by freshness status
            sla_status: Filter by SLA status
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            Count of matching records
        """
        query = self.db.query(func.count(FreshnessMetric.id))
        
        if dataset_name:
            query = query.filter(FreshnessMetric.dataset_name == dataset_name)
        
        if freshness_status:
            query = query.filter(FreshnessMetric.freshness_status == freshness_status)
        
        if sla_status:
            query = query.filter(FreshnessMetric.sla_status == sla_status)
        
        if start_date:
            query = query.filter(FreshnessMetric.ingestion_timestamp >= start_date)
        
        if end_date:
            query = query.filter(FreshnessMetric.ingestion_timestamp <= end_date)
        
        return query.scalar()
    
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
        query = self.db.query(FreshnessMetric)
        
        if start_date:
            query = query.filter(FreshnessMetric.ingestion_timestamp >= start_date)
        
        if end_date:
            query = query.filter(FreshnessMetric.ingestion_timestamp <= end_date)
        
        metrics = query.all()
        
        if not metrics:
            return {
                "total_datasets": 0,
                "healthy_count": 0,
                "warning_count": 0,
                "critical_count": 0,
                "sla_compliant_count": 0,
                "sla_breached_count": 0,
                "avg_ingestion_latency_seconds": None,
                "avg_validation_latency_seconds": None,
                "avg_dataset_age_hours": None,
            }
        
        healthy_count = sum(1 for m in metrics if m.freshness_status == "healthy")
        warning_count = sum(1 for m in metrics if m.freshness_status == "warning")
        critical_count = sum(1 for m in metrics if m.freshness_status == "critical")
        
        sla_compliant = sum(1 for m in metrics if m.sla_status == "compliant")
        sla_breached = sum(1 for m in metrics if m.sla_status == "breached")
        
        # Calculate averages
        ingestion_latencies = [m.ingestion_latency_seconds for m in metrics if m.ingestion_latency_seconds is not None]
        validation_latencies = [m.validation_latency_seconds for m in metrics if m.validation_latency_seconds is not None]
        
        avg_ingestion = sum(ingestion_latencies) / len(ingestion_latencies) if ingestion_latencies else None
        avg_validation = sum(validation_latencies) / len(validation_latencies) if validation_latencies else None
        avg_age = sum(m.dataset_age_hours for m in metrics) / len(metrics)
        
        # Get unique dataset count
        unique_datasets = len(set(m.dataset_name for m in metrics))
        
        return {
            "total_datasets": unique_datasets,
            "healthy_count": healthy_count,
            "warning_count": warning_count,
            "critical_count": critical_count,
            "sla_compliant_count": sla_compliant,
            "sla_breached_count": sla_breached,
            "avg_ingestion_latency_seconds": round(avg_ingestion, 2) if avg_ingestion else None,
            "avg_validation_latency_seconds": round(avg_validation, 2) if avg_validation else None,
            "avg_dataset_age_hours": round(avg_age, 2),
        }
    
    def get_time_series(
        self,
        dataset_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[FreshnessMetric]:
        """Get time series data for freshness metrics
        
        Args:
            dataset_name: Filter by dataset name
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            List of FreshnessMetric instances ordered by time
        """
        query = self.db.query(FreshnessMetric)
        
        if dataset_name:
            query = query.filter(FreshnessMetric.dataset_name == dataset_name)
        
        if start_date:
            query = query.filter(FreshnessMetric.ingestion_timestamp >= start_date)
        
        if end_date:
            query = query.filter(FreshnessMetric.ingestion_timestamp <= end_date)
        
        return query.order_by(FreshnessMetric.ingestion_timestamp.asc()).all()
