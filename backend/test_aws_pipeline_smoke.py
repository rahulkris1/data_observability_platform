"""
End-to-End AWS Pipeline Smoke Test

Tests the complete pipeline flow with S3, Glue, CloudWatch, and Snowflake integration.
Validates that data flows correctly through all AWS services.
"""

import sys
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from app.core.config import settings
from app.services.cloudwatch_metrics_service import cloudwatch_metrics_service
from app.services.cloudwatch_logs_service import cloudwatch_logs_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_s3_operations() -> bool:
    """
    Test S3 read/write operations.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        logger.info("Testing S3 operations...")
        
        # Create S3 client
        session_args = {"region_name": settings.AWS_REGION}
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            session_args["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            session_args["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
        
        s3_client = boto3.client('s3', **session_args)
        
        # Test data
        test_key = f"smoke-test/{datetime.utcnow().isoformat()}/test-data.txt"
        test_data = "This is a smoke test from Data Observability Platform"
        
        # Write to S3
        bucket = settings.S3_BUCKET_RAW
        if not bucket:
            logger.error("S3_BUCKET_RAW not configured")
            return False
        
        logger.info(f"Writing test data to s3://{bucket}/{test_key}")
        s3_client.put_object(
            Bucket=bucket,
            Key=test_key,
            Body=test_data.encode('utf-8')
        )
        logger.info("✓ Write operation successful")
        
        # Read from S3
        logger.info(f"Reading test data from s3://{bucket}/{test_key}")
        response = s3_client.get_object(Bucket=bucket, Key=test_key)
        content = response['Body'].read().decode('utf-8')
        
        if content == test_data:
            logger.info("✓ Read operation successful - data matches")
        else:
            logger.error("✗ Read operation failed - data mismatch")
            return False
        
        # Delete test data
        logger.info(f"Deleting test data from s3://{bucket}/{test_key}")
        s3_client.delete_object(Bucket=bucket, Key=test_key)
        logger.info("✓ Delete operation successful")
        
        return True
        
    except Exception as e:
        logger.error(f"S3 operations test failed: {e}")
        return False


def test_cloudwatch_metrics() -> bool:
    """
    Test CloudWatch metrics publishing.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Testing CloudWatch metrics publishing...")
        
        if not cloudwatch_metrics_service.is_available():
            logger.warning("CloudWatch metrics service not available - skipping test")
            return True
        
        # Publish test metrics
        success = cloudwatch_metrics_service.publish_metric(
            metric_name="SmokeTestMetric",
            value=1.0,
            unit="Count",
            dimensions={
                "TestType": "EndToEnd",
                "Environment": settings.EXECUTION_MODE
            }
        )
        
        if success:
            logger.info("✓ CloudWatch metrics publishing successful")
        else:
            logger.error("✗ CloudWatch metrics publishing failed")
            return False
        
        # Publish pipeline metrics
        test_metrics = {
            "RecordsProcessed": 1000,
            "ProcessingDuration": 45.5,
            "ValidationsPassed": 10,
            "ValidationsFailed": 0
        }
        
        success = cloudwatch_metrics_service.publish_pipeline_metrics(
            pipeline_id="smoke-test-pipeline",
            dataset_name="smoke-test-dataset",
            metrics=test_metrics
        )
        
        if success:
            logger.info("✓ Pipeline metrics publishing successful")
        else:
            logger.error("✗ Pipeline metrics publishing failed")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"CloudWatch metrics test failed: {e}")
        return False


def test_cloudwatch_logs() -> bool:
    """
    Test CloudWatch logs publishing.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Testing CloudWatch logs publishing...")
        
        if not cloudwatch_logs_service.is_available():
            logger.warning("CloudWatch logs service not available - skipping test")
            return True
        
        # Publish test log event
        success = cloudwatch_logs_service.publish_log_event(
            log_stream_name="smoke-test",
            message="This is a smoke test log event",
            level="INFO"
        )
        
        if success:
            logger.info("✓ CloudWatch logs publishing successful")
        else:
            logger.error("✗ CloudWatch logs publishing failed")
            return False
        
        # Publish pipeline logs
        test_logs = [
            "Pipeline execution started",
            "Reading data from S3",
            "Validating schema",
            "Writing processed data",
            "Pipeline execution completed"
        ]
        
        success = cloudwatch_logs_service.publish_pipeline_logs(
            pipeline_id="smoke-test-pipeline",
            dataset_name="smoke-test-dataset",
            logs=test_logs,
            level="INFO"
        )
        
        if success:
            logger.info("✓ Pipeline logs publishing successful")
        else:
            logger.error("✗ Pipeline logs publishing failed")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"CloudWatch logs test failed: {e}")
        return False


def test_glue_job_submission() -> bool:
    """
    Test Glue job submission (does not wait for completion).
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Testing Glue job submission...")
        
        if not settings.GLUE_JOB_NAME:
            logger.warning("GLUE_JOB_NAME not configured - skipping Glue test")
            return True
        
        from app.services.glue_service import GlueService
        
        glue_service = GlueService()
        
        if not glue_service.is_available():
            logger.error("Glue service not available")
            return False
        
        # Submit job run
        job_run_id = glue_service.start_job_run(
            job_arguments={
                '--TEST_MODE': 'true',
                '--SMOKE_TEST': 'true'
            }
        )
        
        if job_run_id:
            logger.info(f"✓ Glue job submitted successfully: {job_run_id}")
            
            # Get job status (don't wait for completion)
            time.sleep(5)  # Brief wait to let job start
            status = glue_service.get_job_run_status(job_run_id=job_run_id)
            
            if status:
                logger.info(f"  Job state: {status.get('state', 'UNKNOWN')}")
                logger.info("  Note: Job is running asynchronously. Check AWS console for final status.")
            
            return True
        else:
            logger.error("✗ Glue job submission failed")
            return False
        
    except Exception as e:
        logger.error(f"Glue job submission test failed: {e}")
        return False


