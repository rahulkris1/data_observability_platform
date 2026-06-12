"""Batch Loader for warehouse data loading

Provides batch loading capabilities with:
- Configurable batch sizes
- Transaction management
- Rollback handling
- Error recovery
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
import hashlib
import json
import uuid
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.warehouse_tables import (
    WarehouseStagingData,
    WarehouseProcessedData,
    WarehouseLoadHistory
)
from app.warehouse.warehouse_service import WarehouseWriteService

logger = logging.getLogger(__name__)


class BatchLoaderConfig:
    """Configuration for batch loader"""
    
    def __init__(
        self,
        batch_size: int = 1000,
        enable_deduplication: bool = True,
        skip_duplicates: bool = True,
        enable_validation: bool = True,
        enable_staging: bool = False
    ):
        """Initialize batch loader configuration
        
        Args:
            batch_size: Number of records to process in each batch
            enable_deduplication: Enable duplicate detection using hash
            skip_duplicates: Skip duplicate records instead of failing
            enable_validation: Enable pre-insert validation
            enable_staging: Use staging table before final load
        """
        self.batch_size = batch_size
        self.enable_deduplication = enable_deduplication
        self.skip_duplicates = skip_duplicates
        self.enable_validation = enable_validation
        self.enable_staging = enable_staging


class BatchLoader:
    """Batch loader for warehouse data with transaction management"""
    
    def __init__(
        self,
        db: Session,
        config: Optional[BatchLoaderConfig] = None
    ):
        """Initialize batch loader
        
        Args:
            db: Database session
            config: Batch loader configuration
        """
        self.db = db
        self.config = config or BatchLoaderConfig()
        self.write_service = WarehouseWriteService(db)
    
    def _generate_batch_id(self) -> str:
        """Generate unique batch ID
        
        Returns:
            Unique batch identifier
        """
        return f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    def _calculate_record_hash(self, record: Dict[str, Any]) -> str:
        """Calculate hash for a record to detect duplicates
        
        Args:
            record: Data record
            
        Returns:
            SHA-256 hash of the record
        """
        # Create a stable string representation of the record
        record_str = json.dumps(record, sort_keys=True)
        return hashlib.sha256(record_str.encode()).hexdigest()
    
    def _check_duplicate(self, record_hash: str) -> bool:
        """Check if a record with this hash already exists
        
        Args:
            record_hash: Hash of the record
            
        Returns:
            True if duplicate exists, False otherwise
        """
        existing = self.db.query(WarehouseProcessedData).filter(
            WarehouseProcessedData.record_hash == record_hash
        ).first()
        return existing is not None
    
    def _process_batch(
        self,
        batch_records: List[Dict[str, Any]],
        dataset_name: str,
        batch_id: str,
        source_system: Optional[str] = None
    ) -> Tuple[int, int, int, List[str]]:
        """Process a single batch of records
        
        Args:
            batch_records: List of records to process
            dataset_name: Name of the dataset
            batch_id: Batch identifier
            source_system: Source system name
            
        Returns:
            Tuple of (loaded_count, duplicate_count, failed_count, error_messages)
        """
        loaded_count = 0
        duplicate_count = 0
        failed_count = 0
        error_messages = []
        
        processed_records = []
        
        for idx, record in enumerate(batch_records):
            try:
                # Calculate record hash for deduplication
                record_hash = None
                if self.config.enable_deduplication:
                    record_hash = self._calculate_record_hash(record)
                    
                    # Check for duplicates
                    if self._check_duplicate(record_hash):
                        duplicate_count += 1
                        if self.config.skip_duplicates:
                            logger.debug(f"Skipping duplicate record with hash {record_hash[:8]}")
                            continue
                        else:
                            error_messages.append(f"Duplicate record at index {idx}: hash {record_hash[:8]}")
                            failed_count += 1
                            continue
                
                # Create processed record
                processed_record = WarehouseProcessedData(
                    dataset_name=dataset_name,
                    batch_id=batch_id,
                    source_system=source_system,
                    data=record,
                    source_record_id=record.get('id'),
                    record_hash=record_hash,
                    data_quality_score=record.get('_quality_score'),
                    validation_status=record.get('_validation_status', 'passed'),
                    load_timestamp=datetime.utcnow(),
                    partition_key=record.get('_partition_key')
                )
                
                processed_records.append(processed_record)
                loaded_count += 1
                
            except Exception as e:
                failed_count += 1
                error_msg = f"Failed to process record at index {idx}: {str(e)}"
                error_messages.append(error_msg)
                logger.error(error_msg)
        
        # Bulk insert processed records
        if processed_records:
            try:
                self.db.bulk_save_objects(processed_records)
                self.db.flush()  # Flush but don't commit yet
            except IntegrityError as e:
                # Handle constraint violations
                error_msg = f"Integrity error during batch insert: {str(e)}"
                error_messages.append(error_msg)
                logger.error(error_msg)
                raise
        
        return loaded_count, duplicate_count, failed_count, error_messages
    
    def load_batch(
        self,
        records: List[Dict[str, Any]],
        dataset_name: str,
        source_system: Optional[str] = None,
        load_type: str = 'incremental',
        load_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Load a batch of records to the warehouse with transaction management
        
        Args:
            records: List of records to load
            dataset_name: Name of the dataset
            source_system: Source system name
            load_type: Type of load (incremental, full_refresh, initial)
            load_metadata: Additional metadata
            
        Returns:
            Dictionary containing load results
        """
        batch_id = self._generate_batch_id()
        start_time = datetime.utcnow()
        
        # Create load history record
        load_history = self.write_service.create_load_history(
            batch_id=batch_id,
            dataset_name=dataset_name,
            load_type=load_type,
            source_system=source_system,
            load_metadata=load_metadata
        )
        
        total_loaded = 0
        total_duplicates = 0
        total_failed = 0
        all_errors = []
        
        try:
            # Process records in batches
            for i in range(0, len(records), self.config.batch_size):
                batch_records = records[i:i + self.config.batch_size]
                batch_num = (i // self.config.batch_size) + 1
                
                logger.info(
                    f"Processing batch {batch_num} ({len(batch_records)} records) "
                    f"for dataset {dataset_name}"
                )
                
                loaded, duplicates, failed, errors = self._process_batch(
                    batch_records=batch_records,
                    dataset_name=dataset_name,
                    batch_id=batch_id,
                    source_system=source_system
                )
                
                total_loaded += loaded
                total_duplicates += duplicates
                total_failed += failed
                all_errors.extend(errors)
            
            # Commit the transaction if successful
            self.db.commit()
            
            # Calculate execution duration
            end_time = datetime.utcnow()
            execution_duration_ms = (end_time - start_time).total_seconds() * 1000
            
            # Update load history with success
            self.write_service.update_load_history(
                batch_id=batch_id,
                status='completed',
                records_attempted=len(records),
                records_loaded=total_loaded,
                records_failed=total_failed,
                records_duplicate=total_duplicates,
                execution_duration_ms=execution_duration_ms,
                validation_summary={
                    'total_records': len(records),
                    'loaded': total_loaded,
                    'duplicates': total_duplicates,
                    'failed': total_failed,
                    'success_rate': (total_loaded / len(records) * 100) if records else 0
                }
            )
            
            logger.info(
                f"Batch load completed for {dataset_name}: "
                f"loaded={total_loaded}, duplicates={total_duplicates}, failed={total_failed}"
            )
            
            return {
                'batch_id': batch_id,
                'status': 'completed',
                'dataset_name': dataset_name,
                'records_attempted': len(records),
                'records_loaded': total_loaded,
                'records_duplicate': total_duplicates,
                'records_failed': total_failed,
                'execution_duration_ms': execution_duration_ms,
                'errors': all_errors[:100],  # Limit error messages
                'load_timestamp': end_time
            }
            
        except Exception as e:
            # Rollback on error
            self.db.rollback()
            
            error_message = f"Batch load failed for {dataset_name}: {str(e)}"
            logger.error(error_message, exc_info=True)
            
            # Calculate execution duration
            end_time = datetime.utcnow()
            execution_duration_ms = (end_time - start_time).total_seconds() * 1000
            
            # Update load history with failure
            self.write_service.update_load_history(
                batch_id=batch_id,
                status='failed',
                records_attempted=len(records),
                records_loaded=total_loaded,
                records_failed=len(records) - total_loaded,
                records_duplicate=total_duplicates,
                execution_duration_ms=execution_duration_ms,
                error_message=error_message,
                error_details={
                    'exception_type': type(e).__name__,
                    'exception_message': str(e),
                    'errors': all_errors[:100]
                }
            )
            
            return {
                'batch_id': batch_id,
                'status': 'failed',
                'dataset_name': dataset_name,
                'records_attempted': len(records),
                'records_loaded': total_loaded,
                'records_duplicate': total_duplicates,
                'records_failed': len(records) - total_loaded,
                'execution_duration_ms': execution_duration_ms,
                'error_message': error_message,
                'errors': all_errors[:100],
                'load_timestamp': end_time
            }
    
    def rollback_batch(self, batch_id: str) -> Dict[str, Any]:
        """Rollback a batch load by deleting loaded records
        
        Args:
            batch_id: Batch identifier to rollback
            
        Returns:
            Dictionary containing rollback results
        """
        try:
            # Delete processed records for this batch
            deleted_count = self.db.query(WarehouseProcessedData).filter(
                WarehouseProcessedData.batch_id == batch_id
            ).delete()
            
            self.db.commit()
            
            # Update load history
            self.write_service.update_load_history(
                batch_id=batch_id,
                status='rolled_back',
                error_message='Batch manually rolled back'
            )
            
            logger.info(f"Rolled back batch {batch_id}: deleted {deleted_count} records")
            
            return {
                'batch_id': batch_id,
                'status': 'rolled_back',
                'records_deleted': deleted_count
            }
            
        except Exception as e:
            self.db.rollback()
            error_message = f"Failed to rollback batch {batch_id}: {str(e)}"
            logger.error(error_message, exc_info=True)
            
            return {
                'batch_id': batch_id,
                'status': 'rollback_failed',
                'error_message': error_message
            }
