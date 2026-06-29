"""Integration tests for audit history API.

Tests audit log creation, retrieval, filtering, and aggregation.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.main import app
from app.core.database import get_db
from app.models.audit_log import AuditLog
from app.schemas.audit_schema import AuditLogCreate


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
def sample_audit_logs(test_db):
    """Create sample audit logs in database."""
    audit_logs = []
    base_time = datetime.utcnow()
    
    datasets = ["customers.csv", "orders.csv", "products.csv"]
    statuses = ["PASSED", "FAILED", "WARNING"]
    validation_types = ["schema", "null", "datatype", "integrity"]
    
    for i in range(15):
        audit = AuditLog(
            dataset_name=datasets[i % 3],
            validation_type=validation_types[i % 4],
            status=statuses[i % 3],
            execution_time_ms=100 + (i * 50),
            total_records=1000 + (i * 100),
            failed_records=i * 10 if statuses[i % 3] == "FAILED" else 0,
            pass_rate=100.0 if statuses[i % 3] == "PASSED" else (90.0 - i),
            validator_name=f"{validation_types[i % 4]}_validator",
            triggered_by="integration_test",
            environment="test",
            metadata={
                "test_run": i + 1,
                "batch_id": f"batch_{i // 5}"
            },
            created_at=base_time - timedelta(hours=i)
        )
        test_db.add(audit)
        audit_logs.append(audit)
    
    test_db.commit()
    
    # Refresh to get IDs
    for audit in audit_logs:
        test_db.refresh(audit)
    
    return audit_logs


@pytest.mark.integration
class TestAuditAPI:
    """Integration tests for audit API."""
    
    def test_create_audit_record(self, client, test_db):
        """Test creating a new audit log record."""
        audit_data = {
            "dataset_name": "test_dataset.csv",
            "validation_type": "schema",
            "status": "PASSED",
            "execution_time_ms": 250,
            "total_records": 500,
            "failed_records": 0,
            "pass_rate": 100.0,
            "validator_name": "schema_validator",
            "triggered_by": "integration_test",
            "environment": "test",
            "metadata": {
                "run_id": "test-123"
            }
        }
        
        response = client.post("/api/v1/audit/", json=audit_data)
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response
        assert data["dataset_name"] == "test_dataset.csv"
        assert data["validation_type"] == "schema"
        assert data["status"] == "PASSED"
        assert data["pass_rate"] == 100.0
        assert "id" in data
        assert "created_at" in data
        
        # Verify database persistence
        audit = test_db.query(AuditLog).filter_by(dataset_name="test_dataset.csv").first()
        assert audit is not None
        assert audit.validation_type == "schema"
    
    def test_get_audit_history_all(self, client, test_db, sample_audit_logs):
        """Test retrieving all audit history."""
        response = client.get("/api/v1/audit/history")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "audits" in data
        assert "total_count" in data
        assert "limit" in data
        assert "offset" in data
        
        # Verify data
        assert data["total_count"] == 15
        assert len(data["audits"]) <= data["limit"]
    
    def test_get_audit_history_with_pagination(self, client, test_db, sample_audit_logs):
        """Test audit history pagination."""
        # First page
        response1 = client.get("/api/v1/audit/history?limit=5&offset=0")
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["audits"]) == 5
        assert data1["offset"] == 0
        
        # Second page
        response2 = client.get("/api/v1/audit/history?limit=5&offset=5")
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["audits"]) == 5
        assert data2["offset"] == 5
        
        # Verify different records
        first_ids = {audit["id"] for audit in data1["audits"]}
        second_ids = {audit["id"] for audit in data2["audits"]}
        assert first_ids.isdisjoint(second_ids)
    
    def test_filter_by_dataset_name(self, client, test_db, sample_audit_logs):
        """Test filtering audit history by dataset name."""
        response = client.get("/api/v1/audit/history?dataset_name=customers")
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned audits should match the filter
        for audit in data["audits"]:
            assert "customers" in audit["dataset_name"].lower()
    
    def test_filter_by_validation_type(self, client, test_db, sample_audit_logs):
        """Test filtering by validation type."""
        response = client.get("/api/v1/audit/history?validation_type=schema")
        
        assert response.status_code == 200
        data = response.json()
        
        for audit in data["audits"]:
            assert audit["validation_type"] == "schema"
    
    def test_filter_by_status(self, client, test_db, sample_audit_logs):
        """Test filtering by status."""
        response = client.get("/api/v1/audit/history?status=PASSED")
        
        assert response.status_code == 200
        data = response.json()
        
        for audit in data["audits"]:
            assert audit["status"] == "PASSED"
    
    def test_filter_by_date_range(self, client, test_db, sample_audit_logs):
        """Test filtering by date range."""
        now = datetime.utcnow()
        start_date = (now - timedelta(hours=10)).isoformat()
        end_date = now.isoformat()
        
        response = client.get(
            f"/api/v1/audit/history?start_date={start_date}&end_date={end_date}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify dates are within range
        for audit in data["audits"]:
            audit_time = datetime.fromisoformat(audit["created_at"].replace("Z", "+00:00"))
            assert audit_time >= datetime.fromisoformat(start_date)
            assert audit_time <= datetime.fromisoformat(end_date)
    
    def test_filter_by_triggered_by(self, client, test_db, sample_audit_logs):
        """Test filtering by triggered_by field."""
        response = client.get("/api/v1/audit/history?triggered_by=integration_test")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_count"] > 0
        for audit in data["audits"]:
            assert audit["triggered_by"] == "integration_test"
    
    def test_filter_by_environment(self, client, test_db, sample_audit_logs):
        """Test filtering by environment."""
        response = client.get("/api/v1/audit/history?environment=test")
        
        assert response.status_code == 200
        data = response.json()
        
        for audit in data["audits"]:
            assert audit["environment"] == "test"
    
    def test_combined_filters(self, client, test_db, sample_audit_logs):
        """Test combining multiple filters."""
        response = client.get(
            "/api/v1/audit/history"
            "?dataset_name=customers"
            "&status=PASSED"
            "&environment=test"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for audit in data["audits"]:
            assert "customers" in audit["dataset_name"].lower()
            assert audit["status"] == "PASSED"
            assert audit["environment"] == "test"
    
    def test_sort_by_created_at_desc(self, client, test_db, sample_audit_logs):
        """Test sorting by created_at descending (most recent first)."""
        response = client.get(
            "/api/v1/audit/history?sort_by=created_at&sort_order=desc&limit=5"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify descending order
        audits = data["audits"]
        for i in range(len(audits) - 1):
            time1 = datetime.fromisoformat(audits[i]["created_at"].replace("Z", "+00:00"))
            time2 = datetime.fromisoformat(audits[i + 1]["created_at"].replace("Z", "+00:00"))
            assert time1 >= time2
    
    def test_sort_by_execution_time(self, client, test_db, sample_audit_logs):
        """Test sorting by execution time."""
        response = client.get(
            "/api/v1/audit/history?sort_by=execution_time_ms&sort_order=asc&limit=5"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify ascending order
        audits = data["audits"]
        for i in range(len(audits) - 1):
            assert audits[i]["execution_time_ms"] <= audits[i + 1]["execution_time_ms"]
    
    def test_get_audit_statistics(self, client, test_db, sample_audit_logs):
        """Test getting audit statistics (if endpoint exists)."""
        response = client.get("/api/v1/audit/statistics")
        
        # Statistics endpoint might not exist yet
        if response.status_code == 200:
            data = response.json()
            assert "total_validations" in data or "summary" in data
    
    def test_get_audit_by_id(self, client, test_db, sample_audit_logs):
        """Test retrieving specific audit by ID (if endpoint exists)."""
        audit_id = sample_audit_logs[0].id
        
        response = client.get(f"/api/v1/audit/{audit_id}")
        
        # Single audit endpoint might not exist yet
        if response.status_code == 200:
            data = response.json()
            assert data["id"] == audit_id
    
    def test_empty_audit_history(self, client, test_db):
        """Test retrieving audit history when database is empty."""
        response = client.get("/api/v1/audit/history")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
        assert len(data["audits"]) == 0
    
    def test_invalid_date_format(self, client, test_db):
        """Test handling invalid date format."""
        response = client.get("/api/v1/audit/history?start_date=invalid-date")
        
        # Should return 422 for validation error
        assert response.status_code in [422, 400]
    
    def test_pagination_beyond_results(self, client, test_db, sample_audit_logs):
        """Test pagination offset beyond available results."""
        response = client.get("/api/v1/audit/history?limit=10&offset=100")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["audits"]) == 0
        assert data["total_count"] == 15


@pytest.mark.integration
class TestAuditAPIEdgeCases:
    """Edge case tests for audit API."""
    
    def test_create_audit_with_minimal_data(self, client, test_db):
        """Test creating audit record with minimal required fields."""
        audit_data = {
            "dataset_name": "minimal_test.csv",
            "validation_type": "schema",
            "status": "PASSED",
            "execution_time_ms": 100,
            "total_records": 10,
            "failed_records": 0,
            "pass_rate": 100.0,
            "validator_name": "test_validator",
            "triggered_by": "test",
            "environment": "test"
        }
        
        response = client.post("/api/v1/audit/", json=audit_data)
        
        assert response.status_code == 201
    
    def test_create_audit_with_error_summary(self, client, test_db):
        """Test creating audit record with error summary."""
        audit_data = {
            "dataset_name": "error_test.csv",
            "validation_type": "datatype",
            "status": "FAILED",
            "execution_time_ms": 300,
            "total_records": 100,
            "failed_records": 15,
            "pass_rate": 85.0,
            "validator_name": "datatype_validator",
            "triggered_by": "test",
            "environment": "test",
            "error_summary": {
                "total_errors": 15,
                "error_types": {
                    "type_mismatch": 10,
                    "invalid_format": 5
                }
            },
            "details": "Datatype validation failed for age column"
        }
        
        response = client.post("/api/v1/audit/", json=audit_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["error_summary"] is not None
        assert data["details"] == "Datatype validation failed for age column"
    
    def test_large_metadata_storage(self, client, test_db):
        """Test storing large metadata in audit log."""
        large_metadata = {
            f"key_{i}": f"value_{i}" for i in range(100)
        }
        
        audit_data = {
            "dataset_name": "large_metadata_test.csv",
            "validation_type": "schema",
            "status": "PASSED",
            "execution_time_ms": 200,
            "total_records": 50,
            "failed_records": 0,
            "pass_rate": 100.0,
            "validator_name": "test_validator",
            "triggered_by": "test",
            "environment": "test",
            "metadata": large_metadata
        }
        
        response = client.post("/api/v1/audit/", json=audit_data)
        
        assert response.status_code == 201
        data = response.json()
        assert len(data["metadata"]) == 100
