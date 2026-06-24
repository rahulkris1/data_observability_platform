"""Schema Drift History ORM Model

Records schema drift events between versions
"""
from sqlalchemy import Column, String, Integer, JSON, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import BaseModel


class SchemaDriftHistory(BaseModel):
    """Schema Drift History model for tracking schema changes
    
    Attributes:
        dataset_name: Name of the dataset this drift event belongs to
        previous_version_id: ID of the previous schema version (null for first version)
        current_version_id: ID of the current schema version
        drift_type: Type of drift detected (column_added, column_removed, type_changed, nullability_changed, etc.)
        severity: Severity level (info, warning, critical)
        changes: JSON structure with detailed change information
            Format: {
                "added_columns": [...],
                "removed_columns": [...],
                "type_changes": [...],
                "nullability_changes": [...],
                "position_changes": [...]
            }
        detected_at: Timestamp when drift was detected
        acknowledged: Whether this drift has been acknowledged
        acknowledged_by: User who acknowledged the drift
        acknowledged_at: Timestamp when drift was acknowledged
        notes: Additional notes about the drift
    """
    __tablename__ = "schema_drift_history"
    
    dataset_name = Column(String(255), nullable=False, index=True)
    previous_version_id = Column(Integer, ForeignKey('schema_versions.id', ondelete='CASCADE'), nullable=True)
    current_version_id = Column(Integer, ForeignKey('schema_versions.id', ondelete='CASCADE'), nullable=False)
    drift_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False, index=True)
    changes = Column(JSON, nullable=False)
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    acknowledged = Column(Boolean, nullable=False, default=False, index=True)
    acknowledged_by = Column(String(255), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    previous_version = relationship(
        "SchemaVersion",
        foreign_keys=[previous_version_id],
        back_populates="drift_records_as_previous"
    )
    
    current_version = relationship(
        "SchemaVersion",
        foreign_keys=[current_version_id],
        back_populates="drift_records_as_current"
    )
    
    def __repr__(self) -> str:
        """String representation of the drift event"""
        return f"<SchemaDriftHistory(dataset={self.dataset_name}, type={self.drift_type}, severity={self.severity})>"
