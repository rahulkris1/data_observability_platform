"""
AWS Glue Service

Handles Glue job execution, monitoring, and status retrieval.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


class GlueService:
    """Service for managing AWS Glue jobs."""
    
    def __init__(self):
        """Initialize Glue service with AWS credentials from settings."""
        session_args = {"region_name": settings.AWS_REGION}
        
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            session_args["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            session_args["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
        
        try:
            self.glue_client = boto3.client('glue', **session_args)
            logger.info(f"Initialized Glue client for region: {settings.AWS_REGION}")
        except Exception as e:
            logger.error(f"Failed to initialize Glue client: {e}")
            self.glue_client = None
    
    def is_available(self) -> bool:
        """
        Check if Glue service is available.
        
        Returns:
            True if Glue client is initialized, False otherwise
        """
        return self.glue_client is not None
    
    def start_job_run(self, job_name: Optional[str] = None, 
                     job_arguments: Optional[Dict[str, str]] = None) -> Optional[str]:
        """
        Start a Glue job run.
        
        Args:
            job_name: Name of Glue job (uses settings if not provided)
            job_arguments: Job arguments to pass
        
        Returns:
            Job run ID if successful, None otherwise
        """
        if not self.is_available():
            logger.error("Glue client not available")
            return None
        
        try:
            job_name = job_name or settings.GLUE_JOB_NAME
            if not job_name:
                logger.error("No Glue job name configured")
                return None
            
            # Default arguments
            default_args = {
                '--S3_BUCKET_RAW': settings.S3_BUCKET_RAW,
                '--S3_BUCKET_PROCESSED': settings.S3_BUCKET_PROCESSED,
                '--DATABASE_URL': settings.DATABASE_URL
            }
            
            # Merge with provided arguments
            if job_arguments:
                default_args.update(job_arguments)
            
            logger.info(f"Starting Glue job: {job_name}")
            
            response = self.glue_client.start_job_run(
                JobName=job_name,
                Arguments=default_args
            )
            
            job_run_id = response['JobRunId']
            logger.info(f"Started Glue job run: {job_run_id}")
            
            return job_run_id
            
        except ClientError as e:
            logger.error(f"Failed to start Glue job: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error starting Glue job: {e}")
            return None
    
    def get_job_run_status(self, job_name: Optional[str] = None, 
                          job_run_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific job run.
        
        Args:
            job_name: Name of Glue job
            job_run_id: Job run ID
        
        Returns:
            Job run status information, or None if not found
        """
        if not self.is_available():
            logger.error("Glue client not available")
            return None
        
        try:
            job_name = job_name or settings.GLUE_JOB_NAME
            if not job_name or not job_run_id:
                logger.error("Job name and run ID required")
                return None
            
            response = self.glue_client.get_job_run(
                JobName=job_name,
                RunId=job_run_id
            )
            
            job_run = response['JobRun']
            
            status = {
                'job_run_id': job_run['Id'],
                'job_name': job_run['JobName'],
                'state': job_run['JobRunState'],
                'started_on': job_run.get('StartedOn'),
                'completed_on': job_run.get('CompletedOn'),
                'execution_time': job_run.get('ExecutionTime', 0),
                'error_message': job_run.get('ErrorMessage'),
                'arguments': job_run.get('Arguments', {})
            }
            
            return status
            
        except ClientError as e:
            logger.error(f"Failed to get job run status: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting job run status: {e}")
            return None
    
    def get_job_runs_history(self, job_name: Optional[str] = None, 
                            max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get history of job runs.
        
        Args:
            job_name: Name of Glue job
            max_results: Maximum number of results to return
        
        Returns:
            List of job run information
        """
        if not self.is_available():
            logger.error("Glue client not available")
            return []
        
        try:
            job_name = job_name or settings.GLUE_JOB_NAME
            if not job_name:
                logger.error("No Glue job name configured")
                return []
            
            response = self.glue_client.get_job_runs(
                JobName=job_name,
                MaxResults=max_results
            )
            
            job_runs = []
            for run in response.get('JobRuns', []):
                job_runs.append({
                    'job_run_id': run['Id'],
                    'job_name': run['JobName'],
                    'state': run['JobRunState'],
                    'started_on': run.get('StartedOn'),
                    'completed_on': run.get('CompletedOn'),
                    'execution_time': run.get('ExecutionTime', 0),
                    'error_message': run.get('ErrorMessage')
                })
            
            logger.info(f"Retrieved {len(job_runs)} job runs")
            return job_runs
            
        except ClientError as e:
            logger.error(f"Failed to get job runs history: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting job runs history: {e}")
            return []
    
    def stop_job_run(self, job_name: Optional[str] = None, 
                    job_run_id: Optional[str] = None) -> bool:
        """
        Stop a running Glue job.
        
        Args:
            job_name: Name of Glue job
            job_run_id: Job run ID to stop
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            logger.error("Glue client not available")
            return False
        
        try:
            job_name = job_name or settings.GLUE_JOB_NAME
            if not job_name or not job_run_id:
                logger.error("Job name and run ID required")
                return False
            
            self.glue_client.batch_stop_job_run(
                JobName=job_name,
                JobRunIds=[job_run_id]
            )
            
            logger.info(f"Stopped job run: {job_run_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to stop job run: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error stopping job run: {e}")
            return False
    
    def get_execution_environment(self) -> Dict[str, Any]:
        """
        Get current execution environment information.
        
        Returns:
            Environment information including mode and configuration
        """
        return {
            'execution_mode': settings.EXECUTION_MODE,
            'is_glue_enabled': settings.EXECUTION_MODE.lower() == 'glue',
            'glue_job_name': settings.GLUE_JOB_NAME,
            'glue_available': self.is_available(),
            'aws_region': settings.AWS_REGION,
            'storage_provider': settings.STORAGE_PROVIDER
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate Glue configuration.
        
        Returns:
            Validation results
        """
        issues = []
        warnings = []
        
        # Check required settings
        if settings.EXECUTION_MODE.lower() == 'glue':
            if not settings.GLUE_JOB_NAME:
                issues.append("GLUE_JOB_NAME not configured")
            
            if not settings.GLUE_IAM_ROLE:
                issues.append("GLUE_IAM_ROLE not configured")
            
            if not settings.GLUE_SCRIPT_BUCKET:
                warnings.append("GLUE_SCRIPT_BUCKET not configured")
            
            if not settings.S3_BUCKET_RAW:
                issues.append("S3_BUCKET_RAW not configured")
            
            if not settings.S3_BUCKET_PROCESSED:
                issues.append("S3_BUCKET_PROCESSED not configured")
            
            if not self.is_available():
                issues.append("Glue client not available - check AWS credentials")
        
        is_valid = len(issues) == 0
        
        return {
            'is_valid': is_valid,
            'issues': issues,
            'warnings': warnings,
            'execution_mode': settings.EXECUTION_MODE
        }


# Global service instance
_glue_service: Optional[GlueService] = None


def get_glue_service() -> GlueService:
    """
    Get or create GlueService instance.
    
    Returns:
        GlueService instance
    """
    global _glue_service
    if _glue_service is None:
        _glue_service = GlueService()
    return _glue_service
