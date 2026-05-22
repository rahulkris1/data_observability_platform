"""Storage module for object storage operations"""

from app.storage.minio_client import minio_client, MinIOClient

__all__ = ['minio_client', 'MinIOClient']
