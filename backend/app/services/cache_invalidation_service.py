"""
Cache invalidation service for schema contracts and validation metadata.
Handles clearing cache when data is updated to maintain consistency.
"""
import logging
from typing import List, Optional
from datetime import datetime
from app.services.cache_service import get_cache_service, CacheService

logger = logging.getLogger(__name__)


class CacheInvalidationService:
    """Service for managing cache invalidation on data updates."""
    
    def __init__(self, cache_service: Optional[CacheService] = None):
        self.cache_service = cache_service or get_cache_service()
    
    def invalidate_schema_contract(self, table_name: str) -> bool:
        """
        Invalidate cached schema contract for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            True if successful
        """
        try:
            success = self.cache_service.delete_schema_contract(table_name)
            if success:
                logger.info(f"Invalidated schema contract cache for table: {table_name}")
            else:
                logger.warning(f"Failed to invalidate schema contract cache for table: {table_name}")
            return success
        except Exception as e:
            logger.error(f"Error invalidating schema contract for {table_name}: {e}")
            return False
    
    def invalidate_all_schema_contracts(self) -> int:
        """
        Invalidate all cached schema contracts.
        
        Returns:
            Number of contracts invalidated
        """
        try:
            pattern = f"{self.cache_service.SCHEMA_CONTRACT_PREFIX}*"
            count = self.cache_service.delete_pattern(pattern)
            logger.info(f"Invalidated {count} schema contracts from cache")
            return count
        except Exception as e:
            logger.error(f"Error invalidating all schema contracts: {e}")
            return 0
    
    def invalidate_validation_metadata(self, validation_id: str) -> bool:
        """
        Invalidate cached validation metadata for a specific validation.
        
        Args:
            validation_id: Validation identifier
            
        Returns:
            True if successful
        """
        try:
            key = f"{validation_id}"
            success = self.cache_service.delete(
                key, 
                prefix=self.cache_service.VALIDATION_METADATA_PREFIX
            )
            if success:
                logger.info(f"Invalidated validation metadata cache for: {validation_id}")
            return success
        except Exception as e:
            logger.error(f"Error invalidating validation metadata for {validation_id}: {e}")
            return False
    
    def invalidate_all_validation_metadata(self) -> int:
        """
        Invalidate all cached validation metadata.
        
        Returns:
            Number of metadata entries invalidated
        """
        try:
            pattern = f"{self.cache_service.VALIDATION_METADATA_PREFIX}*"
            count = self.cache_service.delete_pattern(pattern)
            logger.info(f"Invalidated {count} validation metadata entries from cache")
            return count
        except Exception as e:
            logger.error(f"Error invalidating all validation metadata: {e}")
            return 0
    
    def invalidate_table_related_caches(self, table_name: str) -> dict:
        """
        Invalidate all caches related to a specific table.
        This includes schema contracts and related validation metadata.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with invalidation results
        """
        results = {
            "table_name": table_name,
            "schema_contract_invalidated": False,
            "validation_metadata_count": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Invalidate schema contract
            results["schema_contract_invalidated"] = self.invalidate_schema_contract(table_name)
            
            # Invalidate validation metadata that might be related to this table
            # This is a pattern-based cleanup for table-specific validations
            pattern = f"{self.cache_service.VALIDATION_METADATA_PREFIX}*{table_name}*"
            count = self.cache_service.delete_pattern(pattern)
            results["validation_metadata_count"] = count
            
            logger.info(f"Invalidated all caches for table {table_name}: {results}")
            
        except Exception as e:
            logger.error(f"Error invalidating table-related caches for {table_name}: {e}")
            results["error"] = str(e)
        
        return results
    
    def invalidate_on_contract_update(
        self, 
        table_name: str, 
        updated_by: str,
        reason: Optional[str] = None
    ) -> dict:
        """
        Invalidate cache when a schema contract is updated.
        
        Args:
            table_name: Name of the table
            updated_by: User or system that updated the contract
            reason: Optional reason for the update
            
        Returns:
            Dictionary with invalidation results
        """
        results = {
            "table_name": table_name,
            "updated_by": updated_by,
            "reason": reason,
            "invalidated": False,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            success = self.invalidate_schema_contract(table_name)
            results["invalidated"] = success
            
            if success:
                logger.info(
                    f"Cache invalidated on contract update - "
                    f"Table: {table_name}, Updated by: {updated_by}, Reason: {reason}"
                )
            
        except Exception as e:
            logger.error(f"Error in invalidate_on_contract_update for {table_name}: {e}")
            results["error"] = str(e)
        
        return results
    
    def invalidate_on_validation_complete(
        self, 
        validation_id: str,
        table_names: Optional[List[str]] = None
    ) -> dict:
        """
        Invalidate cache when a validation completes.
        
        Args:
            validation_id: Validation identifier
            table_names: Optional list of table names involved in validation
            
        Returns:
            Dictionary with invalidation results
        """
        results = {
            "validation_id": validation_id,
            "metadata_invalidated": False,
            "contracts_invalidated": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Invalidate the validation metadata
            results["metadata_invalidated"] = self.invalidate_validation_metadata(validation_id)
            
            # Optionally invalidate schema contracts for involved tables
            if table_names:
                for table_name in table_names:
                    if self.invalidate_schema_contract(table_name):
                        results["contracts_invalidated"] += 1
            
            logger.info(f"Cache invalidated on validation complete: {results}")
            
        except Exception as e:
            logger.error(f"Error in invalidate_on_validation_complete for {validation_id}: {e}")
            results["error"] = str(e)
        
        return results
    
    def refresh_schema_contract(self, table_name: str, new_contract: dict) -> bool:
        """
        Refresh (invalidate and set new) schema contract cache.
        
        Args:
            table_name: Name of the table
            new_contract: New schema contract to cache
            
        Returns:
            True if successful
        """
        try:
            # Invalidate old cache
            self.invalidate_schema_contract(table_name)
            
            # Set new contract
            success = self.cache_service.set_schema_contract(table_name, new_contract)
            
            if success:
                logger.info(f"Refreshed schema contract cache for table: {table_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error refreshing schema contract for {table_name}: {e}")
            return False
    
    def get_invalidation_stats(self) -> dict:
        """
        Get statistics about cache invalidations.
        
        Returns:
            Dictionary with invalidation statistics
        """
        try:
            cache_stats = self.cache_service.get_stats()
            
            return {
                "total_deletes": cache_stats.get("deletes", 0),
                "current_cached_contracts": self.cache_service.get_cached_contracts_count(),
                "current_cached_metadata": self.cache_service.get_cached_metadata_count(),
                "cache_hit_rate": cache_stats.get("hit_rate", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting invalidation stats: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Singleton instance
_invalidation_service: Optional[CacheInvalidationService] = None


def get_cache_invalidation_service() -> CacheInvalidationService:
    """
    Get or create cache invalidation service instance.
    
    Returns:
        CacheInvalidationService instance
    """
    global _invalidation_service
    if _invalidation_service is None:
        _invalidation_service = CacheInvalidationService()
    return _invalidation_service
