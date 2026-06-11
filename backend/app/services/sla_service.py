"""SLA Service

Service for defining SLA thresholds, evaluating compliance, and detecting breaches
"""
from datetime import datetime
from typing import Dict, Optional, List
from app.schemas.freshness_schema import SLAEvaluationResult


class SLAThresholds:
    """SLA threshold configuration for different datasets"""
    
    # Default SLA thresholds in hours
    DEFAULT_SLA_HOURS = 24.0
    
    # Custom SLA thresholds per dataset (can be configured)
    DATASET_SLA_THRESHOLDS: Dict[str, float] = {
        "customers": 12.0,      # Must be processed within 12 hours
        "orders": 6.0,          # Must be processed within 6 hours
        "transactions": 2.0,    # Must be processed within 2 hours
        "inventory": 24.0,      # Must be processed within 24 hours
        "analytics": 48.0,      # Must be processed within 48 hours
    }
    
    @classmethod
    def get_sla_threshold(cls, dataset_name: str) -> float:
        """Get SLA threshold for a specific dataset
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            SLA threshold in hours
        """
        return cls.DATASET_SLA_THRESHOLDS.get(
            dataset_name.lower(),
            cls.DEFAULT_SLA_HOURS
        )
    
    @classmethod
    def set_sla_threshold(cls, dataset_name: str, threshold_hours: float) -> None:
        """Set custom SLA threshold for a dataset
        
        Args:
            dataset_name: Name of the dataset
            threshold_hours: SLA threshold in hours
        """
        cls.DATASET_SLA_THRESHOLDS[dataset_name.lower()] = threshold_hours
    
    @classmethod
    def get_all_thresholds(cls) -> Dict[str, float]:
        """Get all configured SLA thresholds
        
        Returns:
            Dictionary of dataset names to threshold hours
        """
        return cls.DATASET_SLA_THRESHOLDS.copy()


class SLAService:
    """Service for SLA evaluation and compliance tracking
    
    Evaluates whether datasets meet their SLA requirements and
    calculates compliance metrics.
    """
    
    def __init__(self):
        """Initialize SLA service"""
        self.thresholds = SLAThresholds()
    
    def evaluate_sla(
        self,
        dataset_name: str,
        ingestion_timestamp: datetime,
        completion_timestamp: datetime,
        sla_threshold_hours: Optional[float] = None
    ) -> SLAEvaluationResult:
        """Evaluate SLA compliance for a dataset
        
        Args:
            dataset_name: Name of the dataset
            ingestion_timestamp: When ingestion started
            completion_timestamp: When processing completed
            sla_threshold_hours: Custom SLA threshold (optional)
            
        Returns:
            SLAEvaluationResult with evaluation details
        """
        # Get SLA threshold
        if sla_threshold_hours is None:
            sla_threshold_hours = self.thresholds.get_sla_threshold(dataset_name)
        
        # Calculate actual latency
        latency_delta = completion_timestamp - ingestion_timestamp
        actual_latency_hours = latency_delta.total_seconds() / 3600.0
        
        # Determine SLA status
        sla_status = "compliant" if actual_latency_hours <= sla_threshold_hours else "breached"
        
        # Calculate breach duration if SLA was breached
        breach_duration_hours = None
        if sla_status == "breached":
            breach_duration_hours = actual_latency_hours - sla_threshold_hours
        
        # Calculate compliance percentage (inverse of breach percentage)
        compliance_percentage = None
        if sla_threshold_hours > 0:
            if sla_status == "compliant":
                compliance_percentage = 100.0
            else:
                # Calculate how much over the SLA we are
                compliance_percentage = max(0.0, (sla_threshold_hours / actual_latency_hours) * 100.0)
        
        return SLAEvaluationResult(
            dataset_name=dataset_name,
            sla_threshold_hours=sla_threshold_hours,
            actual_latency_hours=round(actual_latency_hours, 2),
            sla_status=sla_status,
            compliance_percentage=round(compliance_percentage, 2) if compliance_percentage is not None else None,
            breach_duration_hours=round(breach_duration_hours, 2) if breach_duration_hours is not None else None
        )
    
    def detect_sla_breach(
        self,
        dataset_name: str,
        actual_latency_hours: float,
        sla_threshold_hours: Optional[float] = None
    ) -> bool:
        """Detect if an SLA breach has occurred
        
        Args:
            dataset_name: Name of the dataset
            actual_latency_hours: Actual latency in hours
            sla_threshold_hours: Custom SLA threshold (optional)
            
        Returns:
            True if SLA is breached, False otherwise
        """
        if sla_threshold_hours is None:
            sla_threshold_hours = self.thresholds.get_sla_threshold(dataset_name)
        
        return actual_latency_hours > sla_threshold_hours
    
    def calculate_sla_compliance_percentage(
        self,
        compliant_count: int,
        total_count: int
    ) -> float:
        """Calculate overall SLA compliance percentage
        
        Args:
            compliant_count: Number of compliant datasets/operations
            total_count: Total number of datasets/operations
            
        Returns:
            Compliance percentage (0-100)
        """
        if total_count == 0:
            return 100.0
        
        return (compliant_count / total_count) * 100.0
    
    def get_sla_threshold(self, dataset_name: str) -> float:
        """Get SLA threshold for a dataset
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            SLA threshold in hours
        """
        return self.thresholds.get_sla_threshold(dataset_name)
    
    def set_sla_threshold(self, dataset_name: str, threshold_hours: float) -> None:
        """Set SLA threshold for a dataset
        
        Args:
            dataset_name: Name of the dataset
            threshold_hours: SLA threshold in hours
        """
        self.thresholds.set_sla_threshold(dataset_name, threshold_hours)
    
    def get_all_sla_thresholds(self) -> Dict[str, float]:
        """Get all configured SLA thresholds
        
        Returns:
            Dictionary of dataset names to threshold hours
        """
        return self.thresholds.get_all_thresholds()
    
    def evaluate_batch_sla_compliance(
        self,
        evaluations: List[SLAEvaluationResult]
    ) -> Dict[str, any]:
        """Evaluate SLA compliance for a batch of operations
        
        Args:
            evaluations: List of SLA evaluation results
            
        Returns:
            Dictionary with batch compliance metrics
        """
        if not evaluations:
            return {
                "total_operations": 0,
                "compliant_count": 0,
                "breached_count": 0,
                "compliance_percentage": 100.0,
                "avg_latency_hours": 0.0,
                "max_breach_hours": 0.0,
            }
        
        compliant_count = sum(1 for e in evaluations if e.sla_status == "compliant")
        breached_count = len(evaluations) - compliant_count
        
        avg_latency = sum(e.actual_latency_hours for e in evaluations) / len(evaluations)
        
        max_breach = 0.0
        if breached_count > 0:
            max_breach = max(
                e.breach_duration_hours for e in evaluations
                if e.breach_duration_hours is not None
            )
        
        compliance_percentage = self.calculate_sla_compliance_percentage(
            compliant_count,
            len(evaluations)
        )
        
        return {
            "total_operations": len(evaluations),
            "compliant_count": compliant_count,
            "breached_count": breached_count,
            "compliance_percentage": round(compliance_percentage, 2),
            "avg_latency_hours": round(avg_latency, 2),
            "max_breach_hours": round(max_breach, 2),
        }
