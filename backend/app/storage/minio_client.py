"""MinIO client and storage utilities for object storage operations"""

from minio import Minio
from minio.error import S3Error
from typing import Optional, List
import io
from datetime import timedelta

from app.core.config import settings


class MinIOClient:
    """MinIO client wrapper for object storage operations"""
    
    def __init__(self):
        """Initialize MinIO client with settings from config"""
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.buckets = {
            'raw': settings.MINIO_BUCKET_RAW,
            'processed': settings.MINIO_BUCKET_PROCESSED,
            'audit': settings.MINIO_BUCKET_AUDIT
        }
    
    def check_connection(self) -> bool:
        """
        Check if MinIO connection is working
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Try to list buckets to verify connection
            buckets = self.client.list_buckets()
            return True
        except Exception as e:
            print(f"MinIO connection failed: {str(e)}")
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
                exists = self.client.bucket_exists(bucket_id)
                bucket_status[bucket_name] = {
                    'name': bucket_id,
                    'exists': exists
                }
            except S3Error as e:
                bucket_status[bucket_name] = {
                    'name': bucket_id,
                    'exists': False,
                    'error': str(e)
                }
        return bucket_status

    def create_bucket_if_not_exists(self, bucket_name: str) -> bool:
        """Create a MinIO bucket if it does not already exist."""
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
            return True
        except Exception as e:
            print(f"Failed to create or verify bucket '{bucket_name}': {str(e)}")
            return False

    def ensure_buckets(self) -> bool:
        """Ensure all configured buckets exist in MinIO."""
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
        Upload an object to MinIO
        
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
                bucket_name=bucket_name,
                object_name=object_name,
                data=data_stream,
                length=len(data),
                content_type=content_type
            )
            return True
        except Exception as e:
            print(f"Upload failed: {str(e)}")
            return False
    
    def download_object(self, bucket_type: str, object_name: str) -> Optional[bytes]:
        """
        Download an object from MinIO
        
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
            
            response = self.client.get_object(bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except Exception as e:
            print(f"Download failed: {str(e)}")
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
            
            objects = self.client.list_objects(bucket_name, prefix=prefix)
            return [obj.object_name for obj in objects]
        except Exception as e:
            print(f"List objects failed: {str(e)}")
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
            
            url = self.client.presigned_get_object(
                bucket_name=bucket_name,
                object_name=object_name,
                expires=expires
            )
            return url
        except Exception as e:
            print(f"Get presigned URL failed: {str(e)}")
            return None


# Global MinIO client instance
minio_client = MinIOClient()
