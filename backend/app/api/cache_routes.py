"""
Cache monitoring API routes.
Provides endpoints for monitoring Redis cache health and performance.
"""
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.redis_client import RedisClient
from app.services.cache_service import get_cache_service
from app.services.cache_invalidation_service import get_cache_invalidation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cache", tags=["Cache Monitoring"])


class CacheStatusResponse(BaseModel):
    """Cache status response model."""
    connected: bool
    redis_version: str = "unknown"
    used_memory: str = "unknown"
    connected_clients: int = 0
    uptime_days: int = 0
    error: str = None


class CacheStatsResponse(BaseModel):
    """Cache statistics response model."""
    hits: int
    misses: int
    sets: int
    deletes: int
    hit_rate: float
    cached_contracts: int
    cached_metadata: int


class CacheRefreshResponse(BaseModel):
    """Cache refresh response model."""
    message: str
    invalidated_contracts: int
    invalidated_metadata: int
    stats_reset: bool


@router.get("/status", response_model=CacheStatusResponse)
async def get_cache_status():
    """
    Get Redis cache connection status and server information.
    
    Returns:
        CacheStatusResponse with connection status and server info
    """
    try:
        info = RedisClient.get_info()
        
        if info.get("connected"):
            return CacheStatusResponse(
                connected=True,
                redis_version=info.get("version", "unknown"),
                used_memory=info.get("used_memory", "unknown"),
                connected_clients=info.get("connected_clients", 0),
                uptime_days=info.get("uptime_in_days", 0)
            )
        else:
            return CacheStatusResponse(
                connected=False,
                error=info.get("error", "Unknown error")
            )
    
    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        return CacheStatusResponse(
            connected=False,
            error=str(e)
        )


@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    """
    Get cache performance statistics.
    
    Returns:
        CacheStatsResponse with cache performance metrics
    """
    try:
        cache_service = get_cache_service()
        stats = cache_service.get_stats()
        
        return CacheStatsResponse(
            hits=stats.get("hits", 0),
            misses=stats.get("misses", 0),
            sets=stats.get("sets", 0),
            deletes=stats.get("deletes", 0),
            hit_rate=stats.get("hit_rate", 0.0),
            cached_contracts=cache_service.get_cached_contracts_count(),
            cached_metadata=cache_service.get_cached_metadata_count()
        )
    
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache statistics: {str(e)}"
        )


@router.post("/refresh", response_model=CacheRefreshResponse)
async def refresh_cache():
    """
    Refresh cache by invalidating all cached data and resetting statistics.
    
    Returns:
        CacheRefreshResponse with refresh results
    """
    try:
        invalidation_service = get_cache_invalidation_service()
        cache_service = get_cache_service()
        
        # Invalidate all contracts and metadata
        contracts_invalidated = invalidation_service.invalidate_all_schema_contracts()
        metadata_invalidated = invalidation_service.invalidate_all_validation_metadata()
        
        # Reset statistics
        stats_reset = cache_service.reset_stats()
        
        logger.info(
            f"Cache refreshed - Contracts: {contracts_invalidated}, "
            f"Metadata: {metadata_invalidated}, Stats reset: {stats_reset}"
        )
        
        return CacheRefreshResponse(
            message="Cache refreshed successfully",
            invalidated_contracts=contracts_invalidated,
            invalidated_metadata=metadata_invalidated,
            stats_reset=stats_reset
        )
    
    except Exception as e:
        logger.error(f"Error refreshing cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh cache: {str(e)}"
        )


@router.delete("/invalidate/{table_name}")
async def invalidate_table_cache(table_name: str):
    """
    Invalidate cache for a specific table.
    
    Args:
        table_name: Name of the table to invalidate
        
    Returns:
        Invalidation result details
    """
    try:
        invalidation_service = get_cache_invalidation_service()
        result = invalidation_service.invalidate_table_related_caches(table_name)
        
        logger.info(f"Cache invalidated for table {table_name}: {result}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error invalidating cache for table {table_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invalidate cache: {str(e)}"
        )


@router.get("/health")
async def cache_health_check():
    """
    Simple health check endpoint for cache connectivity.
    
    Returns:
        Health status
    """
    try:
        is_healthy = RedisClient.check_connection()
        
        if is_healthy:
            return {
                "status": "healthy",
                "message": "Cache connection is active"
            }
        else:
            return {
                "status": "unhealthy",
                "message": "Cache connection failed"
            }
    
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": str(e)
        }


@router.get("/metrics")
async def get_cache_metrics() -> Dict[str, Any]:
    """
    Get comprehensive cache metrics for monitoring.
    
    Returns:
        Dictionary with comprehensive cache metrics
    """
    try:
        cache_service = get_cache_service()
        invalidation_service = get_cache_invalidation_service()
        
        # Get cache stats
        stats = cache_service.get_stats()
        
        # Get invalidation stats
        invalidation_stats = invalidation_service.get_invalidation_stats()
        
        # Get Redis info
        redis_info = RedisClient.get_info()
        
        return {
            "cache_performance": {
                "hits": stats.get("hits", 0),
                "misses": stats.get("misses", 0),
                "hit_rate": stats.get("hit_rate", 0.0),
                "total_requests": stats.get("hits", 0) + stats.get("misses", 0)
            },
            "cache_operations": {
                "sets": stats.get("sets", 0),
                "deletes": stats.get("deletes", 0)
            },
            "cached_items": {
                "contracts": cache_service.get_cached_contracts_count(),
                "metadata": cache_service.get_cached_metadata_count(),
                "total": cache_service.get_cached_contracts_count() + cache_service.get_cached_metadata_count()
            },
            "redis_server": {
                "connected": redis_info.get("connected", False),
                "version": redis_info.get("version", "unknown"),
                "used_memory": redis_info.get("used_memory", "unknown"),
                "connected_clients": redis_info.get("connected_clients", 0),
                "uptime_days": redis_info.get("uptime_in_days", 0)
            },
            "invalidation_stats": invalidation_stats
        }
    
    except Exception as e:
        logger.error(f"Error getting cache metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache metrics: {str(e)}"
        )
