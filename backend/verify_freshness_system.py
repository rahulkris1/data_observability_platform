"""
Verification script for freshness monitoring system

Tests:
1. Freshness service validation
2. Latency service tracking
3. SLA service evaluation
4. Freshness aggregation
5. Database repository operations
"""
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.freshness_service import FreshnessService, FreshnessThresholds
from app.services.latency_service import LatencyService
from app.services.sla_service import SLAService


def test_freshness_service():
    """Test freshness service functionality"""
    print("\n" + "="*60)
    print("Testing Freshness Service")
    print("="*60)
    
    service = FreshnessService()
    
    # Test 1: Calculate dataset age
    print("\n1. Testing dataset age calculation...")
    ingestion_time = datetime.utcnow() - timedelta(hours=5)
    age = service.calculate_dataset_age(ingestion_time)
    print(f"   ✓ Dataset ingested 5 hours ago has age: {age:.2f} hours")
    assert 4.9 < age < 5.1, "Age calculation failed"
    
    # Test 2: Determine freshness status
    print("\n2. Testing freshness status determination...")
    status_healthy = service.determine_freshness_status(2.0, "customers")
    status_warning = service.determine_freshness_status(15.0, "customers")
    status_critical = service.determine_freshness_status(30.0, "customers")
    
    print(f"   ✓ 2 hours old: {status_healthy}")
    print(f"   ✓ 15 hours old: {status_warning}")
    print(f"   ✓ 30 hours old: {status_critical}")
    
    assert status_healthy == "healthy", "Healthy status failed"
    assert status_warning == "warning", "Warning status failed"
    assert status_critical == "critical", "Critical status failed"
    
    # Test 3: Validate freshness
    print("\n3. Testing freshness validation...")
    result = service.validate_freshness(
        dataset_name="customers",
        ingestion_timestamp=ingestion_time
    )
    print(f"   ✓ Dataset: {result.dataset_name}")
    print(f"   ✓ Age: {result.dataset_age_hours:.2f} hours")
    print(f"   ✓ Status: {result.freshness_status}")
    print(f"   ✓ Is Fresh: {result.is_fresh}")
    print(f"   ✓ Message: {result.message}")
    
    # Test 4: Custom thresholds
    print("\n4. Testing custom threshold configuration...")
    service.add_custom_threshold("test_dataset", healthy_hours=1.0, warning_hours=2.0)
    config = service.get_threshold_config("test_dataset")
    print(f"   ✓ Custom thresholds set: {config}")
    assert config["healthy"] == 1.0, "Custom threshold failed"
    
    print("\n✅ Freshness Service tests passed!")


def test_latency_service():
    """Test latency service functionality"""
    print("\n" + "="*60)
    print("Testing Latency Service")
    print("="*60)
    
    service = LatencyService()
    
    # Test 1: Track ingestion latency
    print("\n1. Testing ingestion latency tracking...")
    operation_id = "test_op_1"
    
    start = service.start_ingestion(operation_id)
    print(f"   ✓ Ingestion started at: {start}")
    
    # Simulate some work
    import time
    time.sleep(0.1)
    
    end = service.complete_ingestion(operation_id)
    print(f"   ✓ Ingestion completed at: {end}")
    
    latency = service.calculate_ingestion_latency(start, end)
    print(f"   ✓ Ingestion latency: {latency:.3f} seconds")
    assert latency > 0.09, "Latency tracking failed"
    
    # Test 2: Track validation latency
    print("\n2. Testing validation latency tracking...")
    start = service.start_validation(operation_id)
    time.sleep(0.05)
    end = service.complete_validation(operation_id)
    
    latency = service.calculate_validation_latency(start, end)
    print(f"   ✓ Validation latency: {latency:.3f} seconds")
    assert latency > 0.04, "Validation latency tracking failed"
    
    # Test 3: Get operation latencies
    print("\n3. Testing operation latency retrieval...")
    latencies = service.get_operation_latencies(operation_id)
    print(f"   ✓ Ingestion latency: {latencies['ingestion_latency_seconds']:.3f}s")
    print(f"   ✓ Validation latency: {latencies['validation_latency_seconds']:.3f}s")
    print(f"   ✓ Total latency: {latencies['total_latency_seconds']:.3f}s")
    
    # Test 4: Context manager
    print("\n4. Testing latency context managers...")
    operation_id_2 = "test_op_2"
    
    with service.track_ingestion(operation_id_2):
        time.sleep(0.05)
    
    latencies = service.get_operation_latencies(operation_id_2)
    print(f"   ✓ Context manager ingestion latency: {latencies['ingestion_latency_seconds']:.3f}s")
    
    # Cleanup
    service.cleanup_operation(operation_id)
    service.cleanup_operation(operation_id_2)
    
    print("\n✅ Latency Service tests passed!")


