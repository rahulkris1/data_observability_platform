"""Warehouse Table ORM Models

Stores warehouse data and load execution history
"""
from sqlalchemy import Column, String, Integer, Text, JSON, DateTime, Float, Boolean
from datetime import datetime
from app.models.base import BaseModel


class WarehouseStagingData(BaseModel):
    """Warehouse Staging Data model for temporarily storing incoming data
    
    Attributes:
        dataset_name: Name of the source dataset
        batch_id: Unique identifier for the batch load
        source_system: System from which data originated
        raw_data: JSON structure containing the raw record
        record_hash: Hash of the record for deduplication
        is_processed: Flag indicating if record has been processed
        processed_at: Timestamp when record was processed
        error_message: Error message if processing failed
    """
    __tablename__ = "warehouse_staging_data"
    
    dataset_name = Column(String(255), nullable=False, index=True)
    batch_id = Column(String(100), nullable=False, index=True)
    source_system = Column(String(255), nullable=True)
    
    raw_data = Column(JSON, nullable=False)
    record_hash = Column(String(64), nullable=True, index=True)
    
    is_processed = Column(Boolean, default=False, nullable=False, index=True)
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    def __repr__(self) -> str:
        """String representation of the staging record"""
        return (
            f"<WarehouseStagingData(dataset={self.dataset_name}, "
            f"batch_id={self.batch_id}, processed={self.is_processed})>"
        )


class WarehouseProcessedData(BaseModel):
    """Warehouse Processed Data model for storing finalized data
    
    Attributes:
        dataset_name: Name of the dataset
        batch_id: Batch identifier this record belongs to
        source_system: System from which data originated
        source_record_id: Original record ID from source system
        data: JSON structure containing the processed record
        record_hash: Hash of the record for deduplication
        data_quality_score: Calculated quality score (0-100)
        validation_status: Status of validation ('passed', 'failed', 'warning')
        load_timestamp: Timestamp when record was loaded
        partition_key: Partition key for data organization
    """
    __tablename__ = "warehouse_processed_data"
    
    dataset_name = Column(String(255), nullable=False, index=True)
    batch_id = Column(String(100), nullable=False, index=True)
    source_system = Column(String(255), nullable=True)
    source_record_id = Column(String(255), nullable=True, index=True)
    
    data = Column(JSON, nullable=False)
    record_hash = Column(String(64), nullable=True, index=True, unique=True)
    
    data_quality_score = Column(Float, nullable=True)
    validation_status = Column(String(50), nullable=True, index=True)
    
    load_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    partition_key = Column(String(100), nullable=True, index=True)
    
    def __repr__(self) -> str:
        """String representation of the processed record"""
        return (
            f"<WarehouseProcessedData(dataset={self.dataset_name}, "
            f"batch_id={self.batch_id}, hash={self.record_hash[:8] if self.record_hash else None})>"
        )


class WarehouseLoadHistory(BaseModel):
    """Warehouse Load History model for tracking batch load executions
    
    Attributes:
        batch_id: Unique identifier for the batch load
        dataset_name: Name of the dataset being loaded
        source_system: System from which data originated
        load_type: Type of load ('initial', 'incremental', 'full_refresh')
        status: Load execution status ('running', 'completed', 'failed', 'rolled_back')
        records_attempted: Number of records attempted to load
        records_loaded: Number of records successfully loaded
        records_failed: Number of records that failed to load
        records_duplicate: Number of duplicate records skipped
        execution_duration_ms: Total execution time in milliseconds
        started_at: Timestamp when load started
        completed_at: Timestamp when load completed
        error_message: Error message if load failed
        error_details: JSON structure with detailed error information
        validation_summary: JSON structure with validation results
        metadata: JSON structure with additional metadata
    """
    __tablename__ = "warehouse_load_history"
    
    batch_id = Column(String(100), nullable=False, unique=True, index=True)
    dataset_name = Column(String(255), nullable=False, index=True)
    source_system = Column(String(255), nullable=True)
    load_type = Column(String(50), nullable=False, default='incremental', index=True)
    
    status = Column(String(50), nullable=False, default='running', index=True)
    
    records_attempted = Column(Integer, nullable=False, default=0)
    records_loaded = Column(Integer, nullable=False, default=0)
    records_failed = Column(Integer, nullable=False, default=0)
    records_duplicate = Column(Integer, nullable=False, default=0)
    
    execution_duration_ms = Column(Float, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    validation_summary = Column(JSON, nullable=True)
    load_metadata = Column(JSON, nullable=True)
    
    def __repr__(self) -> str:
        """String representation of the load history"""
        return (
            f"<WarehouseLoadHistory(batch_id={self.batch_id}, "
            f"dataset={self.dataset_name}, status={self.status}, "
            f"records_loaded={self.records_loaded})>"
        )
