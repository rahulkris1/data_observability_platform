"""Test Load Monitoring Services

Quick verification of load monitoring services integration
"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.services.load_verification_service import LoadVerificationService
from app.services.load_audit_service import LoadAuditService
from app.services.retry_validation_service import RetryValidationService


def verify_services():
    """Verify that all load monitoring services can be instantiated"""
    print("Verifying Load Monitoring Services...")
    
    db = SessionLocal()
    
    try:
        # Test service initialization
        print("✓ Testing LoadVerificationService initialization...")
        verification_service = LoadVerificationService(db)
        assert verification_service is not None
        print("  ✓ LoadVerificationService initialized successfully")
        
        print("✓ Testing LoadAuditService initialization...")
        audit_service = LoadAuditService(db)
        assert audit_service is not None
        print("  ✓ LoadAuditService initialized successfully")
        
        print("✓ Testing RetryValidationService initialization...")
        retry_service = RetryValidationService(db)
        assert retry_service is not None
        print("  ✓ RetryValidationService initialized successfully")
        
        # Test that services have required methods
        print("\n✓ Verifying service methods...")
        
        assert hasattr(verification_service, 'verify_batch_load')
        assert hasattr(verification_service, 'get_failed_records_details')
        assert hasattr(verification_service, 'verify_dataset_completeness')
        print("  ✓ LoadVerificationService has all required methods")
        
        assert hasattr(audit_service, 'log_load_start')
        assert hasattr(audit_service, 'log_load_completion')
        assert hasattr(audit_service, 'log_load_failure')
        assert hasattr(audit_service, 'get_load_history')
        assert hasattr(audit_service, 'get_load_statistics')
        print("  ✓ LoadAuditService has all required methods")
        
        assert hasattr(retry_service, 'validate_for_retry')
        assert hasattr(retry_service, 'get_retry_ready_loads')
        assert hasattr(retry_service, 'get_failed_loads_summary')
        assert hasattr(retry_service, 'revoke_retry_approval')
        print("  ✓ RetryValidationService has all required methods")
        
        print("\n✅ All services verified successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    success = verify_services()
    sys.exit(0 if success else 1)
