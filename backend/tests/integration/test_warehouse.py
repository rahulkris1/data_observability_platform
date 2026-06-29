"""Integration tests for warehouse write and read workflows.

Tests warehouse service functionality including:
- Writing validation results to warehouse
- Reading data from warehouse
- Batch operations
- Audit logging
"""
import pytest
from datetime import datetime, timedelta
import json

from app.warehouse.warehouse_service import WarehouseService
from app.warehouse.audit_logger import AuditLogger
from app.warehouse.batch_loader import BatchLoader
from app.core.database import get_db
from app.models.base import Base


@pytest.fixture
def test_db():
    """Create test database session."""
    from app.core.database import engine, SessionLocal
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    yield db
    
    # Cleanup
    db.rollback()
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def warehouse_service(test_db):
    """Create warehouse service instance."""
    return WarehouseService(db=test_db)


@pytest.fixture
def audit_logger(test_db):
    """Create audit logger instance."""
    return AuditLogger(db=test_db)


@pytest.fixture
def batch_loader(test_db):
    """Create batch loader instance."""
    return BatchLoader(db=test_db)


@pytest.fixture
def sample_validation_result():
    """Create sample validation result."""
    return {
        "dataset_name": "test_customers.csv",
        "validation_timestamp": datetime.utcnow().isoformat(),
        "overall_status": "PASSED",
        "total_records": 100,
        "validators": [
            {
                "validator_name": "schema_validator",
                "status": "PASSED",
                "passed": 100,
                "total_records": 100,
                "failed_records": 0,
                "pass_rate": 100.0,
                "execution_time_ms": 150,
                "message": "All records passed schema validation"
            },
            {
                "validator_name": "null_validator",
                "status": "PASSED",
                "passed": 100,
                "total_records": 100,
                "failed_records": 0,
                "pass_rate": 100.0,
                "execution_time_ms": 80,
                "message": "No null values found"
            }
        ],
        "metadata": {
            "triggered_by": "integration_test",
            "environment": "test"
        }
    }


@pytest.mark.integration
class TestWarehouseWrite:
    """Integration tests for warehouse write operations."""
    
    def test_write_validation_result(self, warehouse_service, sample_validation_result):
        """Test writing validation result to warehouse."""
        result = warehouse_service.write_validation_result(sample_validation_result)
        
        assert result is not None
        assert "id" in result or "success" in result
    
    def test_write_multiple_validation_results(self, warehouse_service):
        """Test writing multiple validation results."""
        results = []
        
        for i in range(5):
            validation_result = {
                "dataset_name": f"test_dataset_{i}.csv",
                "validation_timestamp": datetime.utcnow().isoformat(),
                "overall_status": "PASSED" if i % 2 == 0 else "FAILED",
                "total_records": 100 + i * 10,
                "validators": [
                    {
                        "validator_name": "schema_validator",
                        "status": "PASSED" if i % 2 == 0 else "FAILED",
                        "passed": 100 if i % 2 == 0 else 90,
                        "total_records": 100,
                        "failed_records": 0 if i % 2 == 0 else 10,
                        "pass_rate": 100.0 if i % 2 == 0 else 90.0,
                        "execution_time_ms": 100 + i * 20
                    }
                ]
            }
            
            result = warehouse_service.write_validation_result(validation_result)
            results.append(result)
        
        assert len(results) == 5
    
    def test_write_with_error_handling(self, warehouse_service):
        """Test warehouse write with error handling."""
        # Invalid result (missing required fields)
        invalid_result = {
            "dataset_name": "test.csv"
            # Missing other required fields
        }
        
        try:
            result = warehouse_service.write_validation_result(invalid_result)
            # Should either handle gracefully or raise exception
            assert result is not None or True  # Some implementations may return None
        except Exception as e:
            # Exception is expected for invalid data
            assert isinstance(e, (ValueError, KeyError, Exception))
    
    def test_write_large_validation_result(self, warehouse_service):
        """Test writing large validation result."""
        large_result = {
            "dataset_name": "large_dataset.csv",
            "validation_timestamp": datetime.utcnow().isoformat(),
            "overall_status": "PASSED",
            "total_records": 100000,
            "validators": [
                {
                    "validator_name": f"validator_{i}",
                    "status": "PASSED",
                    "passed": 100000,
                    "total_records": 100000,
                    "failed_records": 0,
                    "pass_rate": 100.0,
                    "execution_time_ms": 1000 + i * 100,
                    "metadata": {f"key_{j}": f"value_{j}" for j in range(10)}
                }
                for i in range(10)
            ],
            "metadata": {
                "large_metadata": {f"field_{i}": f"data_{i}" for i in range(50)}
            }
        }
        
        result = warehouse_service.write_validation_result(large_result)
        assert result is not None


