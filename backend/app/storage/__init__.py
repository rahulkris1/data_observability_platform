"""Storage module for object storage operations (MinIO and S3 support)"""

from app.storage.minio_client import minio_client, MinIOClient
from app.storage.s3_client import s3_client, S3Client
from app.storage.storage_provider import (
    storage_client,
    StorageProvider,
    StorageProviderType,
    StorageProviderFactory
)

__all__ = [
    'minio_client',
    'MinIOClient',
    's3_client',
    'S3Client',
    'storage_client',
    'StorageProvider',
    'StorageProviderType',
    'StorageProviderFactory'
]
