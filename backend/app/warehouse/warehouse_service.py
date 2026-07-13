"""Warehouse Service for data warehouse read/write operations

Provides services for:
- Reading warehouse data
- Writing data to warehouse
- Querying warehouse statistics
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
import logging

from app.models.warehouse_tables import (
    WarehouseStagingData,
    WarehouseProcessedData,
    WarehouseLoadHistory
)

logger = logging.getLogger(__name__)


class WarehouseService:
    """Unified Warehouse Service combining read and write operations"""
    
    def __init__(self, db: Session):
        """Initialize warehouse service
        
        Args:
            db: Database session
        """
        self.db = db
        self.read_service = WarehouseReadService(db)
        self.write_service = WarehouseWriteService(db)
    
    def __getattr__(self, name):
        """Delegate method calls to read or write service"""
        if hasattr(self.read_service, name):
            return getattr(self.read_service, name)
        elif hasattr(self.write_service, name):
            return getattr(self.write_service, name)
        raise AttributeError(f"WarehouseService has no attribute '{name}'")


class WarehouseReadService:
    """Service for reading data from the warehouse"""
    
    def __init__(self, db: Session):
        """Initialize warehouse read service
        
        Args:
            db: Database session
        """
        self.db = db
    
    def get_processed_data(
        self,
        dataset_name: Optional[str] = None,
        batch_id: Optional[str] = None,
        validation_status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[WarehouseProcessedData]:
        """Get processed warehouse data with filters
        
        Args:
            dataset_name: Filter by dataset name
            batch_id: Filter by batch ID
            validation_status: Filter by validation status
            start_date: Filter records from this date
            end_date: Filter records until this date
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of processed warehouse records
        """
        query = self.db.query(WarehouseProcessedData)
        
        if dataset_name:
            query = query.filter(WarehouseProcessedData.dataset_name == dataset_name)
        
        if batch_id:
            query = query.filter(WarehouseProcessedData.batch_id == batch_id)
        
        if validation_status:
            query = query.filter(WarehouseProcessedData.validation_status == validation_status)
        
        if start_date:
            query = query.filter(WarehouseProcessedData.load_timestamp >= start_date)
        
        if end_date:
            query = query.filter(WarehouseProcessedData.load_timestamp <= end_date)
        
        return query.order_by(desc(WarehouseProcessedData.load_timestamp)).limit(limit).offset(offset).all()
    
    def get_load_history(
        self,
        dataset_name: Optional[str] = None,
        status: Optional[str] = None,
        load_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[WarehouseLoadHistory]:
        """Get warehouse load execution history with filters
        
        Args:
            dataset_name: Filter by dataset name
            status: Filter by load status
            load_type: Filter by load type
            start_date: Filter loads from this date
            end_date: Filter loads until this date
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of load history records
        """
        query = self.db.query(WarehouseLoadHistory)
        
        if dataset_name:
            query = query.filter(WarehouseLoadHistory.dataset_name == dataset_name)
        
        if status:
            query = query.filter(WarehouseLoadHistory.status == status)
        
        if load_type:
            query = query.filter(WarehouseLoadHistory.load_type == load_type)
        
        if start_date:
            query = query.filter(WarehouseLoadHistory.started_at >= start_date)
        
        if end_date:
            query = query.filter(WarehouseLoadHistory.started_at <= end_date)
        
        return query.order_by(desc(WarehouseLoadHistory.started_at)).limit(limit).offset(offset).all()
    
    def get_warehouse_statistics(self) -> Dict[str, Any]:
        """Get overall warehouse statistics
        
        Returns:
            Dictionary containing warehouse metrics
        """
        total_records = self.db.query(func.count(WarehouseProcessedData.id)).scalar() or 0
        
        # Get record counts by dataset
        records_by_dataset = (
            self.db.query(
                WarehouseProcessedData.dataset_name,
                func.count(WarehouseProcessedData.id).label('count')
            )
            .group_by(WarehouseProcessedData.dataset_name)
            .all()
        )
        
        # Get load statistics
        total_loads = self.db.query(func.count(WarehouseLoadHistory.id)).scalar() or 0
        successful_loads = (
            self.db.query(func.count(WarehouseLoadHistory.id))
            .filter(WarehouseLoadHistory.status == 'completed')
            .scalar() or 0
        )
        failed_loads = (
            self.db.query(func.count(WarehouseLoadHistory.id))
            .filter(WarehouseLoadHistory.status == 'failed')
            .scalar() or 0
        )
        
        # Get latest load timestamp
        latest_load = (
            self.db.query(WarehouseLoadHistory)
            .order_by(desc(WarehouseLoadHistory.started_at))
            .first()
        )
        
        return {
            "total_records": total_records,
            "records_by_dataset": {name: count for name, count in records_by_dataset},
            "total_loads": total_loads,
            "successful_loads": successful_loads,
            "failed_loads": failed_loads,
            "latest_load_timestamp": latest_load.started_at if latest_load else None,
            "latest_load_status": latest_load.status if latest_load else None
        }
    
    def get_load_by_batch_id(self, batch_id: str) -> Optional[WarehouseLoadHistory]:
        """Get load history by batch ID
        
        Args:
            batch_id: Batch identifier
            
        Returns:
            Load history record or None
        """
        return self.db.query(WarehouseLoadHistory).filter(
            WarehouseLoadHistory.batch_id == batch_id
        ).first()
    
    def get_dataset_health(self, dataset_name: str) -> Dict[str, Any]:
        """Get health metrics for a specific dataset
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            Dictionary containing dataset health metrics
        """
        total_records = (
            self.db.query(func.count(WarehouseProcessedData.id))
            .filter(WarehouseProcessedData.dataset_name == dataset_name)
            .scalar() or 0
        )
        
        # Get validation status distribution
        validation_stats = (
            self.db.query(
                WarehouseProcessedData.validation_status,
                func.count(WarehouseProcessedData.id).label('count')
            )
            .filter(WarehouseProcessedData.dataset_name == dataset_name)
            .group_by(WarehouseProcessedData.validation_status)
            .all()
        )
        
        # Get latest load for this dataset
        latest_load = (
            self.db.query(WarehouseLoadHistory)
            .filter(WarehouseLoadHistory.dataset_name == dataset_name)
            .order_by(desc(WarehouseLoadHistory.started_at))
            .first()
        )
        
        return {
            "dataset_name": dataset_name,
            "total_records": total_records,
            "validation_status_distribution": {status: count for status, count in validation_stats},
            "latest_load_timestamp": latest_load.started_at if latest_load else None,
            "latest_load_status": latest_load.status if latest_load else None,
            "latest_records_loaded": latest_load.records_loaded if latest_load else 0
        }


class WarehouseWriteService:
    """Service for writing data to the warehouse"""
    
    def __init__(self, db: Session):
        """Initialize warehouse write service
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create_staging_records(
        self,
        records: List[Dict[str, Any]],
        dataset_name: str,
        batch_id: str,
        source_system: Optional[str] = None
    ) -> int:
        """Create staging records for batch processing
        
        Args:
            records: List of raw data records
            dataset_name: Name of the dataset
            batch_id: Unique batch identifier
            source_system: Source system name
            
        Returns:
            Number of records created
        """
        staging_records = []
        for record in records:
            staging_record = WarehouseStagingData(
                dataset_name=dataset_name,
                batch_id=batch_id,
                source_system=source_system,
                raw_data=record,
                is_processed=False
            )
            staging_records.append(staging_record)
        
        self.db.bulk_save_objects(staging_records)
        self.db.commit()
        
        logger.info(f"Created {len(staging_records)} staging records for batch {batch_id}")
        return len(staging_records)
    
    def create_processed_records(
        self,
        records: List[Dict[str, Any]],
        dataset_name: str,
        batch_id: str,
        source_system: Optional[str] = None
    ) -> int:
        """Create processed warehouse records
        
        Args:
            records: List of processed data records
            dataset_name: Name of the dataset
            batch_id: Unique batch identifier
            source_system: Source system name
            
        Returns:
            Number of records created
        """
        processed_records = []
        for record in records:
            processed_record = WarehouseProcessedData(
                dataset_name=dataset_name,
                batch_id=batch_id,
                source_system=source_system,
                data=record.get('data', record),
                source_record_id=record.get('id'),
                record_hash=record.get('record_hash'),
                data_quality_score=record.get('data_quality_score'),
                validation_status=record.get('validation_status', 'passed'),
                load_timestamp=datetime.utcnow(),
                partition_key=record.get('partition_key')
            )
            processed_records.append(processed_record)
        
        self.db.bulk_save_objects(processed_records)
        self.db.commit()
        
        logger.info(f"Created {len(processed_records)} processed records for batch {batch_id}")
        return len(processed_records)
    
    def create_load_history(
        self,
        batch_id: str,
        dataset_name: str,
        load_type: str = 'incremental',
        source_system: Optional[str] = None,
        load_metadata: Optional[Dict[str, Any]] = None
    ) -> WarehouseLoadHistory:
        """Create a new load history record
        
        Args:
            batch_id: Unique batch identifier
            dataset_name: Name of the dataset
            load_type: Type of load (incremental, full_refresh, initial)
            source_system: Source system name
            load_metadata: Additional metadata
            
        Returns:
            Created load history record
        """
        load_history = WarehouseLoadHistory(
            batch_id=batch_id,
            dataset_name=dataset_name,
            source_system=source_system,
            load_type=load_type,
            status='running',
            records_attempted=0,
            records_loaded=0,
            records_failed=0,
            records_duplicate=0,
            started_at=datetime.utcnow(),
            load_metadata=load_metadata
        )
        
        self.db.add(load_history)
        self.db.commit()
        self.db.refresh(load_history)
        
        logger.info(f"Created load history for batch {batch_id}")
        return load_history
    
    def update_load_history(
        self,
        batch_id: str,
        status: Optional[str] = None,
        records_attempted: Optional[int] = None,
        records_loaded: Optional[int] = None,
        records_failed: Optional[int] = None,
        records_duplicate: Optional[int] = None,
        error_message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        validation_summary: Optional[Dict[str, Any]] = None,
        execution_duration_ms: Optional[float] = None
    ) -> Optional[WarehouseLoadHistory]:
        """Update load history record
        
        Args:
            batch_id: Batch identifier
            status: Load status
            records_attempted: Number of records attempted
            records_loaded: Number of records loaded
            records_failed: Number of records failed
            records_duplicate: Number of duplicate records
            error_message: Error message if failed
            error_details: Detailed error information
            validation_summary: Validation results summary
            execution_duration_ms: Execution duration in milliseconds
            
        Returns:
            Updated load history record or None
        """
        load_history = self.db.query(WarehouseLoadHistory).filter(
            WarehouseLoadHistory.batch_id == batch_id
        ).first()
        
        if not load_history:
            logger.warning(f"Load history not found for batch {batch_id}")
            return None
        
        if status:
            load_history.status = status
        if records_attempted is not None:
            load_history.records_attempted = records_attempted
        if records_loaded is not None:
            load_history.records_loaded = records_loaded
        if records_failed is not None:
            load_history.records_failed = records_failed
        if records_duplicate is not None:
            load_history.records_duplicate = records_duplicate
        if error_message:
            load_history.error_message = error_message
        if error_details:
            load_history.error_details = error_details
        if validation_summary:
            load_history.validation_summary = validation_summary
        if execution_duration_ms is not None:
            load_history.execution_duration_ms = execution_duration_ms
        
        if status in ['completed', 'failed', 'rolled_back']:
            load_history.completed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(load_history)
        
        logger.info(f"Updated load history for batch {batch_id}: status={status}")
        return load_history
    
    def delete_staging_batch(self, batch_id: str) -> int:
        """Delete staging records for a batch
        
        Args:
            batch_id: Batch identifier
            
        Returns:
            Number of records deleted
        """
        deleted_count = self.db.query(WarehouseStagingData).filter(
            WarehouseStagingData.batch_id == batch_id
        ).delete()
        
        self.db.commit()
        
        logger.info(f"Deleted {deleted_count} staging records for batch {batch_id}")
        return deleted_count
