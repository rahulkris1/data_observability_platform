"""Freshness Service

Service for validating dataset freshness and determining freshness status
"""
from datetime import datetime, timedelta
from typing import Dict, Optional
from app.schemas.freshness_schema import FreshnessValidationResult


class FreshnessThresholds:
    """Default freshness thresholds for different dataset types"""
    
    # Default thresholds in hours
    DEFAULT_HEALTHY = 24.0  # Data less than 24 hours old is healthy
    DEFAULT_WARNING = 48.0  # Data between 24-48 hours old is warning
    # Data older than 48 hours is critical
    
    # Custom thresholds per dataset (can be configured)
    DATASET_THRESHOLDS: Dict[str, Dict[str, float]] = {
        "customers": {
            "healthy": 12.0,
            "warning": 24.0,
        },
        "orders": {
            "healthy": 6.0,
            "warning": 12.0,
        },
        "transactions": {
            "healthy": 1.0,
            "warning": 3.0,
        },
        "inventory": {
            "healthy": 24.0,
            "warning": 48.0,
        },
    }
    
    @classmethod
    def get_thresholds(cls, dataset_name: str) -> Dict[str, float]:
        """Get freshness thresholds for a specific dataset
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            Dictionary with 'healthy' and 'warning' threshold values in hours
        """
        return cls.DATASET_THRESHOLDS.get(
            dataset_name.lower(),
            {
                "healthy": cls.DEFAULT_HEALTHY,
                "warning": cls.DEFAULT_WARNING,
            }
        )


class FreshnessService:
    """Service for dataset freshness validation
    
    Validates dataset freshness based on ingestion timestamp and
    determines if data meets freshness requirements.
    """
    
    def __init__(self):
        """Initialize freshness service"""
        self.thresholds = FreshnessThresholds()
    
    def calculate_dataset_age(
        self,
        ingestion_timestamp: datetime,
        current_time: Optional[datetime] = None
    ) -> float:
        """Calculate dataset age in hours
        
        Args:
            ingestion_timestamp: When the data was ingested
            current_time: Current time (defaults to now)
            
        Returns:
            Dataset age in hours
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        age = current_time - ingestion_timestamp
        return age.total_seconds() / 3600.0  # Convert to hours
    
    def determine_freshness_status(
        self,
        dataset_age_hours: float,
        dataset_name: str
    ) -> str:
        """Determine freshness status based on dataset age
        
        Args:
            dataset_age_hours: Age of dataset in hours
            dataset_name: Name of the dataset
            
        Returns:
            Freshness status: 'healthy', 'warning', or 'critical'
        """
        thresholds = self.thresholds.get_thresholds(dataset_name)
        
        if dataset_age_hours <= thresholds["healthy"]:
            return "healthy"
        elif dataset_age_hours <= thresholds["warning"]:
            return "warning"
        else:
            return "critical"
    
    def validate_freshness(
        self,
        dataset_name: str,
        ingestion_timestamp: datetime,
        validation_timestamp: Optional[datetime] = None,
        current_time: Optional[datetime] = None
    ) -> FreshnessValidationResult:
        """Validate dataset freshness and return detailed result
        
        Args:
            dataset_name: Name of the dataset
            ingestion_timestamp: When the data was ingested
            validation_timestamp: When validation was completed (optional)
            current_time: Current time for age calculation (defaults to now)
            
        Returns:
            FreshnessValidationResult with detailed freshness information
        """
        # Calculate dataset age
        dataset_age_hours = self.calculate_dataset_age(
            ingestion_timestamp,
            current_time
        )
        
        # Get thresholds for this dataset
        thresholds = self.thresholds.get_thresholds(dataset_name)
        freshness_threshold_hours = thresholds["healthy"]
        
        # Determine status
        freshness_status = self.determine_freshness_status(
            dataset_age_hours,
            dataset_name
        )
        
        # Check if data is fresh
        is_fresh = freshness_status == "healthy"
        
        # Create human-readable message
        message = self._create_status_message(
            dataset_name,
            dataset_age_hours,
            freshness_status,
            freshness_threshold_hours
        )
        
        return FreshnessValidationResult(
            dataset_name=dataset_name,
            ingestion_timestamp=ingestion_timestamp,
            validation_timestamp=validation_timestamp,
            dataset_age_hours=round(dataset_age_hours, 2),
            freshness_status=freshness_status,
            freshness_threshold_hours=freshness_threshold_hours,
            is_fresh=is_fresh,
            message=message
        )
    
    def _create_status_message(
        self,
        dataset_name: str,
        dataset_age_hours: float,
        status: str,
        threshold_hours: float
    ) -> str:
        """Create a human-readable status message
        
        Args:
            dataset_name: Name of the dataset
            dataset_age_hours: Age in hours
            status: Freshness status
            threshold_hours: Threshold in hours
            
        Returns:
            Human-readable message
        """
        age_str = f"{dataset_age_hours:.1f} hours"
        
        if status == "healthy":
            return (
                f"Dataset '{dataset_name}' is fresh. "
                f"Age: {age_str}, Threshold: {threshold_hours}h"
            )
        elif status == "warning":
            return (
                f"Dataset '{dataset_name}' is aging. "
                f"Age: {age_str}, Expected threshold: {threshold_hours}h"
            )
        else:  # critical
            return (
                f"Dataset '{dataset_name}' is stale! "
                f"Age: {age_str}, Expected threshold: {threshold_hours}h"
            )
    
    def add_custom_threshold(
        self,
        dataset_name: str,
        healthy_hours: float,
        warning_hours: float
    ) -> None:
        """Add or update custom freshness threshold for a dataset
        
        Args:
            dataset_name: Name of the dataset
            healthy_hours: Threshold for healthy status
            warning_hours: Threshold for warning status
        """
        self.thresholds.DATASET_THRESHOLDS[dataset_name.lower()] = {
            "healthy": healthy_hours,
            "warning": warning_hours,
        }
    
    def get_threshold_config(self, dataset_name: str) -> Dict[str, float]:
        """Get the configured thresholds for a dataset
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            Dictionary with threshold configuration
        """
        return self.thresholds.get_thresholds(dataset_name)
