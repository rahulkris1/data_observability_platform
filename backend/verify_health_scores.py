"""
Verification script for pipeline health score system.

This script tests the health score calculation, storage, and retrieval.
"""
import sys
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine
from app.models.health_score import HealthScore
from app.models.validation_log import ValidationLog
from app.models.freshness_metrics import FreshnessMetrics
from app.services.pipeline_health_service import PipelineHealthService


def create_test_data(db: Session):
    """Create test validation and freshness data"""
    print("Creating test data...")
    
    pipeline_name = "test_customer_pipeline"
    
    # Create validation logs
    for i in range(10):
        validation = ValidationLog(
            dataset_name=pipeline_name,
            validation_timestamp=datetime.utcnow() - timedelta(hours=i),
            overall_status='passed' if i % 3 != 0 else 'failed',
            overall_passed=i % 3 != 0,
            total_validators=5,
            passed_validators=5 if i % 3 != 0 else 3,
            failed_validators=0 if i % 3 != 0 else 2,
            total_records=1000,
            total_execution_time_ms=500.0
        )
        db.add(validation)
    
    # Create freshness metrics
    for i in range(10):
        freshness = FreshnessMetrics(
            dataset_name=pipeline_name,
            ingestion_timestamp=datetime.utcnow() - timedelta(hours=i),
            dataset_age_hours=float(i),
            freshness_status='fresh' if i < 5 else 'stale',
            freshness_threshold_hours=6.0,
            ingestion_latency_seconds=120.0 + (i * 10),
            validation_latency_seconds=60.0 + (i * 5),
            sla_status='met' if i < 7 else 'violated',
            sla_threshold_hours=8.0
        )
        db.add(freshness)
    
    db.commit()
    print("✓ Test data created")


def test_health_score_calculation():
    """Test health score calculation"""
    print("\n=== Testing Health Score Calculation ===")
    
    db = SessionLocal()
    
    try:
        # Create test data
        create_test_data(db)
        
        # Initialize service
        service = PipelineHealthService(db)
        pipeline_name = "test_customer_pipeline"
        
        # Test validation score calculation
        print("\n1. Testing validation score...")
        validation_metrics = service.calculate_validation_score(pipeline_name)
        print(f"   Validation score: {validation_metrics['score']:.2f}")
        print(f"   Pass rate: {validation_metrics['pass_rate']:.2f}%")
        print(f"   Total validations: {validation_metrics['total_validations']}")
        print(f"   Passed: {validation_metrics['passed_validations']}")
        print(f"   Failed: {validation_metrics['failed_validations']}")
        assert validation_metrics['score'] >= 0 and validation_metrics['score'] <= 100
        print("   ✓ Validation score calculation passed")
        
        # Test freshness score calculation
        print("\n2. Testing freshness score...")
        freshness_metrics = service.calculate_freshness_score(pipeline_name)
        print(f"   Freshness score: {freshness_metrics['score']:.2f}")
        print(f"   Total checks: {freshness_metrics['total_checks']}")
        print(f"   Fresh count: {freshness_metrics['fresh_count']}")
        print(f"   Violations: {freshness_metrics['violations']}")
        assert freshness_metrics['score'] >= 0 and freshness_metrics['score'] <= 100
        print("   ✓ Freshness score calculation passed")
        
        # Test latency score calculation
        print("\n3. Testing latency score...")
        latency_metrics = service.calculate_latency_score(pipeline_name)
        print(f"   Latency score: {latency_metrics['score']:.2f}")
        print(f"   Avg latency: {latency_metrics['avg_latency_seconds']:.2f}s")
        print(f"   Avg ingestion: {latency_metrics['avg_ingestion_seconds']:.2f}s")
        print(f"   Avg validation: {latency_metrics['avg_validation_seconds']:.2f}s")
        assert latency_metrics['score'] >= 0 and latency_metrics['score'] <= 100
        print("   ✓ Latency score calculation passed")
        
        # Test overall health calculation
        print("\n4. Testing overall health score calculation...")
        health_score = service.calculate_pipeline_health(pipeline_name)
        
        print(f"   Pipeline: {health_score.pipeline_name}")
        print(f"   Overall score: {health_score.overall_score:.2f}")
        print(f"   Validation score: {health_score.validation_score:.2f}")
        print(f"   Freshness score: {health_score.freshness_score:.2f}")
        print(f"   Latency score: {health_score.latency_score:.2f}")
        print(f"   Status: {health_score.status}")
        print(f"   Timestamp: {health_score.timestamp}")
        
        assert health_score.overall_score >= 0 and health_score.overall_score <= 100
        assert health_score.status in ['healthy', 'degraded', 'unhealthy']
        assert health_score.id is not None
        print("   ✓ Overall health score calculation passed")
        
        # Test retrieval
        print("\n5. Testing health score retrieval...")
        latest = service.get_latest_health_score(pipeline_name)
        assert latest is not None
        assert latest.id == health_score.id
        print(f"   Retrieved latest score: {latest.overall_score:.2f}")
        print("   ✓ Health score retrieval passed")
        
        # Create a few more scores for history test
        for i in range(3):
            service.calculate_pipeline_health(pipeline_name)
        
        # Test history retrieval
        print("\n6. Testing health score history...")
        history = service.get_health_score_history(pipeline_name, lookback_hours=24)
        print(f"   History records: {len(history)}")
        assert len(history) >= 4  # Should have at least 4 records
        print("   ✓ Health score history retrieval passed")
        
        # Test all pipelines retrieval
        print("\n7. Testing all pipelines health scores...")
        all_scores = service.get_all_pipeline_health(limit=100)
        print(f"   Total pipelines: {len(all_scores)}")
        assert len(all_scores) >= 1
        print("   ✓ All pipelines retrieval passed")
        
        print("\n" + "=" * 50)
        print("✓ All health score tests passed successfully!")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup test data
        print("\nCleaning up test data...")
        db.query(HealthScore).filter(HealthScore.pipeline_name == "test_customer_pipeline").delete()
        db.query(ValidationLog).filter(ValidationLog.dataset_name == "test_customer_pipeline").delete()
        db.query(FreshnessMetrics).filter(FreshnessMetrics.dataset_name == "test_customer_pipeline").delete()
        db.commit()
        db.close()
        print("✓ Cleanup complete")


