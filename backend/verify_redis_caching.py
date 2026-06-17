"""
Verification script for Redis caching functionality.
Tests cache service, invalidation, and API endpoints.
"""
import sys
import asyncio
from typing import Dict, Any

# Test imports
try:
    from app.core.redis_client import RedisClient, get_redis_client
    from app.services.cache_service import CacheService, get_cache_service
    from app.services.cache_invalidation_service import CacheInvalidationService, get_cache_invalidation_service
    print("✓ All cache modules imported successfully")
except ImportError as e:
    print(f"✗ Failed to import cache modules: {e}")
    sys.exit(1)


def test_redis_connection():
    """Test Redis connection."""
    print("\n=== Testing Redis Connection ===")
    try:
        # Check connection
        is_connected = RedisClient.check_connection()
        if is_connected:
            print("✓ Redis connection successful")
        else:
            print("✗ Redis connection failed")
            return False
        
        # Get Redis info
        info = RedisClient.get_info()
        print(f"  - Redis version: {info.get('version', 'unknown')}")
        print(f"  - Used memory: {info.get('used_memory', 'unknown')}")
        print(f"  - Connected clients: {info.get('connected_clients', 0)}")
        print(f"  - Uptime: {info.get('uptime_days', 0)} days")
        
        return True
    except Exception as e:
        print(f"✗ Redis connection test failed: {e}")
        return False


def test_cache_service():
    """Test cache service operations."""
    print("\n=== Testing Cache Service ===")
    try:
        cache_service = get_cache_service()
        
        # Test set operation
        test_key = "test_key"
        test_value = {"message": "Hello, Redis!", "count": 42}
        
        success = cache_service.set(test_key, test_value, prefix="test:", ttl=300)
        if success:
            print("✓ Cache set operation successful")
        else:
            print("✗ Cache set operation failed")
            return False
        
        # Test get operation
        cached_value = cache_service.get(test_key, prefix="test:")
        if cached_value == test_value:
            print("✓ Cache get operation successful")
            print(f"  Retrieved value: {cached_value}")
        else:
            print(f"✗ Cache get operation failed. Expected {test_value}, got {cached_value}")
            return False
        
        # Test delete operation
        deleted = cache_service.delete(test_key, prefix="test:")
        if deleted:
            print("✓ Cache delete operation successful")
        else:
            print("✗ Cache delete operation failed")
            return False
        
        # Verify deletion
        deleted_value = cache_service.get(test_key, prefix="test:")
        if deleted_value is None:
            print("✓ Verified key was deleted")
        else:
            print("✗ Key still exists after deletion")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Cache service test failed: {e}")
        return False


def test_schema_contract_caching():
    """Test schema contract caching."""
    print("\n=== Testing Schema Contract Caching ===")
    try:
        cache_service = get_cache_service()
        
        # Test contract
        table_name = "test_customers"
        contract = {
            "table_name": table_name,
            "schema": {
                "customer_id": "integer",
                "name": "string",
                "email": "string"
            },
            "version": "1.0"
        }
        
        # Cache contract
        success = cache_service.set_schema_contract(table_name, contract)
        if success:
            print(f"✓ Cached schema contract for {table_name}")
        else:
            print(f"✗ Failed to cache schema contract for {table_name}")
            return False
        
        # Retrieve contract
        cached_contract = cache_service.get_schema_contract(table_name)
        if cached_contract == contract:
            print(f"✓ Retrieved schema contract for {table_name}")
        else:
            print(f"✗ Schema contract mismatch")
            return False
        
        # Get count
        count = cache_service.get_cached_contracts_count()
        print(f"  - Total cached contracts: {count}")
        
        # Clean up
        cache_service.delete_schema_contract(table_name)
        print("✓ Cleaned up test contract")
        
        return True
    except Exception as e:
        print(f"✗ Schema contract caching test failed: {e}")
        return False


