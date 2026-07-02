"""
Glue Job Packager

Packages Glue job scripts and dependencies for deployment to S3.
Handles script validation, dependency bundling, and S3 upload.
"""

import logging
import os
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class GlueJobPackager:
    """
    Package and deploy AWS Glue job scripts to S3.
    """
    
    def __init__(self, aws_region: str = "us-east-1", 
                 aws_access_key: Optional[str] = None,
                 aws_secret_key: Optional[str] = None):
        """
        Initialize Glue job packager.
        
        Args:
            aws_region: AWS region
            aws_access_key: AWS access key ID (optional, uses IAM role if not provided)
            aws_secret_key: AWS secret access key (optional)
        """
        self.region = aws_region
        
        # Initialize S3 client
        session_args = {"region_name": aws_region}
        if aws_access_key and aws_secret_key:
            session_args["aws_access_key_id"] = aws_access_key
            session_args["aws_secret_access_key"] = aws_secret_key
        
        self.s3_client = boto3.client('s3', **session_args)
        logger.info(f"Initialized S3 client for region: {aws_region}")
    
    def validate_script(self, script_path: Path) -> bool:
        """
        Validate Glue job script.
        
        Args:
            script_path: Path to script file
        
        Returns:
            True if valid, False otherwise
        """
        try:
            if not script_path.exists():
                logger.error(f"Script not found: {script_path}")
                return False
            
            if script_path.suffix != ".py":
                logger.error(f"Script must be a Python file: {script_path}")
                return False
            
            # Check if script contains basic Glue imports
            content = script_path.read_text()
            
            # Basic validation - check for common issues
            if len(content.strip()) == 0:
                logger.error("Script is empty")
                return False
            
            logger.info(f"Script validation passed: {script_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Script validation failed: {e}")
            return False
    
    def package_dependencies(self, script_path: Path, 
                            additional_files: Optional[List[Path]] = None,
                            output_dir: Optional[Path] = None) -> Optional[Path]:
        """
        Package script dependencies into a zip file.
        
        Args:
            script_path: Main Glue script
            additional_files: Additional Python files to include
            output_dir: Output directory for zip file
        
        Returns:
            Path to created zip file, or None if packaging failed
        """
        try:
            if output_dir is None:
                output_dir = script_path.parent / "dist"
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"{script_path.stem}_dependencies_{timestamp}.zip"
            zip_path = output_dir / zip_filename
            
            logger.info(f"Creating dependency package: {zip_filename}")
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add main script
                zipf.write(script_path, arcname=script_path.name)
                logger.info(f"  Added: {script_path.name}")
                
                # Add additional files
                if additional_files:
                    for file_path in additional_files:
                        if file_path.exists():
                            arcname = file_path.name
                            zipf.write(file_path, arcname=arcname)
                            logger.info(f"  Added: {arcname}")
            
            logger.info(f"Dependency package created: {zip_path}")
            return zip_path
            
        except Exception as e:
            logger.error(f"Failed to package dependencies: {e}")
            return None
    
    def upload_script_to_s3(self, script_path: Path, bucket_name: str, 
                           s3_key_prefix: str = "glue-scripts") -> Optional[str]:
        """
        Upload Glue script to S3.
        
        Args:
            script_path: Path to script file
            bucket_name: S3 bucket name
            s3_key_prefix: S3 key prefix (folder path)
        
        Returns:
            S3 URI of uploaded script, or None if upload failed
        """
        try:
            # Validate script first
            if not self.validate_script(script_path):
                return None
            
            # Generate S3 key
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            s3_key = f"{s3_key_prefix}/{script_path.stem}_{timestamp}.py"
            
            logger.info(f"Uploading {script_path.name} to s3://{bucket_name}/{s3_key}")
            
            # Upload to S3
            with open(script_path, 'rb') as f:
                self.s3_client.put_object(
                    Bucket=bucket_name,
                    Key=s3_key,
                    Body=f,
                    ContentType='text/x-python'
                )
            
            s3_uri = f"s3://{bucket_name}/{s3_key}"
            logger.info(f"Script uploaded successfully: {s3_uri}")
            
            return s3_uri
            
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            return None
    
    def upload_dependencies_to_s3(self, zip_path: Path, bucket_name: str,
                                  s3_key_prefix: str = "glue-libs") -> Optional[str]:
        """
        Upload dependency zip file to S3.
        
        Args:
            zip_path: Path to zip file
            bucket_name: S3 bucket name
            s3_key_prefix: S3 key prefix
        
        Returns:
            S3 URI of uploaded zip, or None if upload failed
        """
        try:
            s3_key = f"{s3_key_prefix}/{zip_path.name}"
            
            logger.info(f"Uploading {zip_path.name} to s3://{bucket_name}/{s3_key}")
            
            with open(zip_path, 'rb') as f:
                self.s3_client.put_object(
                    Bucket=bucket_name,
                    Key=s3_key,
                    Body=f,
                    ContentType='application/zip'
                )
            
            s3_uri = f"s3://{bucket_name}/{s3_key}"
            logger.info(f"Dependencies uploaded successfully: {s3_uri}")
            
            return s3_uri
            
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return None
    
    def create_or_update_glue_job(self, job_name: str, script_s3_uri: str,
                                  iam_role: str, job_config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create or update AWS Glue job definition.
        
        Args:
            job_name: Glue job name
            script_s3_uri: S3 URI of job script
            iam_role: IAM role ARN for Glue job
            job_config: Additional job configuration
        
        Returns:
            True if successful, False otherwise
        """
        try:
            glue_client = boto3.client('glue', region_name=self.region)
            
            # Default job configuration
            default_config = {
                'WorkerType': 'G.1X',
                'NumberOfWorkers': 2,
                'GlueVersion': '4.0',
                'Timeout': 2880,
                'MaxRetries': 1
            }
            
            # Merge with provided config
            if job_config:
                default_config.update(job_config)
            
            job_params = {
                'Name': job_name,
                'Role': iam_role,
                'Command': {
                    'Name': 'glueetl',
                    'ScriptLocation': script_s3_uri,
                    'PythonVersion': '3'
                },
                'DefaultArguments': {
                    '--enable-metrics': 'true',
                    '--enable-spark-ui': 'true',
                    '--enable-job-insights': 'true',
                    '--job-language': 'python'
                },
                **default_config
            }
            
            try:
                # Try to update existing job
                glue_client.update_job(JobName=job_name, JobUpdate=job_params)
                logger.info(f"Updated Glue job: {job_name}")
            except glue_client.exceptions.EntityNotFoundException:
                # Create new job
                glue_client.create_job(**job_params)
                logger.info(f"Created Glue job: {job_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create/update Glue job: {e}")
            return False
    
    def deploy_glue_job(self, script_path: Path, job_name: str,
                       bucket_name: str, iam_role: str,
                       additional_files: Optional[List[Path]] = None,
                       job_config: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, str]]:
        """
        Full deployment workflow: validate, package, upload, and create/update Glue job.
        
        Args:
            script_path: Path to Glue script
            job_name: Glue job name
            bucket_name: S3 bucket name
            iam_role: IAM role ARN
            additional_files: Additional dependency files
            job_config: Job configuration
        
        Returns:
            Deployment result with S3 URIs, or None if deployment failed
        """
        try:
            logger.info(f"Starting deployment for Glue job: {job_name}")
            
            # Step 1: Validate script
            if not self.validate_script(script_path):
                logger.error("Script validation failed, aborting deployment")
                return None
            
            # Step 2: Upload script to S3
            script_s3_uri = self.upload_script_to_s3(script_path, bucket_name)
            if not script_s3_uri:
                logger.error("Script upload failed, aborting deployment")
                return None
            
            # Step 3: Package and upload dependencies (if any)
            dependencies_s3_uri = None
            if additional_files:
                zip_path = self.package_dependencies(script_path, additional_files)
                if zip_path:
                    dependencies_s3_uri = self.upload_dependencies_to_s3(zip_path, bucket_name)
            
            # Step 4: Create or update Glue job
            if not self.create_or_update_glue_job(job_name, script_s3_uri, iam_role, job_config):
                logger.error("Glue job creation/update failed")
                return None
            
            result = {
                "job_name": job_name,
                "script_s3_uri": script_s3_uri,
                "dependencies_s3_uri": dependencies_s3_uri,
                "status": "deployed"
            }
            
            logger.info(f"Deployment completed successfully: {job_name}")
            return result
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return None


def main():
    """CLI for Glue job packaging and deployment."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Package and deploy AWS Glue jobs")
    parser.add_argument("script_path", help="Path to Glue job script")
    parser.add_argument("--job-name", required=True, help="Glue job name")
    parser.add_argument("--bucket", required=True, help="S3 bucket name")
    parser.add_argument("--role", required=True, help="IAM role ARN")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--worker-type", default="G.1X", help="Worker type")
    parser.add_argument("--workers", type=int, default=2, help="Number of workers")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize packager
    packager = GlueJobPackager(aws_region=args.region)
    
    # Deploy job
    job_config = {
        'WorkerType': args.worker_type,
        'NumberOfWorkers': args.workers
    }
    
    result = packager.deploy_glue_job(
        script_path=Path(args.script_path),
        job_name=args.job_name,
        bucket_name=args.bucket,
        iam_role=args.role,
        job_config=job_config
    )
    
    if result:
        print(f"\nDeployment successful!")
        print(f"Job Name: {result['job_name']}")
        print(f"Script S3 URI: {result['script_s3_uri']}")
    else:
        print("\nDeployment failed!")
        exit(1)


if __name__ == "__main__":
    main()