def test_score_thresholds():
    """Test score threshold logic"""
    print("\n=== Testing Score Thresholds ===")
    
    db = SessionLocal()
    service = PipelineHealthService(db)
    
    try:
        # Test healthy threshold
        status = service.determine_status(85.0)
        assert status == 'healthy'
        print(f"✓ Score 85.0 -> {status}")
        
        # Test degraded threshold
        status = service.determine_status(70.0)
        assert status == 'degraded'
        print(f"✓ Score 70.0 -> {status}")
        
        # Test unhealthy threshold
        status = service.determine_status(50.0)
        assert status == 'unhealthy'
        print(f"✓ Score 50.0 -> {status}")
        
        # Test overall score calculation
        overall = service.calculate_overall_score(80.0, 70.0, 90.0)
        expected = (80.0 * 0.4) + (70.0 * 0.3) + (90.0 * 0.3)
        assert abs(overall - expected) < 0.01
        print(f"✓ Overall score calculation: {overall:.2f}")
        
        print("\n✓ All threshold tests passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Threshold test failed: {str(e)}")
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("Health Score System Verification")
    print("=" * 50)
    
    # Run tests
    test1_passed = test_health_score_calculation()
    test2_passed = test_score_thresholds()
    
    # Summary
    print("\n" + "=" * 50)
    print("VERIFICATION SUMMARY")
    print("=" * 50)
    print(f"Health Score Calculation: {'PASSED ✓' if test1_passed else 'FAILED ✗'}")
    print(f"Score Thresholds:         {'PASSED ✓' if test2_passed else 'FAILED ✗'}")
    print("=" * 50)
    
    # Exit with appropriate code
    if test1_passed and test2_passed:
        print("\n🎉 All verification tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some verification tests failed!")
        sys.exit(1)
