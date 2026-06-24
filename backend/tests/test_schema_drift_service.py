"""Tests for Schema Drift Detection Service"""
import pytest
from datetime import datetime
from app.services.schema_drift_service import SchemaDriftService
from tests.fixtures.schema_drift_fixtures import (
    CUSTOMER_SCHEMA_V1,
    CUSTOMER_SCHEMA_V2_ADDED_COLUMN,
    CUSTOMER_SCHEMA_V3_TYPE_CHANGE,
    create_schema_version
)


def test_register_schema_first_version(db_session):
    """Test registering the first schema version"""
    service = SchemaDriftService(db_session)
    
    version, drift = service.register_schema(
        dataset_name="test_dataset",
        schema_definition=CUSTOMER_SCHEMA_V1,
        source="test"
    )
    
    assert version is not None
    assert version.version_number == 1
    assert version.dataset_name == "test_dataset"
    assert drift is None  # No drift on first version


def test_register_schema_no_drift(db_session):
    """Test registering the same schema twice"""
    service = SchemaDriftService(db_session)
    
    # Register first time
    v1, _ = service.register_schema(
        dataset_name="test_dataset",
        schema_definition=CUSTOMER_SCHEMA_V1,
        source="test"
    )
    
    # Register same schema again
    v2, drift = service.register_schema(
        dataset_name="test_dataset",
        schema_definition=CUSTOMER_SCHEMA_V1,
        source="test"
    )
    
    assert v1.id == v2.id  # Should return same version
    assert drift is None  # No drift detected


def test_register_schema_with_drift(db_session):
    """Test registering a new schema version with drift"""
    service = SchemaDriftService(db_session)
    
    # Register v1
    v1, _ = service.register_schema(
        dataset_name="test_dataset",
        schema_definition=CUSTOMER_SCHEMA_V1,
        source="test"
    )
    
    # Register v2 with added column
    v2, drift = service.register_schema(
        dataset_name="test_dataset",
        schema_definition=CUSTOMER_SCHEMA_V2_ADDED_COLUMN,
        source="test"
    )
    
    assert v2.version_number == 2
    assert drift is not None
    assert drift.drift_type == "column_added"
    assert drift.severity == "info"
    assert len(drift.changes["added_columns"]) == 1
    assert drift.changes["added_columns"][0]["name"] == "phone"


def test_detect_type_change_drift(db_session):
    """Test detection of type change drift"""
    service = SchemaDriftService(db_session)
    
    # Register v1 and v2
    service.register_schema("test_dataset", CUSTOMER_SCHEMA_V2_ADDED_COLUMN, "test")
    
    # Register v3 with type change
    v3, drift = service.register_schema(
        dataset_name="test_dataset",
        schema_definition=CUSTOMER_SCHEMA_V3_TYPE_CHANGE,
        source="test"
    )
    
    assert drift is not None
    assert drift.drift_type == "type_changed"
    assert drift.severity == "critical"
    assert len(drift.changes["type_changes"]) == 1
    assert drift.changes["type_changes"][0]["name"] == "customer_id"


def test_get_latest_version(db_session):
    """Test getting the latest schema version"""
    service = SchemaDriftService(db_session)
    
    # Register multiple versions
    service.register_schema("test_dataset", CUSTOMER_SCHEMA_V1, "test")
    service.register_schema("test_dataset", CUSTOMER_SCHEMA_V2_ADDED_COLUMN, "test")
    
    latest = service.get_latest_version("test_dataset")
    
    assert latest is not None
    assert latest.version_number == 2


def test_get_drift_history(db_session):
    """Test getting drift history"""
    service = SchemaDriftService(db_session)
    
    # Register versions to create drift
    service.register_schema("test_dataset", CUSTOMER_SCHEMA_V1, "test")
    service.register_schema("test_dataset", CUSTOMER_SCHEMA_V2_ADDED_COLUMN, "test")
    service.register_schema("test_dataset", CUSTOMER_SCHEMA_V3_TYPE_CHANGE, "test")
    
    history = service.get_drift_history(dataset_name="test_dataset")
    
    assert len(history) == 2
    assert history[0].drift_type == "type_changed"  # Most recent first
    assert history[1].drift_type == "column_added"


def test_acknowledge_drift(db_session):
    """Test acknowledging a drift event"""
    service = SchemaDriftService(db_session)
    
    # Create drift
    service.register_schema("test_dataset", CUSTOMER_SCHEMA_V1, "test")
    _, drift = service.register_schema("test_dataset", CUSTOMER_SCHEMA_V2_ADDED_COLUMN, "test")
    
    # Acknowledge drift
    acknowledged = service.acknowledge_drift(
        drift_id=drift.id,
        acknowledged_by="test_user",
        notes="This is expected"
    )
    
    assert acknowledged.acknowledged is True
    assert acknowledged.acknowledged_by == "test_user"
    assert acknowledged.notes == "This is expected"
    assert acknowledged.acknowledged_at is not None


def test_compare_schemas(db_session):
    """Test comparing two schema versions"""
    service = SchemaDriftService(db_session)
    
    # Register versions
    service.register_schema("test_dataset", CUSTOMER_SCHEMA_V1, "test")
    service.register_schema("test_dataset", CUSTOMER_SCHEMA_V2_ADDED_COLUMN, "test")
    
    comparison = service.compare_schemas("test_dataset", 1, 2)
    
    assert comparison["has_drift"] is True
    assert comparison["drift_type"] == "column_added"
    assert comparison["severity"] == "info"
    assert len(comparison["changes"]["added_columns"]) == 1


@pytest.fixture
def db_session():
    """Fixture for database session (implement based on your test setup)"""
    # This should return a test database session
    # Implementation depends on your testing framework
    from app.core.database import SessionLocal
    db = SessionLocal()
    yield db
    db.close()
