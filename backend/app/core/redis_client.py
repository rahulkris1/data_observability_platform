"""
Redis client configuration and connection management.
Provides a singleton Redis client instance for caching operations.
"""
import redis
from typing import Optional
import logging
from .config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Singleton Redis client manager."""
    
    _instance: Optional[redis.Redis] = None
    _connection_pool: Optional[redis.ConnectionPool] = None
    
    @classmethod
    def get_client(cls) -> redis.Redis:
        """
        Get or create Redis client instance.
        
        Returns:
            redis.Redis: Redis client instance
        """
        if cls._instance is None:
            cls._initialize_client()
        return cls._instance
    
    @classmethod
    def _initialize_client(cls) -> None:
        """Initialize Redis connection pool and client."""
        try:
            # Create connection pool
            cls._connection_pool = redis.ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True,  # Automatically decode responses to strings
                max_connections=10,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            
            # Create Redis client from pool
            cls._instance = redis.Redis(connection_pool=cls._connection_pool)
            
            # Test connection
            cls._instance.ping()
            logger.info("Redis connection established successfully")
            
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            cls._instance = None
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing Redis client: {e}")
            cls._instance = None
            raise
    
    @classmethod
    def check_connection(cls) -> bool:
        """
        Check if Redis connection is healthy.
        
        Returns:
            bool: True if connection is healthy, False otherwise
        """
        try:
            client = cls.get_client()
            client.ping()
            return True
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            return False
    
    @classmethod
    def get_info(cls) -> dict:
        """
        Get Redis server information.
        
        Returns:
            dict: Redis server info
        """
        try:
            client = cls.get_client()
            info = client.info()
            return {
                "connected": True,
                "version": info.get("redis_version", "unknown"),
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "uptime_days": info.get("uptime_in_days", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get Redis info: {e}")
            return {
                "connected": False,
                "error": str(e)
            }
    
    @classmethod
    def close(cls) -> None:
        """Close Redis connection and cleanup resources."""
        if cls._instance:
            try:
                cls._instance.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
            finally:
                cls._instance = None
        
        if cls._connection_pool:
            try:
                cls._connection_pool.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting connection pool: {e}")
            finally:
                cls._connection_pool = None


def get_redis_client() -> redis.Redis:
    """
    Dependency injection function for FastAPI routes.
    
    Returns:
        redis.Redis: Redis client instance
    """
    return RedisClient.get_client()
