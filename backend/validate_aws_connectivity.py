"""
AWS Services & Snowflake Connectivity Validation

Tests connectivity to S3, Glue, CloudWatch, and Snowflake.
Validates that all AWS services and Snowflake are properly configured.
"""

import sys
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime

from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_s3_connectivity() -> Tuple[bool, str]:
    """
    Validate S3 connectivity and bucket access.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        logger.info("Testing S3 connectivity...")
        
        # Create S3 client
        session_args = {"region_name": settings.AWS_REGION}
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            session_args["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            session_args["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
        
        s3_client = boto3.client('s3', **session_args)
        
        # Test bucket access
        buckets_to_test = [
            settings.S3_BUCKET_RAW,
            settings.S3_BUCKET_PROCESSED,
            settings.S3_BUCKET_AUDIT
        ]
        
        results = []
        for bucket in buckets_to_test:
            if not bucket:
                continue
            try:
                s3_client.head_bucket(Bucket=bucket)
                results.append(f"✓ Bucket '{bucket}' accessible")
                logger.info(f"Bucket '{bucket}' accessible")
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404':
                    results.append(f"✗ Bucket '{bucket}' not found")
                    logger.error(f"Bucket '{bucket}' not found")
                    return False, "\n".join(results)
                elif error_code == '403':
                    results.append(f"✗ Access denied to bucket '{bucket}'")
                    logger.error(f"Access denied to bucket '{bucket}'")
                    return False, "\n".join(results)
                else:
                    results.append(f"✗ Error accessing bucket '{bucket}': {error_code}")
                    logger.error(f"Error accessing bucket '{bucket}': {error_code}")
                    return False, "\n".join(results)
        
        return True, "\n".join(results)
        
    except Exception as e:
        logger.error(f"S3 connectivity test failed: {e}")
        return False, f"S3 connectivity test failed: {str(e)}"


def validate_glue_connectivity() -> Tuple[bool, str]:
    """
    Validate AWS Glue connectivity and job access.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        logger.info("Testing Glue connectivity...")
        
        # Create Glue client
        session_args = {"region_name": settings.AWS_REGION}
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            session_args["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            session_args["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
        
        glue_client = boto3.client('glue', **session_args)
        
        results = []
        
        # Test basic Glue access by listing jobs
        try:
            response = glue_client.list_jobs(MaxResults=1)
            results.append("✓ Glue service accessible")
            logger.info("Glue service accessible")
        except ClientError as e:
            results.append(f"✗ Glue service access error: {e.response['Error']['Code']}")
            logger.error(f"Glue service access error: {e.response['Error']['Code']}")
            return False, "\n".join(results)
        
        # Test specific job if configured
        if settings.GLUE_JOB_NAME:
            try:
                response = glue_client.get_job(JobName=settings.GLUE_JOB_NAME)
                results.append(f"✓ Glue job '{settings.GLUE_JOB_NAME}' found")
                logger.info(f"Glue job '{settings.GLUE_JOB_NAME}' found")
            except ClientError as e:
                if e.response['Error']['Code'] == 'EntityNotFoundException':
                    results.append(f"✗ Glue job '{settings.GLUE_JOB_NAME}' not found")
                    logger.warning(f"Glue job '{settings.GLUE_JOB_NAME}' not found")
                else:
                    results.append(f"✗ Error accessing Glue job: {e.response['Error']['Code']}")
                    logger.error(f"Error accessing Glue job: {e.response['Error']['Code']}")
                    return False, "\n".join(results)
        else:
            results.append("⚠ No Glue job name configured")
            logger.warning("No Glue job name configured")
        
        return True, "\n".join(results)
        
    except Exception as e:
        logger.error(f"Glue connectivity test failed: {e}")
        return False, f"Glue connectivity test failed: {str(e)}"


def validate_cloudwatch_connectivity() -> Tuple[bool, str]:
    """
    Validate CloudWatch connectivity and permissions.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        logger.info("Testing CloudWatch connectivity...")
        
        if not settings.CLOUDWATCH_ENABLED:
            return True, "⚠ CloudWatch disabled - skipping validation"
        
        # Create CloudWatch clients
        session_args = {"region_name": settings.AWS_REGION}
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            session_args["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            session_args["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
        
        cw_client = boto3.client('cloudwatch', **session_args)
        logs_client = boto3.client('logs', **session_args)
        
        results = []
        
        # Test CloudWatch Metrics access
        try:
            # Try to list metrics (limit to 1)
            response = cw_client.list_metrics(
                Namespace=settings.CLOUDWATCH_NAMESPACE,
                MaxRecords=1
            )
            results.append("✓ CloudWatch Metrics accessible")
            logger.info("CloudWatch Metrics accessible")
            
            # Test metric publishing
            cw_client.put_metric_data(
                Namespace=settings.CLOUDWATCH_NAMESPACE,
                MetricData=[
                    {
                        'MetricName': 'ConnectivityTest',
                        'Value': 1.0,
                        'Unit': 'Count',
                        'Timestamp': datetime.utcnow()
                    }
                ]
            )
            results.append("✓ CloudWatch Metrics publishing works")
            logger.info("CloudWatch Metrics publishing works")
            
        except ClientError as e:
            results.append(f"✗ CloudWatch Metrics error: {e.response['Error']['Code']}")
            logger.error(f"CloudWatch Metrics error: {e.response['Error']['Code']}")
            return False, "\n".join(results)
        
        # Test CloudWatch Logs access
        try:
            # Try to describe log groups
            response = logs_client.describe_log_groups(
                logGroupNamePrefix=settings.CLOUDWATCH_LOG_GROUP,
                limit=1
            )
            results.append("✓ CloudWatch Logs accessible")
            logger.info("CloudWatch Logs accessible")
            
            # Check if log group exists
            if response.get('logGroups'):
                results.append(f"✓ Log group '{settings.CLOUDWATCH_LOG_GROUP}' exists")
                logger.info(f"Log group '{settings.CLOUDWATCH_LOG_GROUP}' exists")
            else:
                results.append(f"⚠ Log group '{settings.CLOUDWATCH_LOG_GROUP}' does not exist (will be created on first use)")
                logger.warning(f"Log group '{settings.CLOUDWATCH_LOG_GROUP}' does not exist")
            
        except ClientError as e:
            results.append(f"✗ CloudWatch Logs error: {e.response['Error']['Code']}")
            logger.error(f"CloudWatch Logs error: {e.response['Error']['Code']}")
            return False, "\n".join(results)
        
        return True, "\n".join(results)
        
    except Exception as e:
        logger.error(f"CloudWatch connectivity test failed: {e}")
        return False, f"CloudWatch connectivity test failed: {str(e)}"


def validate_snowflake_connectivity() -> Tuple[bool, str]:
    """
    Validate Snowflake connectivity and access.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        logger.info("Testing Snowflake connectivity...")
        
        if not settings.SNOWFLAKE_ACCOUNT:
            return True, "⚠ Snowflake not configured - skipping validation"
        
        try:
            import snowflake.connector
        except ImportError:
            return False, "✗ snowflake-connector-python not installed. Install with: pip install snowflake-connector-python"
        
        results = []
        
        # Create Snowflake connection
        try:
            conn = snowflake.connector.connect(
                account=settings.SNOWFLAKE_ACCOUNT,
                user=settings.SNOWFLAKE_USER,
                password=settings.SNOWFLAKE_PASSWORD,
                warehouse=settings.SNOWFLAKE_WAREHOUSE,
                database=settings.SNOWFLAKE_DATABASE,
                schema=settings.SNOWFLAKE_SCHEMA,
                role=settings.SNOWFLAKE_ROLE
            )
            results.append("✓ Snowflake connection established")
            logger.info("Snowflake connection established")
            
            # Test query execution
            cursor = conn.cursor()
            cursor.execute("SELECT CURRENT_VERSION()")
            version = cursor.fetchone()[0]
            results.append(f"✓ Snowflake version: {version}")
            logger.info(f"Snowflake version: {version}")
            
            # Test database access
            cursor.execute(f"USE DATABASE {settings.SNOWFLAKE_DATABASE}")
            results.append(f"✓ Database '{settings.SNOWFLAKE_DATABASE}' accessible")
            logger.info(f"Database '{settings.SNOWFLAKE_DATABASE}' accessible")
            
            # Test warehouse access
            cursor.execute(f"USE WAREHOUSE {settings.SNOWFLAKE_WAREHOUSE}")
            results.append(f"✓ Warehouse '{settings.SNOWFLAKE_WAREHOUSE}' accessible")
            logger.info(f"Warehouse '{settings.SNOWFLAKE_WAREHOUSE}' accessible")
            
            cursor.close()
            conn.close()
            
            return True, "\n".join(results)
            
        except snowflake.connector.errors.Error as e:
            results.append(f"✗ Snowflake connection error: {str(e)}")
            logger.error(f"Snowflake connection error: {str(e)}")
            return False, "\n".join(results)
        
    except Exception as e:
        logger.error(f"Snowflake connectivity test failed: {e}")
        return False, f"Snowflake connectivity test failed: {str(e)}"


def main():
    """Run all connectivity validations."""
    print("\n" + "="*80)
    print("AWS Services & Snowflake Connectivity Validation")
    print("="*80 + "\n")
    
    print(f"Execution Mode: {settings.EXECUTION_MODE}")
    print(f"AWS Region: {settings.AWS_REGION}")
    print(f"Storage Provider: {settings.STORAGE_PROVIDER}")
    print(f"CloudWatch Enabled: {settings.CLOUDWATCH_ENABLED}")
    print("\n" + "="*80 + "\n")
    
    all_success = True
    results = {}
    
    # S3 Validation
    print("1. Testing S3 Connectivity...")
    print("-" * 80)
    success, message = validate_s3_connectivity()
    print(message)
    print()
    results['S3'] = success
    all_success = all_success and success
    
    # Glue Validation
    print("2. Testing AWS Glue Connectivity...")
    print("-" * 80)
    success, message = validate_glue_connectivity()
    print(message)
    print()
    results['Glue'] = success
    all_success = all_success and success
    
    # CloudWatch Validation
    print("3. Testing CloudWatch Connectivity...")
    print("-" * 80)
    success, message = validate_cloudwatch_connectivity()
    print(message)
    print()
    results['CloudWatch'] = success
    all_success = all_success and success
    
    # Snowflake Validation
    print("4. Testing Snowflake Connectivity...")
    print("-" * 80)
    success, message = validate_snowflake_connectivity()
    print(message)
    print()
    results['Snowflake'] = success
    all_success = all_success and success
    
    # Summary
    print("="*80)
    print("Validation Summary")
    print("="*80)
    for service, success in results.items():
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{service}: {status}")
    print("="*80)
    
    if all_success:
        print("\n✓ All connectivity validations passed!")
        return 0
    else:
        print("\n✗ Some connectivity validations failed. Please check configuration.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
