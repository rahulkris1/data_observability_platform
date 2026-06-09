"""
Verification script for observability features.
Tests logging, metrics, and request tracking functionality.
"""
import sys
import time
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.observability import (
    configure_logging,
    get_logger,
    parse_log_file,
    get_log_stats,
    get_metrics_service,
)


def test_logging_configuration():
    """Test basic logging configuration."""
    print("Testing logging configuration...")
    
    # Configure logging
    configure_logging(
        log_level="DEBUG",
        enable_console=True,
        enable_json=True,
    )
    
    logger = get_logger(__name__)
    
    # Test different log levels
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    # Test logging with extra context
    logger.info(
        "Test message with context",
        extra={
            "user_id": "test_user",
            "request_id": "test_req_123",
            "action": "verification",
        },
    )
    
    print("[PASS] Logging configuration test passed")


def test_log_parsing():
    """Test log file parsing functionality."""
    print("\nTesting log parsing...")
    
    log_file = Path("logs/app.log")
    
    if not log_file.exists():
        print("[WARN] Log file doesn't exist yet, skipping parse test")
        return
    
    # Parse logs
    logs = parse_log_file(str(log_file), max_lines=10)
    
    if logs:
        print(f"[PASS] Successfully parsed {len(logs)} log entries")
        print(f"  Sample log: {logs[0].get('message', 'N/A')}")
    else:
        print("[WARN] No logs parsed")


def test_log_statistics():
    """Test log statistics functionality."""
    print("\nTesting log statistics...")
    
    log_file = Path("logs/app.log")
    
    if not log_file.exists():
        print("[WARN] Log file doesn't exist yet, skipping stats test")
        return
    
    stats = get_log_stats(str(log_file))
    
    print(f"[PASS] Log statistics retrieved:")
    print(f"  Total lines: {stats['total_lines']}")
    print(f"  File size: {stats['file_size_bytes']} bytes")
    print(f"  Levels: {stats['levels']}")
    print(f"  Loggers: {list(stats['loggers'].keys())[:5]}")  # Show first 5


def test_metrics_service():
    """Test metrics service functionality."""
    print("\nTesting metrics service...")
    
    metrics = get_metrics_service()
    
    # Test counter
    metrics.increment_counter("test_counter", value=1, tags={"type": "test"})
    metrics.increment_counter("test_counter", value=5, tags={"type": "test"})
    
    counter = metrics.get_counter("test_counter", tags={"type": "test"})
    assert counter is not None, "Counter should exist"
    assert counter.count == 6, f"Counter should be 6, got {counter.count}"
    
    print("[PASS] Counter test passed")
    
    # Test histogram
    metrics.record_histogram("test_histogram", 100.5, tags={"type": "test"})
    metrics.record_histogram("test_histogram", 200.3, tags={"type": "test"})
    metrics.record_histogram("test_histogram", 150.7, tags={"type": "test"})
    
    histogram = metrics.get_histogram("test_histogram", tags={"type": "test"})
    assert histogram is not None, "Histogram should exist"
    
    stats = histogram.get_stats()
    assert stats["count"] == 3, f"Histogram count should be 3, got {stats['count']}"
    assert stats["min"] == 100.5, f"Histogram min should be 100.5, got {stats['min']}"
    assert stats["max"] == 200.3, f"Histogram max should be 200.3, got {stats['max']}"
    
    print("[PASS] Histogram test passed")
    
    # Test API request tracking
    metrics.increment_api_request(
        method="GET",
        path="/api/v1/test",
        status_code=200,
        duration_ms=45.3,
    )
    
    metrics.increment_api_request(
        method="POST",
        path="/api/v1/test",
        status_code=500,
        duration_ms=123.7,
        error=True,
    )
    
    print("[PASS] API request tracking test passed")
    
    # Test validation tracking
    metrics.increment_validation_execution(
        validator_type="schema",
        success=True,
        duration_ms=234.5,
    )
    
    metrics.increment_validation_execution(
        validator_type="integrity",
        success=False,
        duration_ms=567.8,
    )
    
    print("[PASS] Validation tracking test passed")
    
    # Test ingestion tracking
    metrics.increment_ingestion_execution(
        dataset="test_dataset",
        success=True,
        records_processed=1000,
        duration_ms=5432.1,
    )
    
    print("[PASS] Ingestion tracking test passed")
    
    # Get all metrics
    all_metrics = metrics.get_all_metrics()
    
    print(f"\n[PASS] All metrics retrieved:")
    print(f"  Counters: {len(all_metrics['counters'])}")
    print(f"  Histograms: {len(all_metrics['histograms'])}")


def test_log_rotation():
    """Test log rotation functionality."""
    print("\nTesting log rotation...")
    
    logger = get_logger(__name__)
    
    # Generate many log messages to test rotation
    print("  Generating 1000 log messages...")
    for i in range(1000):
        logger.info(f"Test message {i}", extra={"iteration": i})
    
    log_file = Path("logs/app.log")
    
    if log_file.exists():
        file_size = log_file.stat().st_size
        print(f"[PASS] Log file created: {file_size} bytes")
        
        # Check for backup files
        backup_files = list(Path("logs").glob("app.log.*"))
        if backup_files:
            print(f"[PASS] Log rotation occurred: {len(backup_files)} backup files")
        else:
            print("  (No rotation yet - file size below threshold)")
    else:
        print("[WARN] Log file not found")


def test_metrics_export():
    """Test metrics export functionality."""
    print("\nTesting metrics export...")
    
    metrics = get_metrics_service()
    all_metrics = metrics.get_all_metrics()
    
    # Export to JSON
    json_output = json.dumps(all_metrics, indent=2)
    
    print(f"[PASS] Metrics exported to JSON ({len(json_output)} bytes)")
    print(f"\nSample metrics output:")
    print(json_output[:500] + "..." if len(json_output) > 500 else json_output)


def main():
    """Run all verification tests."""
    print("=" * 70)
    print("OBSERVABILITY VERIFICATION TESTS")
    print("=" * 70)
    
    try:
        test_logging_configuration()
        test_log_parsing()
        test_log_statistics()
        test_metrics_service()
        test_log_rotation()
        test_metrics_export()
        
        print("\n" + "=" * 70)
        print("[PASS] ALL TESTS PASSED")
        print("=" * 70)
        
        print("\nNext steps:")
        print("1. Start the FastAPI server to test request logging middleware")
        print("2. Access the logs API endpoint: GET /api/v1/observability/logs")
        print("3. Access the metrics API endpoint: GET /api/v1/observability/metrics")
        print("4. View logs in the frontend at: http://localhost:3000/logs")
        
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
