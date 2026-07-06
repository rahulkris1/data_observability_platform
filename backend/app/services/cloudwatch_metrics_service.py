"""
AWS CloudWatch Metrics Service

Publishes pipeline metrics to AWS CloudWatch for monitoring and observability.
Maintains dual metrics storage: CloudWatch (AWS) + PostgreSQL (local).
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


class CloudWatchMetricsService:
    """Service for publishing metrics to AWS CloudWatch."""
    
    # CloudWatch namespace for our application
    NAMESPACE = "DataObservabilityPlatform"
    
    # Metric dimension types
    DIM_PIPELINE = "Pipeline"
    DIM_DATASET = "Dataset"
    DIM_VALIDATION = "Validation"
    DIM_ENVIRONMENT = "Environment"
    
    def __init__(self):
        """Initialize CloudWatch metrics service with AWS credentials from settings."""
        self.enabled = settings.CLOUDWATCH_ENABLED
        self.cloudwatch_client = None
        
        if self.enabled:
            try:
                session_args = {"region_name": settings.AWS_REGION}
                
                if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                    session_args["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                    session_args["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
                
                self.cloudwatch_client = boto3.client('cloudwatch', **session_args)
                logger.info(f"Initialized CloudWatch metrics service for region: {settings.AWS_REGION}")
            except Exception as e:
                logger.error(f"Failed to initialize CloudWatch client: {e}")
                self.enabled = False
        else:
            logger.info("CloudWatch metrics disabled - using local metrics only")
    
    def is_available(self) -> bool:
        """
        Check if CloudWatch service is available.
        
        Returns:
            True if CloudWatch client is initialized and enabled, False otherwise
        """
        return self.enabled and self.cloudwatch_client is not None
    
    def publish_metric(
        self, 
        metric_name: str,
        value: float,
        unit: str = "None",
        dimensions: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Publish a single metric to CloudWatch.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: CloudWatch unit (Count, Seconds, Bytes, etc.)
            dimensions: Metric dimensions as key-value pairs
            timestamp: Metric timestamp (defaults to now)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            logger.debug(f"CloudWatch not available, skipping metric: {metric_name}")
            return False
        
        try:
            metric_data = {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': timestamp or datetime.utcnow()
            }
            
            # Add dimensions if provided
            if dimensions:
                metric_data['Dimensions'] = [
                    {'Name': key, 'Value': value}
                    for key, value in dimensions.items()
                ]
            
            self.cloudwatch_client.put_metric_data(
                Namespace=self.NAMESPACE,
                MetricData=[metric_data]
            )
            
            logger.debug(f"Published metric to CloudWatch: {metric_name} = {value}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to publish metric to CloudWatch: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing metric to CloudWatch: {e}")
            return False
    
    def publish_pipeline_metrics(
        self,
        pipeline_id: str,
        dataset_name: str,
        metrics: Dict[str, float]
    ) -> bool:
        """
        Publish pipeline execution metrics to CloudWatch.
        
        Args:
            pipeline_id: Pipeline execution ID
            dataset_name: Name of the dataset
            metrics: Dictionary of metric name to value pairs
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            dimensions = {
                self.DIM_PIPELINE: pipeline_id,
                self.DIM_DATASET: dataset_name,
                self.DIM_ENVIRONMENT: settings.EXECUTION_MODE
            }
            
            metric_data = []
            timestamp = datetime.utcnow()
            
            # Build metric data for batch publishing
            for metric_name, value in metrics.items():
                # Determine appropriate unit
                unit = self._get_metric_unit(metric_name)
                
                metric_data.append({
                    'MetricName': metric_name,
                    'Value': value,
                    'Unit': unit,
                    'Timestamp': timestamp,
                    'Dimensions': [
                        {'Name': key, 'Value': val}
                        for key, val in dimensions.items()
                    ]
                })
            
            # Publish in batches (CloudWatch limit is 20 metrics per call)
            batch_size = 20
            for i in range(0, len(metric_data), batch_size):
                batch = metric_data[i:i + batch_size]
                self.cloudwatch_client.put_metric_data(
                    Namespace=self.NAMESPACE,
                    MetricData=batch
                )
            
            logger.info(f"Published {len(metric_data)} pipeline metrics to CloudWatch")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish pipeline metrics: {e}")
            return False
    
    def publish_validation_metrics(
        self,
        validation_id: str,
        dataset_name: str,
        validation_type: str,
        passed: int,
        failed: int,
        duration_seconds: float
    ) -> bool:
        """
        Publish validation metrics to CloudWatch.
        
        Args:
            validation_id: Validation execution ID
            dataset_name: Name of the dataset
            validation_type: Type of validation
            passed: Number of validation checks passed
            failed: Number of validation checks failed
            duration_seconds: Validation duration in seconds
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            dimensions = {
                self.DIM_VALIDATION: validation_type,
                self.DIM_DATASET: dataset_name,
                self.DIM_ENVIRONMENT: settings.EXECUTION_MODE
            }
            
            timestamp = datetime.utcnow()
            
            metric_data = [
                {
                    'MetricName': 'ValidationChecksPassed',
                    'Value': passed,
                    'Unit': 'Count',
                    'Timestamp': timestamp,
                    'Dimensions': [{'Name': k, 'Value': v} for k, v in dimensions.items()]
                },
                {
                    'MetricName': 'ValidationChecksFailed',
                    'Value': failed,
                    'Unit': 'Count',
                    'Timestamp': timestamp,
                    'Dimensions': [{'Name': k, 'Value': v} for k, v in dimensions.items()]
                },
                {
                    'MetricName': 'ValidationDuration',
                    'Value': duration_seconds,
                    'Unit': 'Seconds',
                    'Timestamp': timestamp,
                    'Dimensions': [{'Name': k, 'Value': v} for k, v in dimensions.items()]
                },
                {
                    'MetricName': 'ValidationSuccessRate',
                    'Value': (passed / (passed + failed) * 100) if (passed + failed) > 0 else 0,
                    'Unit': 'Percent',
                    'Timestamp': timestamp,
                    'Dimensions': [{'Name': k, 'Value': v} for k, v in dimensions.items()]
                }
            ]
            
            self.cloudwatch_client.put_metric_data(
                Namespace=self.NAMESPACE,
                MetricData=metric_data
            )
            
            logger.info(f"Published validation metrics to CloudWatch for {validation_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish validation metrics: {e}")
            return False
    
    def publish_data_quality_score(
        self,
        dataset_name: str,
        quality_score: float,
        category_scores: Optional[Dict[str, float]] = None
    ) -> bool:
        """
        Publish data quality scores to CloudWatch.
        
        Args:
            dataset_name: Name of the dataset
            quality_score: Overall quality score (0-100)
            category_scores: Optional category-specific scores
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            dimensions = {
                self.DIM_DATASET: dataset_name,
                self.DIM_ENVIRONMENT: settings.EXECUTION_MODE
            }
            
            timestamp = datetime.utcnow()
            
            metric_data = [
                {
                    'MetricName': 'DataQualityScore',
                    'Value': quality_score,
                    'Unit': 'None',
                    'Timestamp': timestamp,
                    'Dimensions': [{'Name': k, 'Value': v} for k, v in dimensions.items()]
                }
            ]
            
            # Add category-specific scores if provided
            if category_scores:
                for category, score in category_scores.items():
                    metric_data.append({
                        'MetricName': f'QualityScore_{category}',
                        'Value': score,
                        'Unit': 'None',
                        'Timestamp': timestamp,
                        'Dimensions': [{'Name': k, 'Value': v} for k, v in dimensions.items()]
                    })
            
            self.cloudwatch_client.put_metric_data(
                Namespace=self.NAMESPACE,
                MetricData=metric_data
            )
            
            logger.info(f"Published quality scores to CloudWatch for {dataset_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish quality scores: {e}")
            return False
    
    def _get_metric_unit(self, metric_name: str) -> str:
        """
        Determine the appropriate CloudWatch unit for a metric.
        
        Args:
            metric_name: Name of the metric
        
        Returns:
            CloudWatch unit string
        """
        metric_lower = metric_name.lower()
        
        if 'duration' in metric_lower or 'time' in metric_lower or 'latency' in metric_lower:
            return 'Seconds'
        elif 'size' in metric_lower or 'bytes' in metric_lower:
            return 'Bytes'
        elif 'count' in metric_lower or 'records' in metric_lower or 'rows' in metric_lower:
            return 'Count'
        elif 'rate' in metric_lower or 'percent' in metric_lower:
            return 'Percent'
        else:
            return 'None'
    
    def get_metrics_status(self) -> Dict[str, Any]:
        """
        Get CloudWatch metrics service status.
        
        Returns:
            Dictionary with service status information
        """
        return {
            "enabled": self.enabled,
            "available": self.is_available(),
            "namespace": self.NAMESPACE,
            "region": settings.AWS_REGION if self.is_available() else None,
            "provider": "cloudwatch" if self.is_available() else "local"
        }


# Global singleton instance
cloudwatch_metrics_service = CloudWatchMetricsService()
