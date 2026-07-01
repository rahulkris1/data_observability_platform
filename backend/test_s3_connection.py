"""Test script to verify AWS S3 connection and bucket setup"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.storage.s3_client import s3_client


def test_s3_connection():
    """Test S3 connection and bucket operations"""
    print("=" * 60)
    print("AWS S3 Connection Test")
    print("=" * 60)
    
    # Check configuration
    print("\n1. Configuration:")
    print(f"   - AWS Region: {settings.AWS_REGION}")
    print(f"   - Raw Bucket: {settings.S3_BUCKET_RAW}")
    print(f"   - Processed Bucket: {settings.S3_BUCKET_PROCESSED}")
    print(f"   - Audit Bucket: {settings.S3_BUCKET_AUDIT}")
    
    # Validate credentials
    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        print("\n❌ ERROR: AWS credentials not configured")
        print("   Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in your .env file")
        return False
    
    print(f"   - Access Key ID: {settings.AWS_ACCESS_KEY_ID[:8]}...")
    
    # Test connection
    print("\n2. Testing S3 Connection:")
    try:
        is_connected = s3_client.check_connection()
        if is_connected:
            print("   ✓ S3 connection successful")
        else:
            print("   ❌ S3 connection failed")
            return False
    except Exception as e:
        print(f"   ❌ Connection error: {str(e)}")
        return False
    
    # Verify buckets
    print("\n3. Verifying S3 Buckets:")
    bucket_status = s3_client.verify_buckets()
    all_exist = True
    
    for bucket_type, status in bucket_status.items():
        bucket_name = status['name']
        exists = status.get('exists', False)
        
        if exists:
            print(f"   ✓ {bucket_type.upper()} bucket '{bucket_name}' exists")
        else:
            error = status.get('error', 'Unknown error')
            print(f"   ✗ {bucket_type.upper()} bucket '{bucket_name}' does not exist (Error: {error})")
            all_exist = False
    
    # Create buckets if needed
    if not all_exist:
        print("\n4. Creating Missing Buckets:")
        try:
            success = s3_client.ensure_buckets()
            if success:
                print("   ✓ All buckets created successfully")
            else:
                print("   ❌ Failed to create some buckets")
                return False
        except Exception as e:
            print(f"   ❌ Error creating buckets: {str(e)}")
            return False
    
    # Test upload/download
    print("\n5. Testing Upload/Download:")
    test_data = b"Test data for S3 upload/download verification"
    test_object_name = "test/verification_test.txt"
    
    try:
        # Upload test
        print(f"   - Uploading test object to raw bucket...")
        upload_success = s3_client.upload_object(
            bucket_type="raw",
            object_name=test_object_name,
            data=test_data,
            content_type="text/plain"
        )
        
        if upload_success:
            print("     ✓ Upload successful")
        else:
            print("     ❌ Upload failed")
            return False
        
        # Download test
        print(f"   - Downloading test object from raw bucket...")
        downloaded_data = s3_client.download_object("raw", test_object_name)
        
        if downloaded_data == test_data:
            print("     ✓ Download successful and data matches")
        else:
            print("     ❌ Download failed or data mismatch")
            return False
        
        # List objects test
        print(f"   - Listing objects in raw bucket...")
        objects = s3_client.list_objects("raw", prefix="test/")
        
        if test_object_name in objects:
            print(f"     ✓ List successful, found {len(objects)} object(s)")
        else:
            print("     ❌ List failed or test object not found")
            return False
        
        # Get presigned URL test
        print(f"   - Generating presigned URL...")
        presigned_url = s3_client.get_presigned_url("raw", test_object_name)
        
        if presigned_url:
            print(f"     ✓ Presigned URL generated")
            print(f"       URL: {presigned_url[:80]}...")
        else:
            print("     ❌ Presigned URL generation failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Error during upload/download test: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ All S3 tests passed successfully!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    print("\nStarting S3 connection test...")
    print(f"Storage Provider: {settings.STORAGE_PROVIDER}")
    
    if settings.STORAGE_PROVIDER.lower() != "s3":
        print("\n⚠️  WARNING: STORAGE_PROVIDER is not set to 's3'")
        print("   Current value:", settings.STORAGE_PROVIDER)
        print("   To test S3, set STORAGE_PROVIDER=s3 in your .env file")
        sys.exit(1)
    
    success = test_s3_connection()
    sys.exit(0 if success else 1)