def test_snowflake_operations() -> bool:
    """
    Test Snowflake read/write operations.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Testing Snowflake operations...")
        
        if not settings.SNOWFLAKE_ACCOUNT:
            logger.warning("Snowflake not configured - skipping test")
            return True
        
        try:
            import snowflake.connector
        except ImportError:
            logger.error("snowflake-connector-python not installed")
            return False
        
        # Create connection
        conn = snowflake.connector.connect(
            account=settings.SNOWFLAKE_ACCOUNT,
            user=settings.SNOWFLAKE_USER,
            password=settings.SNOWFLAKE_PASSWORD,
            warehouse=settings.SNOWFLAKE_WAREHOUSE,
            database=settings.SNOWFLAKE_DATABASE,
            schema=settings.SNOWFLAKE_SCHEMA,
            role=settings.SNOWFLAKE_ROLE
        )
        
        cursor = conn.cursor()
        
        # Create test table
        table_name = f"SMOKE_TEST_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Creating test table: {table_name}")
        
        cursor.execute(f"""
            CREATE TEMPORARY TABLE {table_name} (
                id INTEGER,
                name VARCHAR(100),
                timestamp TIMESTAMP_NTZ
            )
        """)
        logger.info("✓ Table creation successful")
        
        # Insert test data
        logger.info("Inserting test data...")
        cursor.execute(f"""
            INSERT INTO {table_name} (id, name, timestamp)
            VALUES
                (1, 'Test Record 1', CURRENT_TIMESTAMP()),
                (2, 'Test Record 2', CURRENT_TIMESTAMP()),
                (3, 'Test Record 3', CURRENT_TIMESTAMP())
        """)
        logger.info("✓ Data insertion successful")
        
        # Read test data
        logger.info("Reading test data...")
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        
        if count == 3:
            logger.info(f"✓ Data read successful - found {count} records")
        else:
            logger.error(f"✗ Data read failed - expected 3 records, found {count}")
            cursor.close()
            conn.close()
            return False
        
        # Drop test table
        logger.info(f"Dropping test table: {table_name}")
        cursor.execute(f"DROP TABLE {table_name}")
        logger.info("✓ Table deletion successful")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Snowflake operations test failed: {e}")
        return False


def main():
    """Run end-to-end AWS pipeline smoke test."""
    print("\n" + "="*80)
    print("End-to-End AWS Pipeline Smoke Test")
    print("="*80 + "\n")
    
    print(f"Execution Mode: {settings.EXECUTION_MODE}")
    print(f"AWS Region: {settings.AWS_REGION}")
    print(f"Storage Provider: {settings.STORAGE_PROVIDER}")
    print(f"CloudWatch Enabled: {settings.CLOUDWATCH_ENABLED}")
    print("\n" + "="*80 + "\n")
    
    all_success = True
    results = {}
    
    # S3 Operations Test
    print("1. Testing S3 Operations...")
    print("-" * 80)
    success = test_s3_operations()
    print()
    results['S3 Operations'] = success
    all_success = all_success and success
    
    # CloudWatch Metrics Test
    print("2. Testing CloudWatch Metrics...")
    print("-" * 80)
    success = test_cloudwatch_metrics()
    print()
    results['CloudWatch Metrics'] = success
    all_success = all_success and success
    
    # CloudWatch Logs Test
    print("3. Testing CloudWatch Logs...")
    print("-" * 80)
    success = test_cloudwatch_logs()
    print()
    results['CloudWatch Logs'] = success
    all_success = all_success and success
    
    # Glue Job Submission Test
    print("4. Testing Glue Job Submission...")
    print("-" * 80)
    success = test_glue_job_submission()
    print()
    results['Glue Job Submission'] = success
    all_success = all_success and success
    
    # Snowflake Operations Test
    print("5. Testing Snowflake Operations...")
    print("-" * 80)
    success = test_snowflake_operations()
    print()
    results['Snowflake Operations'] = success
    all_success = all_success and success
    
    # Summary
    print("="*80)
    print("Smoke Test Summary")
    print("="*80)
    for test_name, success in results.items():
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{test_name}: {status}")
    print("="*80)
    
    if all_success:
        print("\n✓ All smoke tests passed!")
        return 0
    else:
        print("\n✗ Some smoke tests failed. Please check logs for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
