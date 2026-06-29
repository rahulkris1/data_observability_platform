"""Integration tests for validation execution API.

Tests the complete validation workflow including:
- Validation execution
- Result retrieval
- Error handling
- Database persistence
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
import json

from app.main import app
from app.core.database import get_db
from app.models.validation_log import ValidationLog
from app.storage.minio_client import minio_client


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_db(monkeypatch):
    """Mock database session for testing."""
    from app.core.database import engine, SessionLocal
    from app.models.base import Base
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield db
    
    # Cleanup
    db.rollback()
    db.close()
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_dataset_in_minio():
    """Upload sample dataset to MinIO for testing."""
    dataset_name = "test_customers.csv"
    csv_content = b"""customer_id,name,email,age
1,John Doe,john@example.com,30
2,Jane Smith,jane@example.com,25
3,Bob Johnson,bob@example.com,35"""
    
    # Upload to raw bucket
    object_name = f"raw/test_{dataset_name}"
    minio_client.upload_object(
        bucket_type="raw",
        object_name=object_name,
        data=csv_content,
        content_type="text/csv"
    )
    
    # Upload processed version
    processed_data = [
        {"customer_id": "1", "name": "John Doe", "email": "john@example.com", "age": "30"},
        {"customer_id": "2", "name": "Jane Smith", "email": "jane@example.com", "age": "25"},
        {"customer_id": "3", "name": "Bob Johnson", "email": "bob@example.com", "age": "35"}
    ]
    processed_object = f"processed/test_{dataset_name}.json"
    minio_client.upload_object(
        bucket_type="processed",
        object_name=processed_object,
        data=json.dumps(processed_data).encode(),
        content_type="application/json"
    )
    
    yield {
        "raw_object": object_name,
        "processed_object": processed_object,
        "dataset_name": dataset_name
    }
    
    # Cleanup
    try:
        minio_client.client.remove_object(minio_client.raw_bucket, object_name)
        minio_client.client.remove_object(minio_client.processed_bucket, processed_object)
    except:
        pass


@pytest.mark.integration
class TestValidationAPI:
    """Integration tests for validation execution API."""
    
    def test_execute_validation_success(self, client, test_db, sample_dataset_in_minio):
        """Test successful validation execution."""
        request_data = {
            "dataset_name": sample_dataset_in_minio["dataset_name"],
            "object_name": sample_dataset_in_minio["processed_object"],
            "validators": ["schema", "null", "datatype"],
            "metadata": {
                "triggered_by": "integration_test",
                "environment": "test"
            }
        }
        
        response = client.post("/api/v1/validations/execute", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "dataset_name" in data
        assert "validation_timestamp" in data
        assert "overall_status" in data
        assert "validators" in data
        assert isinstance(data["validators"], list)
        
        # Verify validation results
        assert data["dataset_name"] == sample_dataset_in_minio["dataset_name"]
        assert data["total_validators"] >= 1
        assert data["total_records"] == 3
        
        # Verify database persistence
        validation_logs = test_db.query(ValidationLog).all()
        assert len(validation_logs) > 0
    
    def test_execute_validation_with_schema_contract(self, client, test_db, sample_dataset_in_minio):
        """Test validation execution with schema contract."""
        request_data = {
            "dataset_name": sample_dataset_in_minio["dataset_name"],
            "object_name": sample_dataset_in_minio["processed_object"],
            "validators": ["schema"],
            "schema_contract_id": None,  # Will use auto-discovery
            "metadata": {
                "triggered_by": "integration_test"
            }
        }
        
        response = client.post("/api/v1/validations/execute", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "validators" in data
    
    def test_execute_validation_dataset_not_found(self, client, test_db):
        """Test validation execution with non-existent dataset."""
        request_data = {
            "dataset_name": "non_existent.csv",
            "object_name": "processed/non_existent.json",
            "validators": ["schema"]
        }
        
        response = client.post("/api/v1/validations/execute", json=request_data)
        
        # Should handle gracefully
        assert response.status_code in [404, 500]
    
    def test_execute_validation_invalid_validator(self, client, test_db, sample_dataset_in_minio):
        """Test validation execution with invalid validator name."""
        request_data = {
            "dataset_name": sample_dataset_in_minio["dataset_name"],
            "object_name": sample_dataset_in_minio["processed_object"],
            "validators": ["invalid_validator"],
            "metadata": {
                "triggered_by": "integration_test"
            }
        }
        
        response = client.post("/api/v1/validations/execute", json=request_data)
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 500]
    
    def test_execute_validation_empty_dataset(self, client, test_db):
        """Test validation execution with empty dataset."""
        # Upload empty dataset
        empty_object = "processed/empty_test.json"
        minio_client.upload_object(
            bucket_type="processed",
            object_name=empty_object,
            data=json.dumps([]).encode(),
            content_type="application/json"
        )
        
        request_data = {
            "dataset_name": "empty_test.csv",
            "object_name": empty_object,
            "validators": ["schema", "null"]
        }
        
        response = client.post("/api/v1/validations/execute", json=request_data)
        
        # Should handle empty dataset
        assert response.status_code in [200, 400]
        
        # Cleanup
        try:
            minio_client.client.remove_object(minio_client.processed_bucket, empty_object)
        except:
            pass
    
    def test_execute_validation_with_custom_rules(self, client, test_db, sample_dataset_in_minio):
        """Test validation execution with custom validation rules."""
        request_data = {
            "dataset_name": sample_dataset_in_minio["dataset_name"],
            "object_name": sample_dataset_in_minio["processed_object"],
            "validators": ["schema", "null", "datatype"],
            "validation_rules": {
                "null_check_columns": ["customer_id", "name", "email"],
                "datatype_checks": {
                    "age": "integer"
                }
            },
            "metadata": {
                "triggered_by": "integration_test",
                "custom_rules": True
            }
        }
        
        response = client.post("/api/v1/validations/execute", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "validators" in data
    
    def test_validation_result_caching(self, client, test_db, sample_dataset_in_minio):
        """Test that validation results can be cached."""
        request_data = {
            "dataset_name": sample_dataset_in_minio["dataset_name"],
            "object_name": sample_dataset_in_minio["processed_object"],
            "validators": ["schema"],
            "metadata": {
                "triggered_by": "integration_test"
            }
        }
        
        # First execution
        response1 = client.post("/api/v1/validations/execute", json=request_data)
        assert response1.status_code == 200
        
        # Second execution (may use cache)
        response2 = client.post("/api/v1/validations/execute", json=request_data)
        assert response2.status_code == 200
        
        # Both should return valid results
        assert response1.json()["dataset_name"] == response2.json()["dataset_name"]
    
    def test_concurrent_validation_execution(self, client, test_db, sample_dataset_in_minio):
        """Test concurrent validation executions."""
        import concurrent.futures
        
        request_data = {
            "dataset_name": sample_dataset_in_minio["dataset_name"],
            "object_name": sample_dataset_in_minio["processed_object"],
            "validators": ["schema", "null"],
            "metadata": {
                "triggered_by": "integration_test"
            }
        }
        
        def execute_validation():
            return client.post("/api/v1/validations/execute", json=request_data)
        
        # Execute 3 validations concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(execute_validation) for _ in range(3)]
            responses = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
    
    def test_validation_with_metadata_tracking(self, client, test_db, sample_dataset_in_minio):
        """Test that validation metadata is properly tracked."""
        request_data = {
            "dataset_name": sample_dataset_in_minio["dataset_name"],
            "object_name": sample_dataset_in_minio["processed_object"],
            "validators": ["schema"],
            "metadata": {
                "triggered_by": "integration_test_user",
                "environment": "test",
                "run_id": "test-run-123",
                "pipeline_name": "test_pipeline"
            }
        }
        
        response = client.post("/api/v1/validations/execute", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify metadata is included in response
        assert "metadata" in data
        assert data["metadata"]["triggered_by"] == "integration_test_user"
        assert data["metadata"]["environment"] == "test"


@pytest.mark.integration
@pytest.mark.slow
class TestValidationAPIPerformance:
    """Performance tests for validation API."""
    
    def test_large_dataset_validation(self, client, test_db):
        """Test validation on larger dataset."""
        # Create larger dataset
        large_data = [
            {"customer_id": str(i), "name": f"Customer {i}", "email": f"customer{i}@example.com", "age": str(20 + i % 50)}
            for i in range(1000)
        ]
        
        large_object = "processed/large_test.json"
        minio_client.upload_object(
            bucket_type="processed",
            object_name=large_object,
            data=json.dumps(large_data).encode(),
            content_type="application/json"
        )
        
        request_data = {
            "dataset_name": "large_test.csv",
            "object_name": large_object,
            "validators": ["schema", "null", "datatype"]
        }
        
        response = client.post("/api/v1/validations/execute", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_records"] == 1000
        
        # Cleanup
        try:
            minio_client.client.remove_object(minio_client.processed_bucket, large_object)
        except:
            pass
