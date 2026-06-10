"""Metrics Service

Provides aggregation and analysis of metrics data
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case

from app.models.metrics import Metric


class MetricsService:
    """Service for aggregating and analyzing metrics"""
    
    def __init__(self, db: Session):
        """Initialize the metrics service
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def aggregate_by_day(
        self,
        metric_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        dataset_name: Optional[str] = None,
        validation_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Aggregate metrics by day
        
        Args:
            metric_name: Name of the metric to aggregate
            start_date: Start date for aggregation
            end_date: End date for aggregation
            dataset_name: Filter by dataset
            validation_type: Filter by validation type
            
        Returns:
            List of daily aggregations with date and value
        """
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Build query
        query = self.db.query(
            func.date(Metric.timestamp).label('date'),
            func.sum(Metric.metric_value).label('total'),
            func.count(Metric.id).label('count'),
            func.avg(Metric.metric_value).label('average'),
            func.min(Metric.metric_value).label('minimum'),
            func.max(Metric.metric_value).label('maximum')
        ).filter(
            and_(
                Metric.metric_name == metric_name,
                Metric.timestamp >= start_date,
                Metric.timestamp <= end_date
            )
        )
        
        if dataset_name:
            query = query.filter(Metric.dataset_name == dataset_name)
        if validation_type:
            query = query.filter(Metric.validation_type == validation_type)
        
        query = query.group_by(func.date(Metric.timestamp)).order_by(func.date(Metric.timestamp))
        
        results = query.all()
        
        return [
            {
                'date': str(row.date),
                'total': float(row.total or 0),
                'count': row.count,
                'average': float(row.average or 0),
                'minimum': float(row.minimum or 0),
                'maximum': float(row.maximum or 0)
            }
            for row in results
        ]
    
    def aggregate_by_validation_type(
        self,
        metric_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        dataset_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Aggregate metrics by validation type
        
        Args:
            metric_name: Name of the metric to aggregate
            start_date: Start date for aggregation
            end_date: End date for aggregation
            dataset_name: Filter by dataset
            
        Returns:
            List of aggregations by validation type
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        query = self.db.query(
            Metric.validation_type,
            func.sum(Metric.metric_value).label('total'),
            func.count(Metric.id).label('count'),
            func.avg(Metric.metric_value).label('average')
        ).filter(
            and_(
                Metric.metric_name == metric_name,
                Metric.timestamp >= start_date,
                Metric.timestamp <= end_date,
                Metric.validation_type.isnot(None)
            )
        )
        
        if dataset_name:
            query = query.filter(Metric.dataset_name == dataset_name)
        
        query = query.group_by(Metric.validation_type).order_by(Metric.validation_type)
        
        results = query.all()
        
        return [
            {
                'validation_type': row.validation_type,
                'total': float(row.total or 0),
                'count': row.count,
                'average': float(row.average or 0)
            }
            for row in results
        ]
    
    def aggregate_by_dataset(
        self,
        metric_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        validation_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Aggregate metrics by dataset
        
        Args:
            metric_name: Name of the metric to aggregate
            start_date: Start date for aggregation
            end_date: End date for aggregation
            validation_type: Filter by validation type
            
        Returns:
            List of aggregations by dataset
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        query = self.db.query(
            Metric.dataset_name,
            func.sum(Metric.metric_value).label('total'),
            func.count(Metric.id).label('count'),
            func.avg(Metric.metric_value).label('average')
        ).filter(
            and_(
                Metric.metric_name == metric_name,
                Metric.timestamp >= start_date,
                Metric.timestamp <= end_date,
                Metric.dataset_name.isnot(None)
            )
        )
        
        if validation_type:
            query = query.filter(Metric.validation_type == validation_type)
        
        query = query.group_by(Metric.dataset_name).order_by(Metric.dataset_name)
        
        results = query.all()
        
        return [
            {
                'dataset_name': row.dataset_name,
                'total': float(row.total or 0),
                'count': row.count,
                'average': float(row.average or 0)
            }
            for row in results
        ]
    
    def get_summary_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        dataset_name: Optional[str] = None,
        validation_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get summary of all key metrics
        
        Args:
            start_date: Start date for aggregation
            end_date: End date for aggregation
            dataset_name: Filter by dataset
            validation_type: Filter by validation type
            
        Returns:
            Dictionary with summary metrics
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=7)  # Default to last 7 days for summary
        
        # Base filter conditions
        base_filters = [
            Metric.timestamp >= start_date,
            Metric.timestamp <= end_date
        ]
        if dataset_name:
            base_filters.append(Metric.dataset_name == dataset_name)
        if validation_type:
            base_filters.append(Metric.validation_type == validation_type)
        
        # Validation metrics
        validation_success = self.db.query(func.count(Metric.id)).filter(
            and_(Metric.metric_name == 'validation_success', *base_filters)
        ).scalar() or 0
        
        validation_failure = self.db.query(func.count(Metric.id)).filter(
            and_(Metric.metric_name == 'validation_failure', *base_filters)
        ).scalar() or 0
        
        validation_warning = self.db.query(func.count(Metric.id)).filter(
            and_(Metric.metric_name == 'validation_warning', *base_filters)
        ).scalar() or 0
        
        # Ingestion metrics
        ingestion_execution = self.db.query(func.count(Metric.id)).filter(
            and_(Metric.metric_name == 'ingestion_execution', *base_filters)
        ).scalar() or 0
        
        ingestion_success = self.db.query(func.count(Metric.id)).filter(
            and_(Metric.metric_name == 'ingestion_success', *base_filters)
        ).scalar() or 0
        
        ingestion_failure = self.db.query(func.count(Metric.id)).filter(
            and_(Metric.metric_name == 'ingestion_failure', *base_filters)
        ).scalar() or 0
        
        # Duration metrics
        validation_duration = self.db.query(
            func.avg(Metric.execution_time)
        ).filter(
            and_(Metric.metric_name == 'validation_duration', *base_filters)
        ).scalar()
        
        ingestion_duration = self.db.query(
            func.avg(Metric.execution_time)
        ).filter(
            and_(Metric.metric_name == 'ingestion_duration', *base_filters)
        ).scalar()
        
        api_duration = self.db.query(
            func.avg(Metric.execution_time)
        ).filter(
            and_(Metric.metric_name == 'api_request_duration', *base_filters)
        ).scalar()
        
        # Calculate rates
        total_validations = validation_success + validation_failure + validation_warning
        validation_success_rate = (
            (validation_success / total_validations * 100) if total_validations > 0 else 0
        )
        
        total_ingestions = ingestion_success + ingestion_failure
        ingestion_success_rate = (
            (ingestion_success / total_ingestions * 100) if total_ingestions > 0 else 0
        )
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': (end_date - start_date).days
            },
            'filters': {
                'dataset_name': dataset_name,
                'validation_type': validation_type
            },
            'validation': {
                'total': total_validations,
                'success': validation_success,
                'failure': validation_failure,
                'warning': validation_warning,
                'success_rate': round(validation_success_rate, 2)
            },
            'ingestion': {
                'total_executions': ingestion_execution,
                'success': ingestion_success,
                'failure': ingestion_failure,
                'success_rate': round(ingestion_success_rate, 2)
            },
            'performance': {
                'avg_validation_duration_ms': round(float(validation_duration or 0), 2),
                'avg_ingestion_duration_ms': round(float(ingestion_duration or 0), 2),
                'avg_api_duration_ms': round(float(api_duration or 0), 2)
            }
        }
    
    def get_time_series(
        self,
        metric_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        dataset_name: Optional[str] = None,
        validation_type: Optional[str] = None,
        interval_hours: int = 1
    ) -> List[Dict[str, Any]]:
        """Get time series data for a metric
        
        Args:
            metric_name: Name of the metric
            start_date: Start date
            end_date: End date
            dataset_name: Filter by dataset
            validation_type: Filter by validation type
            interval_hours: Aggregation interval in hours
            
        Returns:
            List of time series data points
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=1)
        
        # Build query with time bucketing
        query = self.db.query(
            func.date_trunc('hour', Metric.timestamp).label('hour'),
            func.sum(Metric.metric_value).label('total'),
            func.count(Metric.id).label('count'),
            func.avg(Metric.metric_value).label('average')
        ).filter(
            and_(
                Metric.metric_name == metric_name,
                Metric.timestamp >= start_date,
                Metric.timestamp <= end_date
            )
        )
        
        if dataset_name:
            query = query.filter(Metric.dataset_name == dataset_name)
        if validation_type:
            query = query.filter(Metric.validation_type == validation_type)
        
        query = query.group_by(func.date_trunc('hour', Metric.timestamp)).order_by(
            func.date_trunc('hour', Metric.timestamp)
        )
        
        results = query.all()
        
        return [
            {
                'timestamp': row.hour.isoformat() if row.hour else None,
                'total': float(row.total or 0),
                'count': row.count,
                'average': float(row.average or 0)
            }
            for row in results
        ]