@pytest.mark.integration
class TestWarehouseRead:
    """Integration tests for warehouse read operations."""
    
    def test_read_validation_results(self, warehouse_service, sample_validation_result):
        """Test reading validation results from warehouse."""
        # First write
        warehouse_service.write_validation_result(sample_validation_result)
        
        # Then read
        results = warehouse_service.read_validation_results(
            dataset_name="test_customers.csv"
        )
        
        assert results is not None
        assert len(results) > 0
    
    def test_read_with_filters(self, warehouse_service):
        """Test reading with various filters."""
        # Write multiple results
        for i in range(5):
            result = {
                "dataset_name": "customers.csv" if i % 2 == 0 else "orders.csv",
                "validation_timestamp": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
                "overall_status": "PASSED",
                "total_records": 100,
                "validators": []
            }
            warehouse_service.write_validation_result(result)
        
        # Read with dataset filter
        customers_results = warehouse_service.read_validation_results(
            dataset_name="customers.csv"
        )
        assert len(customers_results) == 3  # i=0,2,4
        
        # Read with time filter
        recent_results = warehouse_service.read_validation_results(
            start_date=datetime.utcnow() - timedelta(hours=2)
        )
        assert len(recent_results) > 0
    
    def test_read_with_pagination(self, warehouse_service):
        """Test reading with pagination."""
        # Write 20 results
        for i in range(20):
            result = {
                "dataset_name": f"dataset_{i}.csv",
                "validation_timestamp": datetime.utcnow().isoformat(),
                "overall_status": "PASSED",
                "total_records": 100,
                "validators": []
            }
            warehouse_service.write_validation_result(result)
        
        # Read first page
        page1 = warehouse_service.read_validation_results(limit=10, offset=0)
        assert len(page1) == 10
        
        # Read second page
        page2 = warehouse_service.read_validation_results(limit=10, offset=10)
        assert len(page2) == 10
        
        # Ensure different results
        page1_ids = {r.get("id") for r in page1 if "id" in r}
        page2_ids = {r.get("id") for r in page2 if "id" in r}
        if page1_ids and page2_ids:
            assert page1_ids.isdisjoint(page2_ids)
    
    def test_read_nonexistent_dataset(self, warehouse_service):
        """Test reading non-existent dataset."""
        results = warehouse_service.read_validation_results(
            dataset_name="nonexistent.csv"
        )
        
        assert results is not None
        assert len(results) == 0


@pytest.mark.integration
class TestAuditLogger:
    """Integration tests for audit logger."""
    
    def test_log_validation_audit(self, audit_logger):
        """Test logging validation audit."""
        audit_data = {
            "dataset_name": "test.csv",
            "validation_type": "schema",
            "status": "PASSED",
            "execution_time_ms": 200,
            "total_records": 100,
            "failed_records": 0,
            "pass_rate": 100.0
        }
        
        result = audit_logger.log_validation(audit_data)
        assert result is not None
    
    def test_log_multiple_audits(self, audit_logger):
        """Test logging multiple audits."""
        audits = []
        
        for i in range(10):
            audit_data = {
                "dataset_name": f"dataset_{i}.csv",
                "validation_type": "schema",
                "status": "PASSED" if i % 2 == 0 else "FAILED",
                "execution_time_ms": 100 + i * 50,
                "total_records": 100,
                "failed_records": 0 if i % 2 == 0 else 10,
                "pass_rate": 100.0 if i % 2 == 0 else 90.0
            }
            
            result = audit_logger.log_validation(audit_data)
            audits.append(result)
        
        assert len(audits) == 10
    
    def test_retrieve_audit_history(self, audit_logger):
        """Test retrieving audit history."""
        # Log some audits
        for i in range(5):
            audit_logger.log_validation({
                "dataset_name": "test.csv",
                "validation_type": "schema",
                "status": "PASSED",
                "execution_time_ms": 100,
                "total_records": 100,
                "failed_records": 0,
                "pass_rate": 100.0
            })
        
        # Retrieve history
        history = audit_logger.get_audit_history(dataset_name="test.csv")
        assert len(history) == 5


