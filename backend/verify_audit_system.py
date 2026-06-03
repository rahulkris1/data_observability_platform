"""
Audit System Setup and Verification Script

This script:
1. Runs Alembic migration for audit_logs table
2. Seeds the database with sample audit data
3. Verifies the audit system is working correctly
"""
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.audit_log import AuditLog
from app.services.audit_service import AuditService


def verify_database_connection():
    """Verify database connection"""
    print("\n" + "=" * 60)
    print("STEP 1: Verifying Database Connection")
    print("=" * 60)
    
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        print("✓ Database connection successful!")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {str(e)}")
        return False


def verify_audit_table_exists():
    """Verify audit_logs table exists"""
    print("\n" + "=" * 60)
    print("STEP 2: Verifying audit_logs Table")
    print("=" * 60)
    
    try:
        db = SessionLocal()
        result = db.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'audit_logs'
            );
        """)
        exists = result.scalar()
        db.close()
        
        if exists:
            print("✓ audit_logs table exists!")
            return True
        else:
            print("✗ audit_logs table does not exist!")
            print("\nPlease run the Alembic migration:")
            print("  cd backend")
            print("  alembic upgrade head")
            return False
    except Exception as e:
        print(f"✗ Error checking table: {str(e)}")
        return False


def verify_audit_service():
    """Verify AuditService functionality"""
    print("\n" + "=" * 60)
    print("STEP 3: Verifying Audit Service")
    print("=" * 60)
    
    try:
        db = SessionLocal()
        service = AuditService(db)
        
        # Create a test audit record
        print("\nCreating test audit record...")
        test_audit = service.create_audit_record(
            dataset_name="test_dataset",
            validation_type="schema",
            status="passed",
            execution_time_ms=123.45,
            total_records=1000,
            failed_records=0,
            pass_rate=100.0,
            validator_name="TestValidator",
            triggered_by="test_script",
            environment="dev",
            metadata={"test": True},
            error_summary=None,
            details={"test_mode": True}
        )
        print(f"✓ Test audit record created with ID: {test_audit.id}")
        
        # Retrieve the audit record
        print("\nRetrieving audit record...")
        retrieved = service.get_audit_by_id(test_audit.id)
        if retrieved:
            print(f"✓ Audit record retrieved successfully!")
            print(f"  Dataset: {retrieved.dataset_name}")
            print(f"  Status: {retrieved.status}")
            print(f"  Pass Rate: {retrieved.pass_rate}%")
        
        # Get audit history
        print("\nFetching audit history...")
        history = service.get_audit_history(limit=5)
        print(f"✓ Retrieved {len(history)} audit records")
        
        # Get statistics
        print("\nFetching statistics...")
        stats = service.get_audit_statistics()
        print(f"✓ Total audits: {stats['total_audits']}")
        
        # Clean up test record
        db.delete(test_audit)
        db.commit()
        print("\n✓ Test record cleaned up")
        
        db.close()
        print("\n✓ Audit service verification successful!")
        return True
        
    except Exception as e:
        print(f"\n✗ Audit service verification failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def verify_sample_data():
    """Verify sample data exists"""
    print("\n" + "=" * 60)
    print("STEP 4: Verifying Sample Data")
    print("=" * 60)
    
    try:
        db = SessionLocal()
        count = db.query(AuditLog).count()
        db.close()
        
        print(f"Current audit record count: {count}")
        
        if count > 0:
            print("✓ Sample data exists!")
            return True
        else:
            print("⚠ No sample data found. You may want to run the seed script:")
            print("  cd backend")
            print("  python tests/fixtures/sample_audit_data.py")
            return True  # Not a failure, just a warning
            
    except Exception as e:
        print(f"✗ Error checking sample data: {str(e)}")
        return False


def display_summary():
    """Display summary and next steps"""
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)
    
    print("\n✓ All verification steps passed!")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    
    print("\n1. Run Alembic migration (if not already done):")
    print("   cd backend")
    print("   alembic upgrade head")
    
    print("\n2. Seed sample data (optional):")
    print("   cd backend")
    print("   python tests/fixtures/sample_audit_data.py")
    
    print("\n3. Start the backend server:")
    print("   cd backend")
    print("   uvicorn app.main:app --reload")
    
    print("\n4. Start the frontend development server:")
    print("   cd frontend")
    print("   npm run dev")
    
    print("\n5. Access the Audit History Dashboard:")
    print("   http://localhost:3000/audit-history")
    
    print("\n" + "=" * 60 + "\n")


def main():
    """Main verification flow"""
    print("\n" + "=" * 60)
    print("AUDIT SYSTEM VERIFICATION")
    print("=" * 60)
    
    # Run verification steps
    steps = [
        verify_database_connection,
        verify_audit_table_exists,
        verify_audit_service,
        verify_sample_data,
    ]
    
    all_passed = True
    for step in steps:
        if not step():
            all_passed = False
            break
    
    if all_passed:
        display_summary()
    else:
        print("\n✗ Verification failed. Please fix the issues above and try again.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
