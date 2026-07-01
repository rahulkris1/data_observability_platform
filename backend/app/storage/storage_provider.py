"""Storage provider abstraction for MinIO or S3"""

from typing import Optional, List, Protocol
from datetime import timedelta
from enum import Enum

from app.core.config import settings


class StorageProviderType(str, Enum):
    """Storage provider types"""
    MINIO = "minio"
    S3 = "s3"


class StorageProvider(Protocol):
    """Protocol for storage provider interface"""
    
    def check_connection(self) -> bool:
        """Check if storage connection is working"""
        ...
    
    def verify_buckets(self) -> dict:
        """Verify that all required buckets exist"""
        ...
    
    def create_bucket_if_not_exists(self, bucket_name: str) -> bool:
        """Create a bucket if it does not already exist"""
        ...
    
    def ensure_buckets(self) -> bool:
        """Ensure all configured buckets exist"""
        ...
    
    def upload_object(
        self, 
        bucket_type: str, 
        object_name: str, 
        data: bytes,
        content_type: str = 'application/octet-stream'
    ) -> bool:
        """Upload an object to storage"""
        ...
    
    def download_object(self, bucket_type: str, object_name: str) -> Optional[bytes]:
        """Download an object from storage"""
        ...
    
    def list_objects(self, bucket_type: str, prefix: str = "") -> List[str]:
        """List objects in a bucket"""
        ...
    
    def get_presigned_url(
        self, 
        bucket_type: str, 
        object_name: str,
        expires: timedelta = timedelta(hours=1)
    ) -> Optional[str]:
        """Get a presigned URL for temporary access to an object"""
        ...


class StorageProviderFactory:
    """Factory for creating storage provider instances"""
    
    @staticmethod
    def get_provider() -> StorageProvider:
        """
        Get the configured storage provider instance
        
        Returns:
            StorageProvider: MinIO or S3 client based on configuration
        """
        provider_type = settings.STORAGE_PROVIDER.lower()
        
        if provider_type == StorageProviderType.S3:
            from app.storage.s3_client import s3_client
            return s3_client
        elif provider_type == StorageProviderType.MINIO:
            from app.storage.minio_client import minio_client
            return minio_client
        else:
            raise ValueError(
                f"Invalid storage provider: {provider_type}. "
                f"Must be one of: {', '.join([e.value for e in StorageProviderType])}"
            )
    
    @staticmethod
    def get_provider_type() -> StorageProviderType:
        """
        Get the configured storage provider type
        
        Returns:
            StorageProviderType: Current storage provider type
        """
        provider_type = settings.STORAGE_PROVIDER.lower()
        return StorageProviderType(provider_type)


# Global storage client that uses the configured provider
storage_client = StorageProviderFactory.get_provider()