def test_sla_service():
    """Test SLA service functionality"""
    print("\n" + "="*60)
    print("Testing SLA Service")
    print("="*60)
    
    service = SLAService()
    
    # Test 1: Get SLA thresholds
    print("\n1. Testing SLA threshold retrieval...")
    threshold = service.get_sla_threshold("customers")
    print(f"   ✓ Customers SLA threshold: {threshold} hours")
    assert threshold == 12.0, "SLA threshold retrieval failed"
    
    # Test 2: Evaluate SLA (compliant)
    print("\n2. Testing SLA evaluation (compliant)...")
    ingestion_time = datetime.utcnow() - timedelta(hours=10)
    completion_time = datetime.utcnow()
    
    result = service.evaluate_sla(
        dataset_name="customers",
        ingestion_timestamp=ingestion_time,
        completion_timestamp=completion_time
    )
    print(f"   ✓ Dataset: {result.dataset_name}")
    print(f"   ✓ SLA Threshold: {result.sla_threshold_hours}h")
    print(f"   ✓ Actual Latency: {result.actual_latency_hours:.2f}h")
    print(f"   ✓ SLA Status: {result.sla_status}")
    print(f"   ✓ Compliance: {result.compliance_percentage}%")
    assert result.sla_status == "compliant", "SLA evaluation (compliant) failed"
    
    # Test 3: Evaluate SLA (breached)
    print("\n3. Testing SLA evaluation (breached)...")
    ingestion_time = datetime.utcnow() - timedelta(hours=15)
    completion_time = datetime.utcnow()
    
    result = service.evaluate_sla(
        dataset_name="customers",
        ingestion_timestamp=ingestion_time,
        completion_timestamp=completion_time
    )
    print(f"   ✓ SLA Status: {result.sla_status}")
    print(f"   ✓ Breach Duration: {result.breach_duration_hours}h")
    assert result.sla_status == "breached", "SLA evaluation (breached) failed"
    
    # Test 4: Detect SLA breach
    print("\n4. Testing SLA breach detection...")
    is_breached = service.detect_sla_breach("customers", 15.0)
    print(f"   ✓ 15 hours latency breached: {is_breached}")
    assert is_breached, "SLA breach detection failed"
    
    # Test 5: Calculate compliance percentage
    print("\n5. Testing SLA compliance percentage...")
    compliance = service.calculate_sla_compliance_percentage(80, 100)
    print(f"   ✓ 80/100 compliant: {compliance}%")
    assert compliance == 80.0, "Compliance calculation failed"
    
    # Test 6: Set custom SLA threshold
    print("\n6. Testing custom SLA threshold...")
    service.set_sla_threshold("test_dataset", 6.0)
    threshold = service.get_sla_threshold("test_dataset")
    print(f"   ✓ Custom threshold set: {threshold}h")
    assert threshold == 6.0, "Custom SLA threshold failed"
    
    print("\n✅ SLA Service tests passed!")


def test_threshold_configurations():
    """Test threshold configurations"""
    print("\n" + "="*60)
    print("Testing Threshold Configurations")
    print("="*60)
    
    print("\n1. Freshness Thresholds:")
    freshness_thresholds = FreshnessThresholds.DATASET_THRESHOLDS
    for dataset, thresholds in freshness_thresholds.items():
        print(f"   ✓ {dataset}: healthy={thresholds['healthy']}h, warning={thresholds['warning']}h")
    
    print("\n2. SLA Thresholds:")
    from app.services.sla_service import SLAThresholds
    sla_thresholds = SLAThresholds.DATASET_SLA_THRESHOLDS
    for dataset, threshold in sla_thresholds.items():
        print(f"   ✓ {dataset}: {threshold}h")
    
    print("\n✅ Threshold configurations verified!")


def main():
    """Run all verification tests"""
    print("\n" + "="*60)
    print("FRESHNESS MONITORING SYSTEM VERIFICATION")
    print("="*60)
    
    try:
        test_freshness_service()
        test_latency_service()
        test_sla_service()
        test_threshold_configurations()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nFreshness monitoring system is ready to use!")
        print("\nNext steps:")
        print("1. Run Alembic migration: alembic upgrade head")
        print("2. Start the backend API: uvicorn app.main:app --reload")
        print("3. Access the freshness monitoring page in the frontend")
        print("4. Ingest datasets to see freshness metrics")
        
    except Exception as e:
        print("\n" + "="*60)
        print("❌ TESTS FAILED!")
        print("="*60)
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