def test_validation_metadata_caching():
    """Test validation metadata caching."""
    print("\n=== Testing Validation Metadata Caching ===")
    try:
        cache_service = get_cache_service()
        
        # Test metadata
        validation_id = "test_validation_001"
        metadata = {
            "validation_id": validation_id,
            "status": "completed",
            "total_records": 1000,
            "passed": 950,
            "failed": 50
        }
        
        # Cache metadata
        success = cache_service.set_validation_metadata(validation_id, metadata)
        if success:
            print(f"✓ Cached validation metadata for {validation_id}")
        else:
            print(f"✗ Failed to cache validation metadata")
            return False
        
        # Retrieve metadata
        cached_metadata = cache_service.get_validation_metadata(validation_id)
        if cached_metadata == metadata:
            print(f"✓ Retrieved validation metadata for {validation_id}")
        else:
            print(f"✗ Validation metadata mismatch")
            return False
        
        # Get count
        count = cache_service.get_cached_metadata_count()
        print(f"  - Total cached metadata: {count}")
        
        # Clean up
        cache_service.delete(validation_id, prefix=cache_service.VALIDATION_METADATA_PREFIX)
        print("✓ Cleaned up test metadata")
        
        return True
    except Exception as e:
        print(f"✗ Validation metadata caching test failed: {e}")
        return False


def test_cache_statistics():
    """Test cache statistics tracking."""
    print("\n=== Testing Cache Statistics ===")
    try:
        cache_service = get_cache_service()
        
        # Reset stats
        cache_service.reset_stats()
        print("✓ Reset cache statistics")
        
        # Perform some operations
        cache_service.set("stat_test_1", "value1", prefix="test:", ttl=60)
        cache_service.set("stat_test_2", "value2", prefix="test:", ttl=60)
        cache_service.get("stat_test_1", prefix="test:")  # Hit
        cache_service.get("stat_test_1", prefix="test:")  # Hit
        cache_service.get("nonexistent", prefix="test:")  # Miss
        cache_service.delete("stat_test_1", prefix="test:")
        
        # Get stats
        stats = cache_service.get_stats()
        print(f"  - Hits: {stats['hits']}")
        print(f"  - Misses: {stats['misses']}")
        print(f"  - Sets: {stats['sets']}")
        print(f"  - Deletes: {stats['deletes']}")
        print(f"  - Hit rate: {stats['hit_rate']}%")
        
        # Verify stats
        if stats['hits'] >= 2 and stats['misses'] >= 1 and stats['sets'] >= 2:
            print("✓ Cache statistics tracking working correctly")
        else:
            print("✗ Cache statistics not tracking correctly")
            return False
        
        # Clean up
        cache_service.delete("stat_test_2", prefix="test:")
        cache_service.reset_stats()
        
        return True
    except Exception as e:
        print(f"✗ Cache statistics test failed: {e}")
        return False


def test_cache_invalidation():
    """Test cache invalidation service."""
    print("\n=== Testing Cache Invalidation ===")
    try:
        cache_service = get_cache_service()
        invalidation_service = get_cache_invalidation_service()
        
        # Set up test data
        table_name = "test_orders"
        contract = {"table": table_name, "version": "1.0"}
        cache_service.set_schema_contract(table_name, contract)
        print(f"✓ Created test contract for {table_name}")
        
        # Test invalidation on contract update
        result = invalidation_service.invalidate_on_contract_update(
            table_name=table_name,
            updated_by="test_script",
            reason="Testing invalidation"
        )
        
        if result['invalidated']:
            print("✓ Contract invalidation successful")
        else:
            print("✗ Contract invalidation failed")
            return False
        
        # Verify contract was removed
        cached = cache_service.get_schema_contract(table_name)
        if cached is None:
            print("✓ Verified contract was invalidated")
        else:
            print("✗ Contract still exists after invalidation")
            return False
        
        # Test invalidation stats
        stats = invalidation_service.get_invalidation_stats()
        print(f"  - Current cached contracts: {stats['current_cached_contracts']}")
        print(f"  - Current cached metadata: {stats['current_cached_metadata']}")
        
        return True
    except Exception as e:
        print(f"✗ Cache invalidation test failed: {e}")
        return False


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Redis Caching Functionality Verification")
    print("=" * 60)
    
    tests = [
        ("Redis Connection", test_redis_connection),
        ("Cache Service", test_cache_service),
        ("Schema Contract Caching", test_schema_contract_caching),
        ("Validation Metadata Caching", test_validation_metadata_caching),
        ("Cache Statistics", test_cache_statistics),
        ("Cache Invalidation", test_cache_invalidation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n✗ {test_name} raised exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    # Clean up
    try:
        cache_service = get_cache_service()
        cache_service.delete_pattern("test:*")
        cache_service.reset_stats()
        print("\n✓ Cleanup completed")
    except Exception as e:
        print(f"\n✗ Cleanup failed: {e}")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
