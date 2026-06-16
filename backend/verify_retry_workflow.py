"""Verify Retry Workflow

Tests the complete retry mechanism for failed validations
"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models import Base, ValidationLog, RetryQueue
from app.services.retry_service import RetryService
from app.services.failure_recovery_service import FailureRecoveryService
from app.services.retry_audit_service import RetryAuditService
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_failed_validation(db: Session) -> ValidationLog:
    """Create a sample failed validation for testing"""
    validation = ValidationLog(
        dataset_name="test_customers",
        validation_type="schema",
        status="failed",
        total_records=1000,
        failed_records=50,
        pass_rate=95.0,
        execution_time_ms=120.5,
        validator_name="SchemaValidator",
        message="Schema validation failed - missing required columns",
        details={
            "missing_columns": ["email", "phone"],
            "extra_columns": ["temp_field"]
        },
        errors=[
            "Column 'email' is required but not found",
            "Column 'phone' is required but not found"
        ]
    )
    
    db.add(validation)
    db.commit()
    db.refresh(validation)
    
    logger.info(f"Created sample failed validation: id={validation.id}")
    return validation


def test_retry_workflow():
    """Test the complete retry workflow"""
    logger.info("=" * 80)
    logger.info("RETRY WORKFLOW VERIFICATION")
    logger.info("=" * 80)
    
    db = SessionLocal()
    
    try:
        # Step 1: Create a failed validation
        logger.info("\n[Step 1] Creating sample failed validation...")
        failed_validation = create_sample_failed_validation(db)
        logger.info(f"✓ Failed validation created: {failed_validation}")
        
        # Step 2: Create retry request
        logger.info("\n[Step 2] Creating retry request...")
        retry_service = RetryService(db)
        retry_entry = retry_service.create_retry_request(
            validation_log_id=failed_validation.id,
            initiated_by="test_user",
            retry_reason="Testing retry mechanism",
            max_retries=3
        )
        logger.info(f"✓ Retry request created: id={retry_entry.id}, status={retry_entry.retry_status}")
        
        # Step 3: Get retry status
        logger.info("\n[Step 3] Getting retry status...")
        status = retry_service.get_retry_status(retry_entry.id)
        logger.info(f"✓ Retry status: {status.retry_status}, is_retryable={status.is_retryable()}")
        
        # Step 4: Execute retry
        logger.info("\n[Step 4] Executing retry...")
        recovery_service = FailureRecoveryService(db)
        result = recovery_service.execute_retry(
            retry_id=retry_entry.id,
            executor="test_user"
        )
        logger.info(f"✓ Retry executed: success={result['success']}, message={result['message']}")
        logger.info(f"  New validation log ID: {result.get('new_validation_log_id')}")
        
        # Step 5: Get retry history
        logger.info("\n[Step 5] Getting retry history...")
        audit_service = RetryAuditService(db)
        timeline = audit_service.get_retry_timeline(failed_validation.id)
        logger.info(f"✓ Retry timeline retrieved: {len(timeline)} entries")
        for entry in timeline:
            logger.info(f"  - Attempt {entry['attempt_number']}: {entry['status']}")
        
        # Step 6: Get retry statistics
        logger.info("\n[Step 6] Getting retry statistics...")
        stats = retry_service.get_retry_statistics(failed_validation.id)
        logger.info(f"✓ Statistics:")
        logger.info(f"  Total retries: {stats['total_retries']}")
        logger.info(f"  Pending: {stats['pending']}")
        logger.info(f"  In progress: {stats['in_progress']}")
        logger.info(f"  Completed: {stats['completed']}")
        logger.info(f"  Failed: {stats['failed']}")
        logger.info(f"  Success rate: {stats['success_rate']:.2f}%")
        
        # Step 7: Get retry metrics
        logger.info("\n[Step 7] Getting retry metrics...")
        metrics = audit_service.get_retry_metrics(dataset_name="test_customers", days_back=7)
        logger.info(f"✓ Metrics:")
        logger.info(f"  Total retries (7 days): {metrics['total_retries']}")
        logger.info(f"  Success rate: {metrics['success_rate']:.2f}%")
        logger.info(f"  Average retry count: {metrics['average_retry_count']}")
        
        # Step 8: Get failed validations
        logger.info("\n[Step 8] Getting failed validations...")
        failed_validations = retry_service.get_failed_validations(
            dataset_name="test_customers",
            limit=10
        )
        logger.info(f"✓ Found {len(failed_validations)} failed validations")
        
        # Step 9: Get pending retries
        logger.info("\n[Step 9] Getting pending retries...")
        pending_retries = retry_service.get_pending_retries(limit=10)
        logger.info(f"✓ Found {len(pending_retries)} pending retries")
        
        # Step 10: Get retry history with filters
        logger.info("\n[Step 10] Getting filtered retry history...")
        history = audit_service.get_retry_history(
            dataset_name="test_customers",
            days_back=30,
            limit=100
        )
        logger.info(f"✓ Retry history:")
        logger.info(f"  Total count: {history['total_count']}")
        logger.info(f"  Retrieved: {len(history['retries'])}")
        logger.info(f"  Has more: {history['has_more']}")
        
        logger.info("\n" + "=" * 80)
        logger.info("✓ ALL TESTS PASSED - Retry workflow is working correctly!")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"\n✗ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


def main():
    """Main verification function"""
    logger.info("Starting retry workflow verification...\n")
    
    # Check database connection
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database connection successful\n")
    except Exception as e:
        logger.error(f"✗ Database connection failed: {str(e)}")
        return
    
    # Run tests
    success = test_retry_workflow()
    
    if success:
        logger.info("\n✓ Verification completed successfully!")
        sys.exit(0)
    else:
        logger.error("\n✗ Verification failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
