"""Testing fixtures for schema drift detection

Provides reusable test data and fixtures for schema drift tests
"""
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.models.schema_version import SchemaVersion
from app.models.schema_drift_history import SchemaDriftHistory


# Sample schema definitions
CUSTOMER_SCHEMA_V1 = {
    "columns": [
        {"name": "customer_id", "data_type": "integer", "nullable": False, "position": 0},
        {"name": "first_name", "data_type": "string", "nullable": False, "position": 1},
        {"name": "last_name", "data_type": "string", "nullable": False, "position": 2},
        {"name": "email", "data_type": "string", "nullable": False, "position": 3},
        {"name": "created_at", "data_type": "timestamp", "nullable": False, "position": 4}
    ]
}

CUSTOMER_SCHEMA_V2_ADDED_COLUMN = {
    "columns": [
        {"name": "customer_id", "data_type": "integer", "nullable": False, "position": 0},
        {"name": "first_name", "data_type": "string", "nullable": False, "position": 1},
        {"name": "last_name", "data_type": "string", "nullable": False, "position": 2},
        {"name": "email", "data_type": "string", "nullable": False, "position": 3},
        {"name": "phone", "data_type": "string", "nullable": True, "position": 4},  # Added column
        {"name": "created_at", "data_type": "timestamp", "nullable": False, "position": 5}
    ]
}

CUSTOMER_SCHEMA_V3_TYPE_CHANGE = {
    "columns": [
        {"name": "customer_id", "data_type": "string", "nullable": False, "position": 0},  # Type changed from integer to string
        {"name": "first_name", "data_type": "string", "nullable": False, "position": 1},
        {"name": "last_name", "data_type": "string", "nullable": False, "position": 2},
        {"name": "email", "data_type": "string", "nullable": False, "position": 3},
        {"name": "phone", "data_type": "string", "nullable": True, "position": 4},
        {"name": "created_at", "data_type": "timestamp", "nullable": False, "position": 5}
    ]
}

CUSTOMER_SCHEMA_V4_COLUMN_REMOVED = {
    "columns": [
        {"name": "customer_id", "data_type": "string", "nullable": False, "position": 0},
        {"name": "first_name", "data_type": "string", "nullable": False, "position": 1},
        {"name": "last_name", "data_type": "string", "nullable": False, "position": 2},
        {"name": "email", "data_type": "string", "nullable": False, "position": 3},
        # phone column removed
        {"name": "created_at", "data_type": "timestamp", "nullable": False, "position": 4}
    ]
}

ORDERS_SCHEMA_V1 = {
    "columns": [
        {"name": "order_id", "data_type": "integer", "nullable": False, "position": 0},
        {"name": "customer_id", "data_type": "integer", "nullable": False, "position": 1},
        {"name": "order_date", "data_type": "date", "nullable": False, "position": 2},
        {"name": "total_amount", "data_type": "float", "nullable": False, "position": 3},
        {"name": "status", "data_type": "string", "nullable": False, "position": 4}
    ]
}

ORDERS_SCHEMA_V2_NULLABILITY_CHANGE = {
    "columns": [
        {"name": "order_id", "data_type": "integer", "nullable": False, "position": 0},
        {"name": "customer_id", "data_type": "integer", "nullable": False, "position": 1},
        {"name": "order_date", "data_type": "date", "nullable": False, "position": 2},
        {"name": "total_amount", "data_type": "float", "nullable": True, "position": 3},  # Changed from non-nullable to nullable
        {"name": "status", "data_type": "string", "nullable": False, "position": 4}
    ]
}


@pytest.fixture
def sample_schema_v1() -> Dict[str, Any]:
    """Fixture for sample schema version 1"""
    return CUSTOMER_SCHEMA_V1.copy()


@pytest.fixture
def sample_schema_v2_added_column() -> Dict[str, Any]:
    """Fixture for sample schema version 2 with added column"""
    return CUSTOMER_SCHEMA_V2_ADDED_COLUMN.copy()


@pytest.fixture
def sample_schema_v3_type_change() -> Dict[str, Any]:
    """Fixture for sample schema version 3 with type change"""
    return CUSTOMER_SCHEMA_V3_TYPE_CHANGE.copy()


@pytest.fixture
def sample_schema_v4_column_removed() -> Dict[str, Any]:
    """Fixture for sample schema version 4 with column removed"""
    return CUSTOMER_SCHEMA_V4_COLUMN_REMOVED.copy()


@pytest.fixture
def sample_orders_schema_v1() -> Dict[str, Any]:
    """Fixture for sample orders schema version 1"""
    return ORDERS_SCHEMA_V1.copy()


@pytest.fixture
def sample_orders_schema_v2_nullability() -> Dict[str, Any]:
    """Fixture for sample orders schema version 2 with nullability change"""
    return ORDERS_SCHEMA_V2_NULLABILITY_CHANGE.copy()


