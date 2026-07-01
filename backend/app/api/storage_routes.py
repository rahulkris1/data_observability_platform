"""API routes for storage provider management and status"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.storage.storage_provider import (
    storage_client,
    StorageProviderFactory,
    StorageProviderType
)
from app.core.config import settings

router = APIRouter()


@router.get("/status", response_model=Dict[str, Any])
async def get_storage_provider_status():
    """
    Get the current storage provider status and configuration.
    
    Returns information about the active storage provider (MinIO or S3),
    connection status, and bucket availability.
    """
    try:
        provider_type = StorageProviderFactory.get_provider_type()
        
        # Check connection
        is_connected = storage_client.check_connection()
        
        # Verify buckets
        bucket_status = storage_client.verify_buckets() if is_connected else {}
        
        # Build response
        response = {
            "provider": provider_type.value,
            "connected": is_connected,
            "buckets": bucket_status,
        }
        
        # Add provider-specific details
        if provider_type == StorageProviderType.S3:
            response["region"] = settings.AWS_REGION
            response["endpoint"] = f"s3.{settings.AWS_REGION}.amazonaws.com"
        elif provider_type == StorageProviderType.MINIO:
            response["endpoint"] = settings.MINIO_ENDPOINT
            response["secure"] = settings.MINIO_SECURE
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get storage provider status: {str(e)}"
        )


@router.get("/info", response_model=Dict[str, Any])
async def get_storage_provider_info():
    """
    Get basic information about the configured storage provider.
    
    Returns the provider type and basic configuration without checking connection.
    """
    try:
        provider_type = StorageProviderFactory.get_provider_type()
        
        info = {
            "provider": provider_type.value,
            "available_providers": [e.value for e in StorageProviderType],
        }
        
        if provider_type == StorageProviderType.S3:
            info["config"] = {
                "region": settings.AWS_REGION,
                "buckets": {
                    "raw": settings.S3_BUCKET_RAW,
                    "processed": settings.S3_BUCKET_PROCESSED,
                    "audit": settings.S3_BUCKET_AUDIT,
                }
            }
        elif provider_type == StorageProviderType.MINIO:
            info["config"] = {
                "endpoint": settings.MINIO_ENDPOINT,
                "secure": settings.MINIO_SECURE,
                "buckets": {
                    "raw": settings.MINIO_BUCKET_RAW,
                    "processed": settings.MINIO_BUCKET_PROCESSED,
                    "audit": settings.MINIO_BUCKET_AUDIT,
                }
            }
        
        return info
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get storage provider info: {str(e)}"
        )
