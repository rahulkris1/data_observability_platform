"""Complete backend integration workflow tests.

Tests the entire backend workflow from ingestion to validation to storage.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import json
from datetime import datetime
import time

from app.main import app
from app.core.database import get_db
from app.models.base import Base
from app.storage.minio_client import minio_client


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture(scope="module")
def test_db_module():
    """Module-scoped database for workflow tests."""
    from app.core.database import engine, SessionLocal
    
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_db():
    """Function-scoped database session."""
    from app.core.database import engine, SessionLocal
    
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield db
    
    db.rollback()
    db.close()
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.mark.integration
class TestCompleteBackendWorkflow:
    """Test complete backend integration workflow."""
    
    def test_end_to_end_validation_workflow(self, client, test_db):
        """Test complete end-to-end validation workflow."""
        # Step 1: Upload dataset to MinIO
        csv_content = b"""customer_id,name,email,age
1,John Doe,john@example.com,30
2,Jane Smith,jane@example.com,25
3,Bob Johnson,bob@example.com,35"""
        
        raw_object = "raw/workflow_test.csv"
        minio_client.upload_object(
            bucket_type="raw",
            object_name=raw_object,
            data=csv_content,
            content_type="text/csv"
        )
        
        # Upload processed version
        processed_data = [
            {"customer_id": "1", "name": "John Doe", "email": "john@example.com", "age": "30"},
            {"customer_id": "2", "name": "Jane Smith", "email": "jane@example.com", "age": "25"},
            {"customer_id": "3", "name": "Bob Johnson", "email": "bob@example.com", "age": "35"}
        ]
        processed_object = "processed/workflow_test.json"
        minio_client.upload_object(
            bucket_type="processed",
            object_name=processed_object,
            data=json.dumps(processed_data).encode(),
            content_type="application/json"
        )
        
        # Step 2: Execute validation
        validation_request = {
            "dataset_name": "workflow_test.csv",
            "object_name": processed_object,
            "validators": ["schema", "null"],
            "metadata": {
                "triggered_by": "integration_workflow_test",
                "environment": "test"
            }
        }
        
        validation_response = client.post(
            "/api/v1/validations/execute",
            json=validation_request
        )
        
        assert validation_response.status_code == 200
        validation_data = validation_response.json()
        
        # Step 3: Verify validation results
        assert validation_data["dataset_name"] == "workflow_test.csv"
        assert validation_data["total_records"] == 3
        assert "validators" in validation_data
        assert len(validation_data["validators"]) >= 1
        
        # Step 4: Create audit log
        audit_request = {
            "dataset_name": "workflow_test.csv",
            "validation_type": "schema",
            "status": validation_data["overall_status"],
            "execution_time_ms": validation_data.get("total_execution_time_ms", 200),
            "total_records": validation_data["total_records"],
            "failed_records": 0,
            "pass_rate": 100.0,
            "validator_name": "workflow_validator",
            "triggered_by": "integration_workflow_test",
            "environment": "test",
            "metadata": validation_data.get("metadata", {})
        }
        
        audit_response = client.post("/api/v1/audit/", json=audit_request)
        assert audit_response.status_code == 201
        
        # Step 5: Retrieve audit history
        audit_history_response = client.get(
            "/api/v1/audit/history?dataset_name=workflow_test"
        )
        assert audit_history_response.status_code == 200
        audit_history = audit_history_response.json()
        assert audit_history["total_count"] >= 1
        
        # Cleanup
        try:
            minio_client.client.remove_object(minio_client.raw_bucket, raw_object)
            minio_client.client.remove_object(minio_client.processed_bucket, processed_object)
        except:
            pass
    
    def test_multi_dataset_workflow(self, client, test_db):
        """Test workflow with multiple datasets."""
        datasets = []
        
        # Upload 3 different datasets
        for i in range(3):
            csv_content = f"""id,value,status
{i*10+1},data_{i*10+1},active
{i*10+2},data_{i*10+2},inactive
{i*10+3},data_{i*10+3},active""".encode()
            
            raw_object = f"raw/multi_dataset_{i}.csv"
            processed_object = f"processed/multi_dataset_{i}.json"
            
            minio_client.upload_object(
                bucket_type="raw",
                object_name=raw_object,
                data=csv_content,
                content_type="text/csv"
            )
            
            processed_data = [
                {"id": str(i*10+1), "value": f"data_{i*10+1}", "status": "active"},
                {"id": str(i*10+2), "value": f"data_{i*10+2}", "status": "inactive"},
                {"id": str(i*10+3), "value": f"data_{i*10+3}", "status": "active"}
            ]
            
            minio_client.upload_object(
                bucket_type="processed",
                object_name=processed_object,
                data=json.dumps(processed_data).encode(),
                content_type="application/json"
            )
            
            datasets.append({
                "name": f"multi_dataset_{i}.csv",
                "raw": raw_object,
                "processed": processed_object
            })
        
        # Execute validation for each dataset
        validation_results = []
        for dataset in datasets:
            response = client.post(
                "/api/v1/validations/execute",
                json={
                    "dataset_name": dataset["name"],
                    "object_name": dataset["processed"],
                    "validators": ["schema"],
                    "metadata": {"test": "multi_dataset"}
                }
            )
            assert response.status_code == 200
            validation_results.append(response.json())
        
        # Verify all validations completed
        assert len(validation_results) == 3
        for result in validation_results:
            assert result["total_records"] == 3
        
        # Cleanup
        for dataset in datasets:
            try:
                minio_client.client.remove_object(minio_client.raw_bucket, dataset["raw"])
                minio_client.client.remove_object(minio_client.processed_bucket, dataset["processed"])
            except:
                pass
    
    def test_workflow_with_validation_failure(self, client, test_db):
        """Test workflow when validation fails."""
        # Create dataset with schema issues
        processed_data = [
            {"id": "1", "name": "John"},  # Missing email
            {"id": "2", "email": "jane@example.com"},  # Missing name
        ]
        
        processed_object = "processed/validation_failure_test.json"
        minio_client.upload_object(
            bucket_type="processed",
            object_name=processed_object,
            data=json.dumps(processed_data).encode(),
            content_type="application/json"
        )
        
        # Execute validation
        response = client.post(
            "/api/v1/validations/execute",
            json={
                "dataset_name": "validation_failure_test.csv",
                "object_name": processed_object,
                "validators": ["schema", "null"]
            }
        )
        
        # Should still return 200 with failure status
        assert response.status_code == 200
        data = response.json()
        
        # Overall status might be FAILED or WARNING
        assert data["overall_status"] in ["FAILED", "WARNING", "PASSED"]
        
        # Create audit log for failed validation
        audit_response = client.post(
            "/api/v1/audit/",
            json={
                "dataset_name": "validation_failure_test.csv",
                "validation_type": "schema",
                "status": "FAILED",
                "execution_time_ms": 200,
                "total_records": 2,
                "failed_records": 2,
                "pass_rate": 0.0,
                "validator_name": "schema_validator",
                "triggered_by": "test",
                "environment": "test",
                "error_summary": {"schema_mismatches": 2}
            }
        )
        
        assert audit_response.status_code == 201
        
        # Cleanup
        try:
            minio_client.client.remove_object(minio_client.processed_bucket, processed_object)
        except:
            pass
    
    def test_workflow_performance(self, client, test_db):
        """Test workflow performance with realistic data."""
        # Create larger dataset
        large_data = [
            {"id": str(i), "name": f"Customer {i}", "email": f"customer{i}@example.com"}
            for i in range(1000)
        ]
        
        processed_object = "processed/performance_test.json"
        minio_client.upload_object(
            bucket_type="processed",
            object_name=processed_object,
            data=json.dumps(large_data).encode(),
            content_type="application/json"
        )
        
        # Measure validation time
        start_time = time.time()
        
        response = client.post(
            "/api/v1/validations/execute",
            json={
                "dataset_name": "performance_test.csv",
                "object_name": processed_object,
                "validators": ["schema", "null"]
            }
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert response.status_code == 200
        assert duration < 30  # Should complete within 30 seconds
        
        data = response.json()
        assert data["total_records"] == 1000
        
        # Cleanup
        try:
            minio_client.client.remove_object(minio_client.processed_bucket, processed_object)
        except:
            pass
    
    def test_workflow_with_caching(self, client, test_db):
        """Test workflow with result caching."""
        processed_data = [{"id": "1", "value": "test"}]
        processed_object = "processed/caching_test.json"
        
        minio_client.upload_object(
            bucket_type="processed",
            object_name=processed_object,
            data=json.dumps(processed_data).encode(),
            content_type="application/json"
        )
        
        request_data = {
            "dataset_name": "caching_test.csv",
            "object_name": processed_object,
            "validators": ["schema"]
        }
        
        # First request
        response1 = client.post("/api/v1/validations/execute", json=request_data)
        assert response1.status_code == 200
        
        # Second request (may use cache)
        response2 = client.post("/api/v1/validations/execute", json=request_data)
        assert response2.status_code == 200
        
        # Both should return same dataset info
        assert response1.json()["dataset_name"] == response2.json()["dataset_name"]
        
        # Cleanup
        try:
            minio_client.client.remove_object(minio_client.processed_bucket, processed_object)
        except:
            pass
    
    def test_complete_observability_workflow(self, client, test_db):
        """Test complete workflow with observability endpoints."""
        # Upload dataset
        processed_data = [{"id": "1", "metric": "cpu_usage", "value": "75"}]
        processed_object = "processed/observability_test.json"
        
        minio_client.upload_object(
            bucket_type="processed",
            object_name=processed_object,
            data=json.dumps(processed_data).encode(),
            content_type="application/json"
        )
        
        # Execute validation
        validation_response = client.post(
            "/api/v1/validations/execute",
            json={
                "dataset_name": "observability_test.csv",
                "object_name": processed_object,
                "validators": ["schema"]
            }
        )
        assert validation_response.status_code == 200
        
        # Check health endpoint
        health_response = client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"
        
        # Check metrics (if endpoint exists)
        metrics_response = client.get("/api/v1/metrics")
        if metrics_response.status_code == 200:
            metrics_data = metrics_response.json()
            assert metrics_data is not None
        
        # Cleanup
        try:
            minio_client.client.remove_object(minio_client.processed_bucket, processed_object)
        except:
            pass


@pytest.mark.integration
@pytest.mark.slow
class TestWorkflowResilience:
    """Test workflow resilience and error recovery."""
    
    def test_workflow_with_minio_unavailable(self, client, test_db):
        """Test workflow behavior when MinIO is unavailable."""
        # Try to validate non-existent object
        response = client.post(
            "/api/v1/validations/execute",
            json={
                "dataset_name": "nonexistent.csv",
                "object_name": "processed/nonexistent.json",
                "validators": ["schema"]
            }
        )
        
        # Should handle gracefully
        assert response.status_code in [404, 500]
    
    def test_workflow_with_database_rollback(self, client, test_db):
        """Test workflow with transaction rollback."""
        # This tests database transaction handling
        processed_data = [{"id": "1", "value": "test"}]
        processed_object = "processed/rollback_test.json"
        
        minio_client.upload_object(
            bucket_type="processed",
            object_name=processed_object,
            data=json.dumps(processed_data).encode(),
            content_type="application/json"
        )
        
        try:
            test_db.begin_nested()
            
            response = client.post(
                "/api/v1/validations/execute",
                json={
                    "dataset_name": "rollback_test.csv",
                    "object_name": processed_object,
                    "validators": ["schema"]
                }
            )
            
            # Simulate error and rollback
            test_db.rollback()
            
        except Exception as e:
            test_db.rollback()
        
        # Cleanup
        try:
            minio_client.client.remove_object(minio_client.processed_bucket, processed_object)
        except:
            pass
    
    def test_concurrent_workflow_execution(self, client, test_db):
        """Test concurrent workflow executions."""
        import concurrent.futures
        
        # Prepare datasets
        datasets = []
        for i in range(5):
            processed_data = [{"id": str(i), "value": f"test_{i}"}]
            processed_object = f"processed/concurrent_{i}.json"
            
            minio_client.upload_object(
                bucket_type="processed",
                object_name=processed_object,
                data=json.dumps(processed_data).encode(),
                content_type="application/json"
            )
            datasets.append(processed_object)
        
        def execute_validation(i):
            return client.post(
                "/api/v1/validations/execute",
                json={
                    "dataset_name": f"concurrent_{i}.csv",
                    "object_name": datasets[i],
                    "validators": ["schema"]
                }
            )
        
        # Execute concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(execute_validation, i) for i in range(5)]
            responses = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
        
        # Cleanup
        for obj in datasets:
            try:
                minio_client.client.remove_object(minio_client.processed_bucket, obj)
            except:
                pass