def create_schema_version(
    db: Session,
    dataset_name: str,
    version_number: int,
    schema_definition: Dict[str, Any],
    version_hash: str = "dummy_hash",
    source: str = "test",
    detected_at: datetime = None
) -> SchemaVersion:
    """Helper function to create a schema version for testing
    
    Args:
        db: Database session
        dataset_name: Name of the dataset
        version_number: Version number
        schema_definition: Schema definition
        version_hash: Hash of the schema (default: "dummy_hash")
        source: Source of the schema (default: "test")
        detected_at: Detection timestamp (default: current time)
        
    Returns:
        Created SchemaVersion instance
    """
    if detected_at is None:
        detected_at = datetime.utcnow()
    
    schema_version = SchemaVersion(
        dataset_name=dataset_name,
        version_number=version_number,
        version_hash=f"{version_hash}_{version_number}",
        schema_definition=schema_definition,
        detected_at=detected_at,
        source=source
    )
    
    db.add(schema_version)
    db.commit()
    db.refresh(schema_version)
    
    return schema_version


def create_drift_record(
    db: Session,
    dataset_name: str,
    previous_version_id: int,
    current_version_id: int,
    drift_type: str,
    severity: str,
    changes: Dict[str, Any],
    acknowledged: bool = False
) -> SchemaDriftHistory:
    """Helper function to create a drift record for testing
    
    Args:
        db: Database session
        dataset_name: Name of the dataset
        previous_version_id: ID of previous version
        current_version_id: ID of current version
        drift_type: Type of drift
        severity: Severity level
        changes: Changes dictionary
        acknowledged: Whether drift is acknowledged
        
    Returns:
        Created SchemaDriftHistory instance
    """
    drift = SchemaDriftHistory(
        dataset_name=dataset_name,
        previous_version_id=previous_version_id,
        current_version_id=current_version_id,
        drift_type=drift_type,
        severity=severity,
        changes=changes,
        detected_at=datetime.utcnow(),
        acknowledged=acknowledged
    )
    
    db.add(drift)
    db.commit()
    db.refresh(drift)
    
    return drift


@pytest.fixture
def create_test_schema_versions(db: Session):
    """Fixture that creates a series of test schema versions with drift
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with created versions and drift records
    """
    now = datetime.utcnow()
    
    # Create version 1
    v1 = create_schema_version(
        db, "test_customers", 1, CUSTOMER_SCHEMA_V1,
        detected_at=now - timedelta(days=30)
    )
    
    # Create version 2 with added column
    v2 = create_schema_version(
        db, "test_customers", 2, CUSTOMER_SCHEMA_V2_ADDED_COLUMN,
        detected_at=now - timedelta(days=20)
    )
    
    drift1 = create_drift_record(
        db, "test_customers", v1.id, v2.id,
        drift_type="column_added",
        severity="info",
        changes={
            "added_columns": [{"name": "phone", "data_type": "string", "nullable": True}],
            "removed_columns": [],
            "type_changes": [],
            "nullability_changes": [],
            "position_changes": []
        }
    )
    
    # Create version 3 with type change
    v3 = create_schema_version(
        db, "test_customers", 3, CUSTOMER_SCHEMA_V3_TYPE_CHANGE,
        detected_at=now - timedelta(days=10)
    )
    
    drift2 = create_drift_record(
        db, "test_customers", v2.id, v3.id,
        drift_type="type_changed",
        severity="critical",
        changes={
            "added_columns": [],
            "removed_columns": [],
            "type_changes": [{"name": "customer_id", "previous_type": "integer", "current_type": "string"}],
            "nullability_changes": [],
            "position_changes": []
        }
    )
    
    return {
        "versions": [v1, v2, v3],
        "drifts": [drift1, drift2]
    }


# Mock data generators
def generate_schema_with_columns(column_count: int, dataset_name: str = "test") -> Dict[str, Any]:
    """Generate a schema with specified number of columns
    
    Args:
        column_count: Number of columns to generate
        dataset_name: Name prefix for columns
        
    Returns:
        Schema definition dictionary
    """
    columns = []
    for i in range(column_count):
        columns.append({
            "name": f"{dataset_name}_col_{i}",
            "data_type": "string" if i % 2 == 0 else "integer",
            "nullable": i % 3 == 0,
            "position": i
        })
    
    return {"columns": columns}


def generate_drift_changes(
    added: int = 0,
    removed: int = 0,
    type_changed: int = 0,
    nullability_changed: int = 0
) -> Dict[str, List]:
    """Generate drift changes for testing
    
    Args:
        added: Number of added columns
        removed: Number of removed columns
        type_changed: Number of type changes
        nullability_changed: Number of nullability changes
        
    Returns:
        Changes dictionary
    """
    changes = {
        "added_columns": [{"name": f"added_col_{i}", "data_type": "string"} for i in range(added)],
        "removed_columns": [{"name": f"removed_col_{i}", "data_type": "string"} for i in range(removed)],
        "type_changes": [
            {"name": f"changed_col_{i}", "previous_type": "integer", "current_type": "string"}
            for i in range(type_changed)
        ],
        "nullability_changes": [
            {"name": f"null_col_{i}", "previous_nullable": False, "current_nullable": True}
            for i in range(nullability_changed)
        ],
        "position_changes": []
    }
    
    return changes
