"""Test script to verify MinIO connection and bucket setup"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.storage.minio_client import minio_client
from app.core.config import settings


def test_minio_connection():
    """Test MinIO connection and bucket verification"""
    
    print("=" * 60)
    print("MinIO Connection Test")
    print("=" * 60)
    
    # Test 1: Check connection
    print("\n1. Testing MinIO connection...")
    print(f"   Endpoint: {settings.MINIO_ENDPOINT}")
    print(f"   Access Key: {settings.MINIO_ACCESS_KEY}")
    
    connection_ok = minio_client.check_connection()
    if connection_ok:
        print("   ✓ Connection successful!")
    else:
        print("   ✗ Connection failed!")
        return False
    
    # Test 2: Verify buckets
    print("\n2. Verifying required buckets...")
    bucket_status = minio_client.verify_buckets()
    
    all_buckets_ok = True
    for bucket_type, status in bucket_status.items():
        exists = status.get('exists', False)
        bucket_name = status.get('name', 'unknown')
        
        if exists:
            print(f"   ✓ Bucket '{bucket_name}' ({bucket_type}) exists")
        else:
            print(f"   ✗ Bucket '{bucket_name}' ({bucket_type}) not found")
            if 'error' in status:
                print(f"     Error: {status['error']}")
            all_buckets_ok = False
    
    # Test 3: Test upload/download (simple test)
    if all_buckets_ok:
        print("\n3. Testing upload/download operations...")
        test_data = b"Test data for MinIO connection verification"
        test_object_name = "test/connection_test.txt"
        
        # Upload test
        upload_ok = minio_client.upload_object(
            bucket_type='raw',
            object_name=test_object_name,
            data=test_data,
            content_type='text/plain'
        )
        
        if upload_ok:
            print(f"   ✓ Upload test successful")
            
            # Download test
            downloaded_data = minio_client.download_object(
                bucket_type='raw',
                object_name=test_object_name
            )
            
            if downloaded_data == test_data:
                print(f"   ✓ Download test successful")
                print(f"   ✓ Data integrity verified")
            else:
                print(f"   ✗ Download test failed or data mismatch")
                all_buckets_ok = False
        else:
            print(f"   ✗ Upload test failed")
            all_buckets_ok = False
    
    # Summary
    print("\n" + "=" * 60)
    if connection_ok and all_buckets_ok:
        print("✓ All tests passed! MinIO is ready to use.")
    else:
        print("✗ Some tests failed. Please check the errors above.")
    print("=" * 60)
    
    return connection_ok and all_buckets_ok


if __name__ == "__main__":
    success = test_minio_connection()
    sys.exit(0 if success else 1)