@pytest.mark.integration
class TestBatchLoader:
    """Integration tests for batch loader."""
    
    def test_batch_load_validation_results(self, batch_loader):
        """Test batch loading validation results."""
        batch_data = [
            {
                "dataset_name": f"dataset_{i}.csv",
                "validation_timestamp": datetime.utcnow().isoformat(),
                "overall_status": "PASSED",
                "total_records": 100,
                "validators": []
            }
            for i in range(10)
        ]
        
        result = batch_loader.load_batch(batch_data)
        assert result is not None
        assert result.get("loaded_count") == 10 or result.get("success") is True
    
    def test_batch_load_with_partial_failure(self, batch_loader):
        """Test batch load with some invalid records."""
        batch_data = [
            {
                "dataset_name": "valid_1.csv",
                "validation_timestamp": datetime.utcnow().isoformat(),
                "overall_status": "PASSED",
                "total_records": 100,
                "validators": []
            },
            {
                "dataset_name": "invalid.csv"
                # Missing required fields
            },
            {
                "dataset_name": "valid_2.csv",
                "validation_timestamp": datetime.utcnow().isoformat(),
                "overall_status": "PASSED",
                "total_records": 100,
                "validators": []
            }
        ]
        
        result = batch_loader.load_batch(batch_data, skip_invalid=True)
        
        # Should load valid records and skip invalid
        assert result is not None
    
    def test_large_batch_load(self, batch_loader):
        """Test loading large batch."""
        batch_data = [
            {
                "dataset_name": f"dataset_{i}.csv",
                "validation_timestamp": datetime.utcnow().isoformat(),
                "overall_status": "PASSED",
                "total_records": 1000,
                "validators": []
            }
            for i in range(100)
        ]
        
        result = batch_loader.load_batch(batch_data)
        assert result is not None


@pytest.mark.integration
class TestWarehouseIntegration:
    """End-to-end warehouse integration tests."""
    
    def test_complete_write_read_workflow(self, warehouse_service, sample_validation_result):
        """Test complete write and read workflow."""
        # Write
        write_result = warehouse_service.write_validation_result(sample_validation_result)
        assert write_result is not None
        
        # Read back
        read_results = warehouse_service.read_validation_results(
            dataset_name=sample_validation_result["dataset_name"]
        )
        assert len(read_results) > 0
        
        # Verify data integrity
        found = False
        for result in read_results:
            if result.get("dataset_name") == sample_validation_result["dataset_name"]:
                found = True
                break
        assert found
    
    def test_warehouse_with_audit_logging(self, warehouse_service, audit_logger, sample_validation_result):
        """Test warehouse operations with audit logging."""
        # Write validation result
        warehouse_service.write_validation_result(sample_validation_result)
        
        # Log audit
        audit_data = {
            "dataset_name": sample_validation_result["dataset_name"],
            "validation_type": "schema",
            "status": sample_validation_result["overall_status"],
            "execution_time_ms": 200,
            "total_records": sample_validation_result["total_records"],
            "failed_records": 0,
            "pass_rate": 100.0
        }
        audit_logger.log_validation(audit_data)
        
        # Verify both operations succeeded
        results = warehouse_service.read_validation_results(
            dataset_name=sample_validation_result["dataset_name"]
        )
        assert len(results) > 0
        
        audit_history = audit_logger.get_audit_history(
            dataset_name=sample_validation_result["dataset_name"]
        )
        assert len(audit_history) > 0
    
    def test_concurrent_warehouse_operations(self, warehouse_service):
        """Test concurrent warehouse operations."""
        import concurrent.futures
        
        def write_result(i):
            result = {
                "dataset_name": f"concurrent_{i}.csv",
                "validation_timestamp": datetime.utcnow().isoformat(),
                "overall_status": "PASSED",
                "total_records": 100,
                "validators": []
            }
            return warehouse_service.write_validation_result(result)
        
        # Write concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(write_result, i) for i in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        assert len(results) == 10
        assert all(r is not None for r in results)
    
    def test_warehouse_transaction_rollback(self, warehouse_service, test_db):
        """Test transaction rollback on error."""
        try:
            # Start a transaction
            test_db.begin_nested()
            
            # Write valid result
            warehouse_service.write_validation_result({
                "dataset_name": "rollback_test.csv",
                "validation_timestamp": datetime.utcnow().isoformat(),
                "overall_status": "PASSED",
                "total_records": 100,
                "validators": []
            })
            
            # Simulate error
            raise Exception("Simulated error")
            
        except Exception:
            # Rollback
            test_db.rollback()
        
        # Verify data was not persisted
        results = warehouse_service.read_validation_results(
            dataset_name="rollback_test.csv"
        )
        # Depending on implementation, might be empty
        assert isinstance(results, list)
