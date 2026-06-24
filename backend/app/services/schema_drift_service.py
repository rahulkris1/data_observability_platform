"""Schema Drift Detection Service

Provides functionality for detecting, tracking, and analyzing schema drift
"""
import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.models.schema_version import SchemaVersion
from app.models.schema_drift_history import SchemaDriftHistory


class SchemaDriftService:
    """Service for detecting and managing schema drift"""
    
    def __init__(self, db: Session):
        """Initialize the schema drift service
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    @staticmethod
    def _normalize_schema(schema_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize schema definition for consistent hashing
        
        Args:
            schema_definition: Raw schema definition
            
        Returns:
            Normalized schema definition
        """
        # Sort columns by name for consistent comparison
        columns = schema_definition.get("columns", [])
        normalized_columns = sorted(columns, key=lambda x: x["name"])
        
        # Add position to each column
        for idx, col in enumerate(normalized_columns):
            col["position"] = idx
        
        return {"columns": normalized_columns}
    
    @staticmethod
    def _calculate_schema_hash(schema_definition: Dict[str, Any]) -> str:
        """Calculate hash of schema definition
        
        Args:
            schema_definition: Schema definition to hash
            
        Returns:
            SHA-256 hash of the schema
        """
        # Normalize and convert to JSON string
        normalized = SchemaDriftService._normalize_schema(schema_definition)
        schema_str = json.dumps(normalized, sort_keys=True)
        
        # Calculate hash
        return hashlib.sha256(schema_str.encode()).hexdigest()
    
    def get_latest_version(self, dataset_name: str) -> Optional[SchemaVersion]:
        """Get the latest schema version for a dataset
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            Latest SchemaVersion or None if no versions exist
        """
        return self.db.query(SchemaVersion).filter(
            SchemaVersion.dataset_name == dataset_name
        ).order_by(desc(SchemaVersion.version_number)).first()
    
    def get_version_by_number(self, dataset_name: str, version_number: int) -> Optional[SchemaVersion]:
        """Get a specific schema version
        
        Args:
            dataset_name: Name of the dataset
            version_number: Version number to retrieve
            
        Returns:
            SchemaVersion or None if not found
        """
        return self.db.query(SchemaVersion).filter(
            and_(
                SchemaVersion.dataset_name == dataset_name,
                SchemaVersion.version_number == version_number
            )
        ).first()
    
    def get_all_versions(self, dataset_name: str, limit: int = 100) -> List[SchemaVersion]:
        """Get all schema versions for a dataset
        
        Args:
            dataset_name: Name of the dataset
            limit: Maximum number of versions to return
            
        Returns:
            List of SchemaVersion objects ordered by version number descending
        """
        return self.db.query(SchemaVersion).filter(
            SchemaVersion.dataset_name == dataset_name
        ).order_by(desc(SchemaVersion.version_number)).limit(limit).all()
    
    def register_schema(
        self, 
        dataset_name: str, 
        schema_definition: Dict[str, Any],
        source: str = "ingestion",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[SchemaVersion, Optional[SchemaDriftHistory]]:
        """Register a new schema version and detect drift
        
        Args:
            dataset_name: Name of the dataset
            schema_definition: Schema definition to register
            source: Source of the schema (e.g., 'ingestion', 'validation', 'manual')
            metadata: Additional metadata
            
        Returns:
            Tuple of (SchemaVersion, SchemaDriftHistory or None)
        """
        # Normalize and hash the schema
        normalized_schema = self._normalize_schema(schema_definition)
        schema_hash = self._calculate_schema_hash(normalized_schema)
        
        # Check if this schema already exists
        latest_version = self.get_latest_version(dataset_name)
        
        if latest_version and latest_version.version_hash == schema_hash:
            # No drift detected - same schema
            return latest_version, None
        
        # Create new version
        new_version_number = 1 if not latest_version else latest_version.version_number + 1
        
        new_version = SchemaVersion(
            dataset_name=dataset_name,
            version_number=new_version_number,
            version_hash=schema_hash,
            schema_definition=normalized_schema,
            detected_at=datetime.utcnow(),
            source=source,
            metadata=metadata
        )
        
        self.db.add(new_version)
        self.db.flush()  # Flush to get the ID
        
        # Detect drift if there was a previous version
        drift_record = None
        if latest_version:
            drift_record = self._detect_drift(latest_version, new_version)
            if drift_record:
                self.db.add(drift_record)
        
        self.db.commit()
        self.db.refresh(new_version)
        
        return new_version, drift_record
    
    def _detect_drift(
        self, 
        previous_version: SchemaVersion, 
        current_version: SchemaVersion
    ) -> Optional[SchemaDriftHistory]:
        """Detect drift between two schema versions
        
        Args:
            previous_version: Previous schema version
            current_version: Current schema version
            
        Returns:
            SchemaDriftHistory object or None if no drift
        """
        prev_columns = {col["name"]: col for col in previous_version.schema_definition["columns"]}
        curr_columns = {col["name"]: col for col in current_version.schema_definition["columns"]}
        
        changes = {
            "added_columns": [],
            "removed_columns": [],
            "type_changes": [],
            "nullability_changes": [],
            "position_changes": []
        }
        
        # Detect added columns
        for col_name, col_def in curr_columns.items():
            if col_name not in prev_columns:
                changes["added_columns"].append({
                    "name": col_name,
                    "data_type": col_def.get("data_type"),
                    "nullable": col_def.get("nullable"),
                    "position": col_def.get("position")
                })
        
        # Detect removed columns
        for col_name, col_def in prev_columns.items():
            if col_name not in curr_columns:
                changes["removed_columns"].append({
                    "name": col_name,
                    "data_type": col_def.get("data_type"),
                    "nullable": col_def.get("nullable"),
                    "position": col_def.get("position")
                })
        
        # Detect type and nullability changes
        for col_name in set(prev_columns.keys()) & set(curr_columns.keys()):
            prev_col = prev_columns[col_name]
            curr_col = curr_columns[col_name]
            
            # Type changes
            if prev_col.get("data_type") != curr_col.get("data_type"):
                changes["type_changes"].append({
                    "name": col_name,
                    "previous_type": prev_col.get("data_type"),
                    "current_type": curr_col.get("data_type")
                })
            
            # Nullability changes
            if prev_col.get("nullable") != curr_col.get("nullable"):
                changes["nullability_changes"].append({
                    "name": col_name,
                    "previous_nullable": prev_col.get("nullable"),
                    "current_nullable": curr_col.get("nullable")
                })
            
            # Position changes
            if prev_col.get("position") != curr_col.get("position"):
                changes["position_changes"].append({
                    "name": col_name,
                    "previous_position": prev_col.get("position"),
                    "current_position": curr_col.get("position")
                })
        
        # Determine drift type and severity
        drift_type, severity = self._categorize_drift(changes)
        
        if drift_type == "no_drift":
            return None
        
        return SchemaDriftHistory(
            dataset_name=current_version.dataset_name,
            previous_version_id=previous_version.id,
            current_version_id=current_version.id,
            drift_type=drift_type,
            severity=severity,
            changes=changes,
            detected_at=datetime.utcnow(),
            acknowledged=False
        )
    
    @staticmethod
    def _categorize_drift(changes: Dict[str, List]) -> Tuple[str, str]:
        """Categorize drift type and severity
        
        Args:
            changes: Dictionary of detected changes
            
        Returns:
            Tuple of (drift_type, severity)
        """
        # Determine primary drift type
        if changes["removed_columns"]:
            drift_type = "column_removed"
            severity = "critical"
        elif changes["type_changes"]:
            drift_type = "type_changed"
            severity = "critical"
        elif changes["nullability_changes"]:
            # Check if nullable became non-nullable (breaking change)
            has_breaking_nullability = any(
                not change["previous_nullable"] and change["current_nullable"]
                for change in changes["nullability_changes"]
            )
            drift_type = "nullability_changed"
            severity = "warning" if has_breaking_nullability else "info"
        elif changes["added_columns"]:
            drift_type = "column_added"
            severity = "info"
        elif changes["position_changes"]:
            drift_type = "position_changed"
            severity = "info"
        else:
            drift_type = "no_drift"
            severity = "info"
        
        return drift_type, severity
    
    def get_drift_history(
        self, 
        dataset_name: Optional[str] = None,
        severity: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 100
    ) -> List[SchemaDriftHistory]:
        """Get drift history with optional filters
        
        Args:
            dataset_name: Filter by dataset name
            severity: Filter by severity (info, warning, critical)
            acknowledged: Filter by acknowledged status
            limit: Maximum number of records to return
            
        Returns:
            List of SchemaDriftHistory objects
        """
        query = self.db.query(SchemaDriftHistory)
        
        if dataset_name:
            query = query.filter(SchemaDriftHistory.dataset_name == dataset_name)
        
        if severity:
            query = query.filter(SchemaDriftHistory.severity == severity)
        
        if acknowledged is not None:
            query = query.filter(SchemaDriftHistory.acknowledged == acknowledged)
        
        return query.order_by(desc(SchemaDriftHistory.detected_at)).limit(limit).all()
    
    def acknowledge_drift(
        self, 
        drift_id: int, 
        acknowledged_by: str,
        notes: Optional[str] = None
    ) -> SchemaDriftHistory:
        """Acknowledge a drift event
        
        Args:
            drift_id: ID of the drift record
            acknowledged_by: User acknowledging the drift
            notes: Optional notes about the acknowledgment
            
        Returns:
            Updated SchemaDriftHistory object
        """
        drift = self.db.query(SchemaDriftHistory).filter(
            SchemaDriftHistory.id == drift_id
        ).first()
        
        if not drift:
            raise ValueError(f"Drift record {drift_id} not found")
        
        drift.acknowledged = True
        drift.acknowledged_by = acknowledged_by
        drift.acknowledged_at = datetime.utcnow()
        if notes:
            drift.notes = notes
        
        self.db.commit()
        self.db.refresh(drift)
        
        return drift
    
    def compare_schemas(
        self, 
        dataset_name: str, 
        version1: int, 
        version2: int
    ) -> Dict[str, Any]:
        """Compare two schema versions
        
        Args:
            dataset_name: Name of the dataset
            version1: First version number
            version2: Second version number
            
        Returns:
            Dictionary with comparison results
        """
        v1 = self.get_version_by_number(dataset_name, version1)
        v2 = self.get_version_by_number(dataset_name, version2)
        
        if not v1 or not v2:
            raise ValueError("One or both versions not found")
        
        # Use the drift detection logic for comparison
        drift = self._detect_drift(v1, v2)
        
        return {
            "dataset_name": dataset_name,
            "version1": version1,
            "version2": version2,
            "version1_detected_at": v1.detected_at.isoformat(),
            "version2_detected_at": v2.detected_at.isoformat(),
            "has_drift": drift is not None,
            "drift_type": drift.drift_type if drift else None,
            "severity": drift.severity if drift else None,
            "changes": drift.changes if drift else {}
        }
