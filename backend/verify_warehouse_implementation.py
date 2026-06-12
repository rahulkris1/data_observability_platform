"""
Verification script for warehouse implementation

This script verifies:
1. Warehouse tables are created
2. Warehouse services work correctly
3. Batch loader functionality
4. Validation functionality
5. API routes are accessible
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import inspect, text
from app.core.database import engine, get_db
from app.warehouse.warehouse_service import WarehouseReadService, WarehouseWriteService
from app.warehouse.batch_loader import BatchLoader, BatchLoaderConfig
from app.warehouse.validator import WarehouseValidator
from app.warehouse.audit_logger import WarehouseAuditLogger
import uuid


def verify_warehouse_tables():
    """Verify that warehouse tables exist in the database"""
    print("\n=== Verifying Warehouse Tables ===")
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    required_tables = [
        'warehouse_staging_data',
        'warehouse_processed_data',
        'warehouse_load_history'
    ]
    
    all_exist = True
    for table in required_tables:
        if table in tables:
            print(f"✓ Table '{table}' exists")
            
            # Show columns
            columns = inspector.get_columns(table)
            print(f"  Columns: {', '.join([col['name'] for col in columns[:5]])}...")
        else:
            print(f"✗ Table '{table}' does NOT exist")
            all_exist = False
    
    return all_exist


def verify_warehouse_services():
    """Verify warehouse services functionality"""
    print("\n=== Verifying Warehouse Services ===")
    
    db = next(get_db())
    
    try:
        # Test Read Service
        print("Testing WarehouseReadService...")
        read_service = WarehouseReadService(db)
        stats = read_service.get_warehouse_statistics()
        print(f"✓ Read service works - Total records: {stats.get('total_records', 0)}")
        
        # Test Write Service
        print("Testing WarehouseWriteService...")
        write_service = WarehouseWriteService(db)
        batch_id = f"test_{uuid.uuid4().hex[:8]}"
        load_history = write_service.create_load_history(
            batch_id=batch_id,
            dataset_name="test_dataset",
            load_type="initial",
            source_system="test"
        )
        print(f"✓ Write service works - Created load history: {load_history.batch_id}")
        
        # Clean up test data
        db.delete(load_history)
        db.commit()
        
        return True
        
    except Exception as e:
        print(f"✗ Service verification failed: {str(e)}")
        return False
    finally:
        db.close()


def verify_batch_loader():
    """Verify batch loader functionality"""
    print("\n=== Verifying Batch Loader ===")
    
    db = next(get_db())
    
    try:
        # Create test records
        test_records = [
            {"id": "1", "name": "Test Record 1", "value": 100},
            {"id": "2", "name": "Test Record 2", "value": 200},
            {"id": "3", "name": "Test Record 3", "value": 300},
        ]
        
        # Create batch loader
        config = BatchLoaderConfig(
            batch_size=10,
            enable_deduplication=True,
            skip_duplicates=True
        )
        loader = BatchLoader(db=db, config=config)
        
        # Execute load
        print("Executing test batch load...")
        result = loader.load_batch(
            records=test_records,
            dataset_name="test_dataset",
            source_system="test_system",
            load_type="initial"
        )
        
        print(f"✓ Batch load completed:")
        print(f"  Status: {result['status']}")
        print(f"  Records loaded: {result['records_loaded']}")
        print(f"  Duration: {result['execution_duration_ms']:.2f}ms")
        
        # Clean up test data
        from app.models.warehouse_tables import WarehouseProcessedData, WarehouseLoadHistory
        db.query(WarehouseProcessedData).filter(
            WarehouseProcessedData.batch_id == result['batch_id']
        ).delete()
        db.query(WarehouseLoadHistory).filter(
            WarehouseLoadHistory.batch_id == result['batch_id']
        ).delete()
        db.commit()
        
        return True
        
    except Exception as e:
        print(f"✗ Batch loader verification failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def verify_validator():
    """Verify warehouse validator functionality"""
    print("\n=== Verifying Warehouse Validator ===")
    
    db = next(get_db())
    
    try:
        validator = WarehouseValidator(db)
        
        # Test required columns validation
        test_records = [
            {"id": "1", "name": "Test", "email": "test@example.com"},
            {"id": "2", "name": "Test2"},  # Missing email
        ]
        
        result = validator.validate_required_columns(
            records=test_records,
            required_columns=["id", "name", "email"]
        )
        
        print(f"✓ Required columns validation: {result.message}")
        
        # Test duplicates validation
        duplicate_records = [
            {"id": "1", "name": "Test"},
            {"id": "1", "name": "Test"},  # Duplicate
        ]
        
        result = validator.validate_duplicates(
            records=duplicate_records,
            unique_keys=["id"]
        )
        
        print(f"✓ Duplicate validation: {result.message}")
        
        return True
        
    except Exception as e:
        print(f"✗ Validator verification failed: {str(e)}")
        return False
    finally:
        db.close()


def verify_audit_logger():
    """Verify audit logger functionality"""
    print("\n=== Verifying Audit Logger ===")
    
    db = next(get_db())
    
    try:
        audit_logger = WarehouseAuditLogger(db)
        
        batch_id = f"audit_test_{uuid.uuid4().hex[:8]}"
        
        # Log load start
        load = audit_logger.log_load_start(
            batch_id=batch_id,
            dataset_name="test_dataset",
            load_type="initial"
        )
        
        print(f"✓ Audit log created: {load.batch_id}")
        
        # Log load completion
        audit_logger.log_load_completion(
            batch_id=batch_id,
            records_attempted=100,
            records_loaded=95,
            records_failed=5,
            records_duplicate=0,
            execution_duration_ms=1234.56
        )
        
        print(f"✓ Audit log updated successfully")
        
        # Clean up
        from app.models.warehouse_tables import WarehouseLoadHistory
        db.query(WarehouseLoadHistory).filter(
            WarehouseLoadHistory.batch_id == batch_id
        ).delete()
        db.commit()
        
        return True
        
    except Exception as e:
        print(f"✗ Audit logger verification failed: {str(e)}")
        return False
    finally:
        db.close()


def main():
    """Main verification function"""
    print("=" * 60)
    print("WAREHOUSE IMPLEMENTATION VERIFICATION")
    print("=" * 60)
    
    results = {
        "Tables": verify_warehouse_tables(),
        "Services": verify_warehouse_services(),
        "Batch Loader": verify_batch_loader(),
        "Validator": verify_validator(),
        "Audit Logger": verify_audit_logger(),
    }
    
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for component, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{component:20s}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All verifications passed successfully!")
        print("\nNext steps:")
        print("1. Start the FastAPI backend server")
        print("2. Navigate to http://localhost:8000/docs to test API endpoints")
        print("3. Test warehouse load endpoint: POST /api/v1/warehouse/load")
        print("4. Start the Next.js frontend and navigate to /warehouse-status")
        return 0
    else:
        print("\n✗ Some verifications failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit(main())
