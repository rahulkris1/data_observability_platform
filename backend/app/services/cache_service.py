"""
Cache service for schema contracts and validation metadata.
Provides get/set operations with TTL and statistics tracking.
"""
import json
import logging
from typing import Any, Optional, Dict
from datetime import timedelta
from app.core.redis_client import get_redis_client
import redis

logger = logging.getLogger(__name__)


class CacheService:
    """Service for caching schema contracts and validation metadata."""
    
    # Cache key prefixes
    SCHEMA_CONTRACT_PREFIX = "schema_contract:"
    VALIDATION_METADATA_PREFIX = "validation_metadata:"
    CACHE_STATS_PREFIX = "cache_stats:"
    
    # Default TTL values (in seconds)
    DEFAULT_TTL = 3600  # 1 hour
    SCHEMA_CONTRACT_TTL = 7200  # 2 hours
    VALIDATION_METADATA_TTL = 1800  # 30 minutes
    
    def __init__(self):
        self.redis_client = get_redis_client()
        self._initialize_stats()
    
    def _initialize_stats(self) -> None:
        """Initialize cache statistics counters if they don't exist."""
        try:
            stats_key = f"{self.CACHE_STATS_PREFIX}global"
            if not self.redis_client.exists(stats_key):
                self.redis_client.hset(stats_key, mapping={
                    "hits": 0,
                    "misses": 0,
                    "sets": 0,
                    "deletes": 0
                })
        except Exception as e:
            logger.error(f"Failed to initialize cache stats: {e}")
    
    def _increment_stat(self, stat_name: str) -> None:
        """Increment a cache statistic counter."""
        try:
            stats_key = f"{self.CACHE_STATS_PREFIX}global"
            self.redis_client.hincrby(stats_key, stat_name, 1)
        except Exception as e:
            logger.error(f"Failed to increment stat {stat_name}: {e}")
    
    def get(self, key: str, prefix: str = "") -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            prefix: Optional key prefix
            
        Returns:
            Cached value or None if not found
        """
        try:
            full_key = f"{prefix}{key}"
            value = self.redis_client.get(full_key)
            
            if value is not None:
                self._increment_stat("hits")
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            else:
                self._increment_stat("misses")
                return None
                
        except redis.RedisError as e:
            logger.error(f"Redis error getting key {key}: {e}")
            self._increment_stat("misses")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting key {key}: {e}")
            self._increment_stat("misses")
            return None
    
    def set(
        self, 
        key: str, 
        value: Any, 
        prefix: str = "",
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache with optional TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            prefix: Optional key prefix
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            full_key = f"{prefix}{key}"
            
            # Serialize value to JSON if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value)
            
            # Set value with TTL if provided
            if ttl:
                self.redis_client.setex(full_key, ttl, value)
            else:
                self.redis_client.set(full_key, value)
            
            self._increment_stat("sets")
            return True
            
        except redis.RedisError as e:
            logger.error(f"Redis error setting key {key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error setting key {key}: {e}")
            return False
    
    def delete(self, key: str, prefix: str = "") -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            prefix: Optional key prefix
            
        Returns:
            True if successful, False otherwise
        """
        try:
            full_key = f"{prefix}{key}"
            deleted = self.redis_client.delete(full_key)
            
            if deleted:
                self._increment_stat("deletes")
            
            return bool(deleted)
            
        except redis.RedisError as e:
            logger.error(f"Redis error deleting key {key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.
        
        Args:
            pattern: Key pattern (e.g., "schema_contract:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                self._increment_stat("deletes")
                return deleted
            return 0
            
        except redis.RedisError as e:
            logger.error(f"Redis error deleting pattern {pattern}: {e}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error deleting pattern {pattern}: {e}")
            return 0
    
    def get_schema_contract(self, table_name: str) -> Optional[Dict]:
        """
        Get cached schema contract for a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Schema contract dictionary or None
        """
        return self.get(table_name, prefix=self.SCHEMA_CONTRACT_PREFIX)
    
    def set_schema_contract(self, table_name: str, contract: Dict) -> bool:
        """
        Cache schema contract for a table.
        
        Args:
            table_name: Name of the table
            contract: Schema contract dictionary
            
        Returns:
            True if successful
        """
        return self.set(
            table_name, 
            contract, 
            prefix=self.SCHEMA_CONTRACT_PREFIX,
            ttl=self.SCHEMA_CONTRACT_TTL
        )
    
    def delete_schema_contract(self, table_name: str) -> bool:
        """
        Delete cached schema contract for a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            True if successful
        """
        return self.delete(table_name, prefix=self.SCHEMA_CONTRACT_PREFIX)
    
    def get_validation_metadata(self, validation_id: str) -> Optional[Dict]:
        """
        Get cached validation metadata.
        
        Args:
            validation_id: Validation identifier
            
        Returns:
            Validation metadata dictionary or None
        """
        return self.get(validation_id, prefix=self.VALIDATION_METADATA_PREFIX)
    
    def set_validation_metadata(self, validation_id: str, metadata: Dict) -> bool:
        """
        Cache validation metadata.
        
        Args:
            validation_id: Validation identifier
            metadata: Validation metadata dictionary
            
        Returns:
            True if successful
        """
        return self.set(
            validation_id,
            metadata,
            prefix=self.VALIDATION_METADATA_PREFIX,
            ttl=self.VALIDATION_METADATA_TTL
        )
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            stats_key = f"{self.CACHE_STATS_PREFIX}global"
            stats = self.redis_client.hgetall(stats_key)
            
            # Convert string values to integers
            return {
                "hits": int(stats.get("hits", 0)),
                "misses": int(stats.get("misses", 0)),
                "sets": int(stats.get("sets", 0)),
                "deletes": int(stats.get("deletes", 0)),
                "hit_rate": self._calculate_hit_rate(
                    int(stats.get("hits", 0)),
                    int(stats.get("misses", 0))
                )
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {
                "hits": 0,
                "misses": 0,
                "sets": 0,
                "deletes": 0,
                "hit_rate": 0.0
            }
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage."""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)
    
    def reset_stats(self) -> bool:
        """Reset cache statistics to zero."""
        try:
            stats_key = f"{self.CACHE_STATS_PREFIX}global"
            self.redis_client.hset(stats_key, mapping={
                "hits": 0,
                "misses": 0,
                "sets": 0,
                "deletes": 0
            })
            return True
        except Exception as e:
            logger.error(f"Failed to reset cache stats: {e}")
            return False
    
    def get_cached_contracts_count(self) -> int:
        """Get count of cached schema contracts."""
        try:
            pattern = f"{self.SCHEMA_CONTRACT_PREFIX}*"
            keys = self.redis_client.keys(pattern)
            return len(keys)
        except Exception as e:
            logger.error(f"Failed to get cached contracts count: {e}")
            return 0
    
    def get_cached_metadata_count(self) -> int:
        """Get count of cached validation metadata."""
        try:
            pattern = f"{self.VALIDATION_METADATA_PREFIX}*"
            keys = self.redis_client.keys(pattern)
            return len(keys)
        except Exception as e:
            logger.error(f"Failed to get cached metadata count: {e}")
            return 0
    
    def flush_all(self) -> bool:
        """Flush all cached data (use with caution)."""
        try:
            self.redis_client.flushdb()
            self._initialize_stats()
            return True
        except Exception as e:
            logger.error(f"Failed to flush cache: {e}")
            return False


# Singleton instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """
    Get or create cache service instance.
    
    Returns:
        CacheService instance
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
