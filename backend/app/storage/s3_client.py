"""AWS S3 client and storage utilities for object storage operations"""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional, List
import io
from datetime import timedelta

from app.core.config import settings


class S3Client:
    """AWS S3 client wrapper for object storage operations"""
    
    def __init__(self):
        """Initialize S3 client with settings from config"""
        self.client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.buckets = {
            'raw': settings.S3_BUCKET_RAW,
            'processed': settings.S3_BUCKET_PROCESSED,
            'audit': settings.S3_BUCKET_AUDIT
        }
        self.region = settings.AWS_REGION
    
    def check_connection(self) -> bool:
        """
        Check if S3 connection is working
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Try to list buckets to verify connection and credentials
            self.client.list_buckets()
            return True
        except (ClientError, NoCredentialsError) as e:
            print(f"S3 connection failed: {str(e)}")
            return False
    
    def verify_buckets(self) -> dict:
        """
        Verify that all required buckets exist
        
        Returns:
            dict: Status of each bucket
        """
        bucket_status = {}
        for bucket_name, bucket_id in self.buckets.items():
            try:
                self.client.head_bucket(Bucket=bucket_id)
                bucket_status[bucket_name] = {
                    'name': bucket_id,
                    'exists': True
                }
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                bucket_status[bucket_name] = {
                    'name': bucket_id,
                    'exists': False,
                    'error': error_code
                }
        return bucket_status

    def create_bucket_if_not_exists(self, bucket_name: str) -> bool:
        """
        Create an S3 bucket if it does not already exist.
        
        Note: Bucket creation respects the configured AWS region.
        """
        try:
            # Check if bucket exists
            try:
                self.client.head_bucket(Bucket=bucket_name)
                return True  # Bucket already exists
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                if error_code != '404':
                    # Some other error occurred
                    print(f"Error checking bucket '{bucket_name}': {str(e)}")
                    return False
            
            # Create bucket
            if self.region == 'us-east-1':
                # us-east-1 doesn't require LocationConstraint
                self.client.create_bucket(Bucket=bucket_name)
            else:
                self.client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            return True
        except ClientError as e:
            print(f"Failed to create bucket '{bucket_name}': {str(e)}")
            return False

    def ensure_buckets(self) -> bool:
        """Ensure all configured buckets exist in S3."""
        for bucket_name in self.buckets.values():
            if not self.create_bucket_if_not_exists(bucket_name):
                return False
        return True
    
    def upload_object(
        self, 
        bucket_type: str, 
        object_name: str, 
        data: bytes,
        content_type: str = 'application/octet-stream'
    ) -> bool:
        """
        Upload an object to S3
        
        Args:
            bucket_type: Type of bucket ('raw', 'processed', or 'audit')
            object_name: Name of the object to create
            data: Bytes data to upload
            content_type: MIME type of the content
            
        Returns:
            bool: True if upload successful, False otherwise
        """
        try:
            bucket_name = self.buckets.get(bucket_type)
            if not bucket_name:
                raise ValueError(f"Invalid bucket type: {bucket_type}")

            if not self.create_bucket_if_not_exists(bucket_name):
                raise RuntimeError(f"Bucket '{bucket_name}' is not available")
            
            data_stream = io.BytesIO(data)
            self.client.put_object(
                Bucket=bucket_name,
                Key=object_name,
                Body=data_stream,
                ContentType=content_type
            )
            return True
        except ClientError as e:
            print(f"S3 upload failed: {str(e)}")
            return False
    
    def download_object(self, bucket_type: str, object_name: str) -> Optional[bytes]:
        """
        Download an object from S3
        
        Args:
            bucket_type: Type of bucket ('raw', 'processed', or 'audit')
            object_name: Name of the object to download
            
        Returns:
            bytes: Object data if successful, None otherwise
        """
        try:
            bucket_name = self.buckets.get(bucket_type)
            if not bucket_name:
                raise ValueError(f"Invalid bucket type: {bucket_type}")
            
            response = self.client.get_object(Bucket=bucket_name, Key=object_name)
            data = response['Body'].read()
            return data
        except ClientError as e:
            print(f"S3 download failed: {str(e)}")
            return None
    
    def list_objects(self, bucket_type: str, prefix: str = "") -> List[str]:
        """
        List objects in a bucket
        
        Args:
            bucket_type: Type of bucket ('raw', 'processed', or 'audit')
            prefix: Filter objects by prefix
            
        Returns:
            List[str]: List of object names
        """
        try:
            bucket_name = self.buckets.get(bucket_type)
            if not bucket_name:
                raise ValueError(f"Invalid bucket type: {bucket_type}")
            
            paginator = self.client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
            
            object_names = []
            for page in pages:
                if 'Contents' in page:
                    object_names.extend([obj['Key'] for obj in page['Contents']])
            
            return object_names
        except ClientError as e:
            print(f"S3 list objects failed: {str(e)}")
            return []
    
    def get_presigned_url(
        self, 
        bucket_type: str, 
        object_name: str,
        expires: timedelta = timedelta(hours=1)
    ) -> Optional[str]:
        """
        Get a presigned URL for temporary access to an object
        
        Args:
            bucket_type: Type of bucket ('raw', 'processed', or 'audit')
            object_name: Name of the object
            expires: URL expiration time
            
        Returns:
            str: Presigned URL if successful, None otherwise
        """
        try:
            bucket_name = self.buckets.get(bucket_type)
            if not bucket_name:
                raise ValueError(f"Invalid bucket type: {bucket_type}")
            
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_name},
                ExpiresIn=int(expires.total_seconds())
            )
            return url
        except ClientError as e:
            print(f"Get presigned URL failed: {str(e)}")
            return None


# Global S3 client instance
s3_client = S3Client()
