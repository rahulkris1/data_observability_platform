"""
AWS CloudWatch Logs Service

Publishes application logs to CloudWatch Log Groups and Log Streams.
Maintains dual logging: CloudWatch (AWS) + local file system.
"""

import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


class CloudWatchLogsService:
    """Service for publishing logs to AWS CloudWatch Logs."""
    
    # Log group name for our application
    LOG_GROUP_NAME = "/aws/dataobservability/application"
    
    def __init__(self):
        """Initialize CloudWatch Logs service with AWS credentials from settings."""
        self.enabled = settings.CLOUDWATCH_ENABLED
        self.logs_client = None
        self.sequence_tokens: Dict[str, Optional[str]] = {}
        
        if self.enabled:
            try:
                session_args = {"region_name": settings.AWS_REGION}
                
                if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                    session_args["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                    session_args["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
                
                self.logs_client = boto3.client('logs', **session_args)
                logger.info(f"Initialized CloudWatch Logs service for region: {settings.AWS_REGION}")
                
                # Ensure log group exists
                self._ensure_log_group_exists()
                
            except Exception as e:
                logger.error(f"Failed to initialize CloudWatch Logs client: {e}")
                self.enabled = False
        else:
            logger.info("CloudWatch Logs disabled - using local logging only")
    
    def is_available(self) -> bool:
        """
        Check if CloudWatch Logs service is available.
        
        Returns:
            True if CloudWatch Logs client is initialized and enabled, False otherwise
        """
        return self.enabled and self.logs_client is not None
    
    def _ensure_log_group_exists(self) -> bool:
        """
        Ensure the log group exists, create if it doesn't.
        
        Returns:
            True if log group exists or was created, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            # Check if log group exists
            response = self.logs_client.describe_log_groups(
                logGroupNamePrefix=self.LOG_GROUP_NAME,
                limit=1
            )
            
            # Create log group if it doesn't exist
            if not response.get('logGroups'):
                self.logs_client.create_log_group(
                    logGroupName=self.LOG_GROUP_NAME,
                    tags={
                        'Application': 'DataObservabilityPlatform',
                        'Environment': settings.EXECUTION_MODE,
                        'ManagedBy': 'Backend'
                    }
                )
                logger.info(f"Created CloudWatch log group: {self.LOG_GROUP_NAME}")
                
                # Set retention policy (7 days)
                self.logs_client.put_retention_policy(
                    logGroupName=self.LOG_GROUP_NAME,
                    retentionInDays=7
                )
            
            return True
            
        except ClientError as e:
            # Log group might already exist
            if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
                return True
            logger.error(f"Failed to ensure log group exists: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error ensuring log group exists: {e}")
            return False
    
    def _ensure_log_stream_exists(self, log_stream_name: str) -> bool:
        """
        Ensure the log stream exists, create if it doesn't.
        
        Args:
            log_stream_name: Name of the log stream
        
        Returns:
            True if log stream exists or was created, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            # Check if log stream exists
            response = self.logs_client.describe_log_streams(
                logGroupName=self.LOG_GROUP_NAME,
                logStreamNamePrefix=log_stream_name,
                limit=1
            )
            
            # Create log stream if it doesn't exist
            if not response.get('logStreams'):
                self.logs_client.create_log_stream(
                    logGroupName=self.LOG_GROUP_NAME,
                    logStreamName=log_stream_name
                )
                logger.info(f"Created CloudWatch log stream: {log_stream_name}")
                self.sequence_tokens[log_stream_name] = None
            else:
                # Store the upload sequence token
                stream = response['logStreams'][0]
                self.sequence_tokens[log_stream_name] = stream.get('uploadSequenceToken')
            
            return True
            
        except ClientError as e:
            # Log stream might already exist
            if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
                return True
            logger.error(f"Failed to ensure log stream exists: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error ensuring log stream exists: {e}")
            return False
    
    def publish_log_event(
        self,
        log_stream_name: str,
        message: str,
        timestamp: Optional[datetime] = None,
        level: str = "INFO"
    ) -> bool:
        """
        Publish a single log event to CloudWatch Logs.
        
        Args:
            log_stream_name: Name of the log stream
            message: Log message
            timestamp: Log timestamp (defaults to now)
            level: Log level (INFO, WARNING, ERROR, etc.)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            # Ensure log stream exists
            self._ensure_log_stream_exists(log_stream_name)
            
            # Convert timestamp to milliseconds since epoch
            if timestamp is None:
                timestamp = datetime.utcnow()
            timestamp_ms = int(timestamp.timestamp() * 1000)
            
            # Format message with level
            formatted_message = f"[{level}] {message}"
            
            # Prepare log event
            log_event = {
                'timestamp': timestamp_ms,
                'message': formatted_message
            }
            
            # Build put_log_events parameters
            params = {
                'logGroupName': self.LOG_GROUP_NAME,
                'logStreamName': log_stream_name,
                'logEvents': [log_event]
            }
            
            # Add sequence token if we have one
            if self.sequence_tokens.get(log_stream_name):
                params['sequenceToken'] = self.sequence_tokens[log_stream_name]
            
            # Publish log event
            response = self.logs_client.put_log_events(**params)
            
            # Update sequence token for next call
            self.sequence_tokens[log_stream_name] = response.get('nextSequenceToken')
            
            return True
            
        except ClientError as e:
            # Handle invalid sequence token error
            if e.response['Error']['Code'] == 'InvalidSequenceTokenException':
                # Extract the expected sequence token from error message
                expected_token = e.response['Error']['Message'].split('is: ')[-1]
                self.sequence_tokens[log_stream_name] = expected_token if expected_token != 'null' else None
                # Retry once with the correct token
                return self.publish_log_event(log_stream_name, message, timestamp, level)
            
            logger.error(f"Failed to publish log event to CloudWatch: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing log event: {e}")
            return False
    
    def publish_log_events_batch(
        self,
        log_stream_name: str,
        events: List[Dict[str, Any]]
    ) -> bool:
        """
        Publish multiple log events to CloudWatch Logs in batch.
        
        Args:
            log_stream_name: Name of the log stream
            events: List of log events with 'message', 'timestamp', and optional 'level'
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available() or not events:
            return False
        
        try:
            # Ensure log stream exists
            self._ensure_log_stream_exists(log_stream_name)
            
            # Prepare log events
            log_events = []
            for event in events:
                timestamp = event.get('timestamp', datetime.utcnow())
                timestamp_ms = int(timestamp.timestamp() * 1000)
                level = event.get('level', 'INFO')
                message = event.get('message', '')
                
                log_events.append({
                    'timestamp': timestamp_ms,
                    'message': f"[{level}] {message}"
                })
            
            # Sort events by timestamp (required by CloudWatch)
            log_events.sort(key=lambda x: x['timestamp'])
            
            # CloudWatch limit is 10,000 events per batch, but we'll use a smaller batch size
            batch_size = 100
            for i in range(0, len(log_events), batch_size):
                batch = log_events[i:i + batch_size]
                
                # Build put_log_events parameters
                params = {
                    'logGroupName': self.LOG_GROUP_NAME,
                    'logStreamName': log_stream_name,
                    'logEvents': batch
                }
                
                # Add sequence token if we have one
                if self.sequence_tokens.get(log_stream_name):
                    params['sequenceToken'] = self.sequence_tokens[log_stream_name]
                
                # Publish log events
                response = self.logs_client.put_log_events(**params)
                
                # Update sequence token for next call
                self.sequence_tokens[log_stream_name] = response.get('nextSequenceToken')
            
            logger.info(f"Published {len(log_events)} log events to CloudWatch")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to publish log events batch to CloudWatch: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing log events batch: {e}")
            return False
    
    def publish_pipeline_logs(
        self,
        pipeline_id: str,
        dataset_name: str,
        logs: List[str],
        level: str = "INFO"
    ) -> bool:
        """
        Publish pipeline execution logs to CloudWatch.
        
        Args:
            pipeline_id: Pipeline execution ID
            dataset_name: Name of the dataset
            logs: List of log messages
            level: Log level
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available() or not logs:
            return False
        
        # Create log stream name: pipeline/{dataset_name}/{pipeline_id}
        log_stream_name = f"pipeline/{dataset_name}/{pipeline_id}"
        
        # Prepare events
        events = [
            {
                'message': log,
                'timestamp': datetime.utcnow(),
                'level': level
            }
            for log in logs
        ]
        
        return self.publish_log_events_batch(log_stream_name, events)
    
    def publish_validation_logs(
        self,
        validation_id: str,
        dataset_name: str,
        validation_type: str,
        logs: List[str],
        level: str = "INFO"
    ) -> bool:
        """
        Publish validation logs to CloudWatch.
        
        Args:
            validation_id: Validation execution ID
            dataset_name: Name of the dataset
            validation_type: Type of validation
            logs: List of log messages
            level: Log level
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available() or not logs:
            return False
        
        # Create log stream name: validation/{validation_type}/{dataset_name}/{validation_id}
        log_stream_name = f"validation/{validation_type}/{dataset_name}/{validation_id}"
        
        # Prepare events
        events = [
            {
                'message': log,
                'timestamp': datetime.utcnow(),
                'level': level
            }
            for log in logs
        ]
        
        return self.publish_log_events_batch(log_stream_name, events)
    
    def get_logs_status(self) -> Dict[str, Any]:
        """
        Get CloudWatch Logs service status.
        
        Returns:
            Dictionary with service status information
        """
        return {
            "enabled": self.enabled,
            "available": self.is_available(),
            "log_group": self.LOG_GROUP_NAME if self.is_available() else None,
            "region": settings.AWS_REGION if self.is_available() else None,
            "active_streams": len(self.sequence_tokens) if self.is_available() else 0
        }


# Global singleton instance
cloudwatch_logs_service = CloudWatchLogsService()
