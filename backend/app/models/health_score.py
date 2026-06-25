"""Health Score ORM Model

Stores pipeline health scores based on validation, freshness, and latency metrics
"""
from sqlalchemy import Column, String, Float, DateTime, JSON, Index
from app.models.base import BaseModel


class HealthScore(BaseModel):
    """Health Score model for tracking pipeline health metrics
    
    Attributes:
        pipeline_name: Name of the pipeline or dataset being scored
        overall_score: Overall health score (0-100)
        validation_score: Validation success score (0-100)
        freshness_score: Data freshness score (0-100)
        latency_score: Processing latency score (0-100)
        timestamp: Time when the score was calculated
        validation_pass_rate: Percentage of passing validations
        freshness_violations: Number of freshness SLA violations
        avg_latency_seconds: Average processing latency in seconds
        total_validations: Total number of validations run
        passed_validations: Number of passing validations
        failed_validations: Number of failing validations
        status: Overall status ('healthy', 'degraded', 'unhealthy')
        score_metadata: Additional scoring details as JSON
    """
    __tablename__ = "health_scores"
    
    pipeline_name = Column(String(255), nullable=False, index=True)
    overall_score = Column(Float, nullable=False)
    validation_score = Column(Float, nullable=False)
    freshness_score = Column(Float, nullable=False)
    latency_score = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Detailed metrics
    validation_pass_rate = Column(Float, nullable=True)
    freshness_violations = Column(Float, nullable=True)
    avg_latency_seconds = Column(Float, nullable=True)
    total_validations = Column(Float, nullable=True)
    passed_validations = Column(Float, nullable=True)
    failed_validations = Column(Float, nullable=True)
    
    # Status classification
    status = Column(String(50), nullable=False, index=True)
    
    # Additional metadata
    score_metadata = Column(JSON, nullable=True)
    
    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_pipeline_timestamp', 'pipeline_name', 'timestamp'),
        Index('idx_status_timestamp', 'status', 'timestamp'),
        Index('idx_overall_score', 'overall_score'),
    )
    
    def __repr__(self) -> str:
        """String representation of the health score"""
        return f"<HealthScore(pipeline={self.pipeline_name}, score={self.overall_score}, status={self.status})>"
