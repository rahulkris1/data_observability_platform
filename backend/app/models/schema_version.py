"""Schema Version ORM Model

Stores different versions of dataset schemas for drift detection
"""
from sqlalchemy import Column, String, Integer, JSON, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import BaseModel


class SchemaVersion(BaseModel):
    """Schema Version model for tracking schema changes over time
    
    Attributes:
        dataset_name: Name of the dataset this schema version belongs to
        version_number: Sequential version number for this dataset
        version_hash: Hash of the schema definition for quick comparison
        schema_definition: JSON structure defining the schema
            Format: {
                "columns": [
                    {
                        "name": "column_name",
                        "data_type": "string|integer|float|boolean|date|timestamp",
                        "nullable": true|false,
                        "position": 0
                    },
                    ...
                ]
            }
        detected_at: Timestamp when this schema was detected
        source: Source of schema detection (e.g., 'ingestion', 'validation', 'manual')
        version_metadata: Additional metadata about the schema version
    """
    __tablename__ = "schema_versions"
    
    dataset_name = Column(String(255), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    version_hash = Column(String(64), nullable=False, index=True)
    schema_definition = Column(JSON, nullable=False)
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    source = Column(String(100), nullable=True)
    version_metadata = Column(JSON, nullable=True)
    
    # Relationship to drift history
    drift_records_as_current = relationship(
        "SchemaDriftHistory",
        foreign_keys="SchemaDriftHistory.current_version_id",
        back_populates="current_version",
        cascade="all, delete-orphan"
    )
    
    drift_records_as_previous = relationship(
        "SchemaDriftHistory",
        foreign_keys="SchemaDriftHistory.previous_version_id",
        back_populates="previous_version",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index('ix_schema_versions_dataset_version', 'dataset_name', 'version_number', unique=True),
    )
    
    def __repr__(self) -> str:
        """String representation of the schema version"""
        return f"<SchemaVersion(dataset={self.dataset_name}, version={self.version_number}, hash={self.version_hash[:8]})>"
