"""Pipeline Health Service

Calculates and manages pipeline health scores based on validation, freshness, and latency metrics
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from app.models.health_score import HealthScore
from app.models.validation_log import ValidationLog
from app.models.freshness_metrics import FreshnessMetrics
from app.models.metrics import Metric


class PipelineHealthService:
    """Service for calculating and managing pipeline health scores"""
    
    # Score weights for overall health calculation
    VALIDATION_WEIGHT = 0.4
    FRESHNESS_WEIGHT = 0.3
    LATENCY_WEIGHT = 0.3
    
    # Thresholds for status classification
    HEALTHY_THRESHOLD = 80.0
    DEGRADED_THRESHOLD = 60.0
    
    # Latency thresholds (in seconds)
    EXCELLENT_LATENCY = 60.0  # < 1 minute
    GOOD_LATENCY = 300.0      # < 5 minutes
    ACCEPTABLE_LATENCY = 900.0  # < 15 minutes
    
    def __init__(self, db: Session):
        """Initialize the pipeline health service
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def calculate_validation_score(
        self,
        pipeline_name: str,
        lookback_hours: int = 24
    ) -> Dict[str, Any]:
        """Calculate validation score based on recent validation results
        
        Args:
            pipeline_name: Name of the pipeline
            lookback_hours: Hours to look back for validation data
            
        Returns:
            Dictionary with validation score and metrics
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=lookback_hours)
        
        # Query validation logs
        validations = self.db.query(
            func.count(ValidationLog.id).label('total'),
            func.sum(
                func.case(
                    (ValidationLog.overall_status == 'passed', 1),
                    else_=0
                )
            ).label('passed')
        ).filter(
            and_(
                ValidationLog.dataset_name == pipeline_name,
                ValidationLog.validation_timestamp >= cutoff_time
            )
        ).first()
        
        total = validations.total or 0
        passed = validations.passed or 0
        failed = total - passed
        
        # Calculate pass rate
        if total > 0:
            pass_rate = (passed / total) * 100
            # Validation score is directly proportional to pass rate
            validation_score = pass_rate
        else:
            pass_rate = 0.0
            validation_score = 0.0
        
        return {
            'score': validation_score,
            'total_validations': total,
            'passed_validations': passed,
            'failed_validations': failed,
            'pass_rate': pass_rate
        }
    
    def calculate_freshness_score(
        self,
        pipeline_name: str,
        lookback_hours: int = 24
    ) -> Dict[str, Any]:
        """Calculate freshness score based on SLA compliance
        
        Args:
            pipeline_name: Name of the pipeline
            lookback_hours: Hours to look back for freshness data
            
        Returns:
            Dictionary with freshness score and metrics
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=lookback_hours)
        
        # Query freshness metrics
        freshness_data = self.db.query(
            func.count(FreshnessMetrics.id).label('total'),
            func.sum(
                func.case(
                    (FreshnessMetrics.freshness_status == 'fresh', 1),
                    else_=0
                )
            ).label('fresh'),
            func.sum(
                func.case(
                    (FreshnessMetrics.sla_status == 'met', 1),
                    else_=0
                )
            ).label('sla_met')
        ).filter(
            and_(
                FreshnessMetrics.dataset_name == pipeline_name,
                FreshnessMetrics.ingestion_timestamp >= cutoff_time
            )
        ).first()
        
        total = freshness_data.total or 0
        fresh = freshness_data.fresh or 0
        sla_met = freshness_data.sla_met or 0
        violations = total - fresh
        
        # Calculate freshness score
        if total > 0:
            # 70% weight on freshness, 30% weight on SLA compliance
            freshness_rate = (fresh / total) * 100
            sla_rate = (sla_met / total) * 100
            freshness_score = (freshness_rate * 0.7) + (sla_rate * 0.3)
        else:
            freshness_score = 100.0  # No data means no violations
            violations = 0
        
        return {
            'score': freshness_score,
            'total_checks': total,
            'fresh_count': fresh,
            'violations': violations
        }
    
    def calculate_latency_score(
        self,
        pipeline_name: str,
        lookback_hours: int = 24
    ) -> Dict[str, Any]:
        """Calculate latency score based on processing times
        
        Args:
            pipeline_name: Name of the pipeline
            lookback_hours: Hours to look back for latency data
            
        Returns:
            Dictionary with latency score and metrics
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=lookback_hours)
        
        # Query ingestion and validation latency from freshness metrics
        latency_data = self.db.query(
            func.avg(FreshnessMetrics.ingestion_latency_seconds).label('avg_ingestion'),
            func.avg(FreshnessMetrics.validation_latency_seconds).label('avg_validation')
        ).filter(
            and_(
                FreshnessMetrics.dataset_name == pipeline_name,
                FreshnessMetrics.ingestion_timestamp >= cutoff_time,
                FreshnessMetrics.ingestion_latency_seconds.isnot(None)
            )
        ).first()
        
        avg_ingestion = latency_data.avg_ingestion or 0.0
        avg_validation = latency_data.avg_validation or 0.0
        avg_latency = avg_ingestion + avg_validation
        
        # Calculate latency score using thresholds
        if avg_latency <= self.EXCELLENT_LATENCY:
            latency_score = 100.0
        elif avg_latency <= self.GOOD_LATENCY:
            # Linear decrease from 100 to 80
            latency_score = 100.0 - ((avg_latency - self.EXCELLENT_LATENCY) / 
                                      (self.GOOD_LATENCY - self.EXCELLENT_LATENCY) * 20)
        elif avg_latency <= self.ACCEPTABLE_LATENCY:
            # Linear decrease from 80 to 60
            latency_score = 80.0 - ((avg_latency - self.GOOD_LATENCY) / 
                                     (self.ACCEPTABLE_LATENCY - self.GOOD_LATENCY) * 20)
        else:
            # Exponential decay below 60
            excess = avg_latency - self.ACCEPTABLE_LATENCY
            latency_score = max(0.0, 60.0 - (excess / 60.0))  # Decrease 1 point per minute over threshold
        
        return {
            'score': latency_score,
            'avg_latency_seconds': avg_latency,
            'avg_ingestion_seconds': avg_ingestion,
            'avg_validation_seconds': avg_validation
        }
    
    def calculate_overall_score(
        self,
        validation_score: float,
        freshness_score: float,
        latency_score: float
    ) -> float:
        """Calculate weighted overall health score
        
        Args:
            validation_score: Validation score (0-100)
            freshness_score: Freshness score (0-100)
            latency_score: Latency score (0-100)
            
        Returns:
            Overall health score (0-100)
        """
        overall_score = (
            validation_score * self.VALIDATION_WEIGHT +
            freshness_score * self.FRESHNESS_WEIGHT +
            latency_score * self.LATENCY_WEIGHT
        )
        return round(overall_score, 2)
    
    def determine_status(self, overall_score: float) -> str:
        """Determine health status from overall score
        
        Args:
            overall_score: Overall health score (0-100)
            
        Returns:
            Status string ('healthy', 'degraded', or 'unhealthy')
        """
        if overall_score >= self.HEALTHY_THRESHOLD:
            return 'healthy'
        elif overall_score >= self.DEGRADED_THRESHOLD:
            return 'degraded'
        else:
            return 'unhealthy'
    
    def calculate_pipeline_health(
        self,
        pipeline_name: str,
        lookback_hours: int = 24
    ) -> HealthScore:
        """Calculate comprehensive health score for a pipeline
        
        Args:
            pipeline_name: Name of the pipeline
            lookback_hours: Hours to look back for data
            
        Returns:
            HealthScore model instance
        """
        # Calculate component scores
        validation_metrics = self.calculate_validation_score(pipeline_name, lookback_hours)
        freshness_metrics = self.calculate_freshness_score(pipeline_name, lookback_hours)
        latency_metrics = self.calculate_latency_score(pipeline_name, lookback_hours)
        
        # Calculate overall score
        overall_score = self.calculate_overall_score(
            validation_metrics['score'],
            freshness_metrics['score'],
            latency_metrics['score']
        )
        
        # Determine status
        status = self.determine_status(overall_score)
        
        # Create health score record
        health_score = HealthScore(
            pipeline_name=pipeline_name,
            overall_score=overall_score,
            validation_score=validation_metrics['score'],
            freshness_score=freshness_metrics['score'],
            latency_score=latency_metrics['score'],
            timestamp=datetime.utcnow(),
            validation_pass_rate=validation_metrics.get('pass_rate'),
            freshness_violations=freshness_metrics.get('violations'),
            avg_latency_seconds=latency_metrics.get('avg_latency_seconds'),
            total_validations=validation_metrics.get('total_validations'),
            passed_validations=validation_metrics.get('passed_validations'),
            failed_validations=validation_metrics.get('failed_validations'),
            status=status,
            score_metadata={
                'lookback_hours': lookback_hours,
                'calculation_timestamp': datetime.utcnow().isoformat(),
                'component_weights': {
                    'validation': self.VALIDATION_WEIGHT,
                    'freshness': self.FRESHNESS_WEIGHT,
                    'latency': self.LATENCY_WEIGHT
                },
                'detailed_metrics': {
                    'validation': validation_metrics,
                    'freshness': freshness_metrics,
                    'latency': latency_metrics
                }
            }
        )
        
        # Save to database
        self.db.add(health_score)
        self.db.commit()
        self.db.refresh(health_score)
        
        return health_score
    
    def get_latest_health_score(
        self,
        pipeline_name: str
    ) -> Optional[HealthScore]:
        """Get the most recent health score for a pipeline
        
        Args:
            pipeline_name: Name of the pipeline
            
        Returns:
            Latest HealthScore or None
        """
        return self.db.query(HealthScore).filter(
            HealthScore.pipeline_name == pipeline_name
        ).order_by(desc(HealthScore.timestamp)).first()
    
    def get_health_score_history(
        self,
        pipeline_name: str,
        lookback_hours: int = 168  # 7 days default
    ) -> List[HealthScore]:
        """Get health score history for a pipeline
        
        Args:
            pipeline_name: Name of the pipeline
            lookback_hours: Hours of history to retrieve
            
        Returns:
            List of HealthScore records
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=lookback_hours)
        
        return self.db.query(HealthScore).filter(
            and_(
                HealthScore.pipeline_name == pipeline_name,
                HealthScore.timestamp >= cutoff_time
            )
        ).order_by(HealthScore.timestamp).all()
    
    def get_all_pipeline_health(
        self,
        limit: int = 100
    ) -> List[HealthScore]:
        """Get latest health scores for all pipelines
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of latest HealthScore records per pipeline
        """
        # Subquery to get latest timestamp per pipeline
        subquery = self.db.query(
            HealthScore.pipeline_name,
            func.max(HealthScore.timestamp).label('max_timestamp')
        ).group_by(HealthScore.pipeline_name).subquery()
        
        # Join to get full records
        results = self.db.query(HealthScore).join(
            subquery,
            and_(
                HealthScore.pipeline_name == subquery.c.pipeline_name,
                HealthScore.timestamp == subquery.c.max_timestamp
            )
        ).order_by(desc(HealthScore.overall_score)).limit(limit).all()
        
        return results


def get_pipeline_health_service(db: Session = None) -> PipelineHealthService:
    """Factory function to get a PipelineHealthService instance
    
    Args:
        db: Optional database session
        
    Returns:
        PipelineHealthService instance
    """
    if db is None:
        from app.core.database import SessionLocal
        db = SessionLocal()
    
    return PipelineHealthService(db)
