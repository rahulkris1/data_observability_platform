"""Warehouse Audit Utility

Provides audit capabilities for warehouse loads:
- Load execution metadata tracking
- Record count tracking
- Failed record tracking
- Execution duration tracking
"""
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from app.models.warehouse_tables import WarehouseLoadHistory
from app.warehouse.warehouse_service import WarehouseWriteService

logger = logging.getLogger(__name__)


class WarehouseAuditLogger:
    """Utility for auditing warehouse load operations"""
    
    def __init__(self, db: Session):
        """Initialize warehouse audit logger
        
        Args:
            db: Database session
        """
        self.db = db
        self.write_service = WarehouseWriteService(db)
    
    def log_load_start(
        self,
        batch_id: str,
        dataset_name: str,
        source_system: Optional[str] = None,
        load_type: str = 'incremental',
        load_metadata: Optional[Dict[str, Any]] = None
    ) -> WarehouseLoadHistory:
        """Log the start of a warehouse load
        
        Args:
            batch_id: Unique batch identifier
            dataset_name: Name of the dataset
            source_system: Source system name
            load_type: Type of load
            load_metadata: Additional metadata
            
        Returns:
            Created load history record
        """
        logger.info(f"Starting warehouse load: batch_id={batch_id}, dataset={dataset_name}")
        
        return self.write_service.create_load_history(
            batch_id=batch_id,
            dataset_name=dataset_name,
            load_type=load_type,
            source_system=source_system,
            load_metadata=load_metadata
        )
    
    def log_load_completion(
        self,
        batch_id: str,
        records_attempted: int,
        records_loaded: int,
        records_failed: int,
        records_duplicate: int,
        execution_duration_ms: float,
        validation_summary: Optional[Dict[str, Any]] = None
    ) -> Optional[WarehouseLoadHistory]:
        """Log successful completion of a warehouse load
        
        Args:
            batch_id: Batch identifier
            records_attempted: Total number of records attempted
            records_loaded: Number of records successfully loaded
            records_failed: Number of records that failed
            records_duplicate: Number of duplicate records skipped
            execution_duration_ms: Execution time in milliseconds
            validation_summary: Summary of validation results
            
        Returns:
            Updated load history record
        """
        logger.info(
            f"Completing warehouse load: batch_id={batch_id}, "
            f"loaded={records_loaded}, failed={records_failed}, "
            f"duplicates={records_duplicate}, duration={execution_duration_ms}ms"
        )
        
        return self.write_service.update_load_history(
            batch_id=batch_id,
            status='completed',
            records_attempted=records_attempted,
            records_loaded=records_loaded,
            records_failed=records_failed,
            records_duplicate=records_duplicate,
            execution_duration_ms=execution_duration_ms,
            validation_summary=validation_summary
        )
    
    def log_load_failure(
        self,
        batch_id: str,
        records_attempted: int,
        records_loaded: int,
        records_failed: int,
        execution_duration_ms: float,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> Optional[WarehouseLoadHistory]:
        """Log failure of a warehouse load
        
        Args:
            batch_id: Batch identifier
            records_attempted: Total number of records attempted
            records_loaded: Number of records loaded before failure
            records_failed: Number of records that failed
            execution_duration_ms: Execution time in milliseconds
            error_message: Error message
            error_details: Detailed error information
            
        Returns:
            Updated load history record
        """
        logger.error(
            f"Warehouse load failed: batch_id={batch_id}, "
            f"error={error_message}, loaded={records_loaded}, failed={records_failed}"
        )
        
        return self.write_service.update_load_history(
            batch_id=batch_id,
            status='failed',
            records_attempted=records_attempted,
            records_loaded=records_loaded,
            records_failed=records_failed,
            execution_duration_ms=execution_duration_ms,
            error_message=error_message,
            error_details=error_details
        )
    
    def log_load_rollback(
        self,
        batch_id: str,
        reason: str,
        rollback_details: Optional[Dict[str, Any]] = None
    ) -> Optional[WarehouseLoadHistory]:
        """Log rollback of a warehouse load
        
        Args:
            batch_id: Batch identifier
            reason: Reason for rollback
            rollback_details: Details about the rollback operation
            
        Returns:
            Updated load history record
        """
        logger.warning(f"Rolling back warehouse load: batch_id={batch_id}, reason={reason}")
        
        return self.write_service.update_load_history(
            batch_id=batch_id,
            status='rolled_back',
            error_message=reason,
            error_details=rollback_details
        )
    
    def get_load_audit(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get audit information for a specific load
        
        Args:
            batch_id: Batch identifier
            
        Returns:
            Dictionary containing audit information
        """
        load_history = self.db.query(WarehouseLoadHistory).filter(
            WarehouseLoadHistory.batch_id == batch_id
        ).first()
        
        if not load_history:
            return None
        
        return {
            'batch_id': load_history.batch_id,
            'dataset_name': load_history.dataset_name,
            'source_system': load_history.source_system,
            'load_type': load_history.load_type,
            'status': load_history.status,
            'records_attempted': load_history.records_attempted,
            'records_loaded': load_history.records_loaded,
            'records_failed': load_history.records_failed,
            'records_duplicate': load_history.records_duplicate,
            'execution_duration_ms': load_history.execution_duration_ms,
            'started_at': load_history.started_at,
            'completed_at': load_history.completed_at,
            'error_message': load_history.error_message,
            'error_details': load_history.error_details,
            'validation_summary': load_history.validation_summary,
            'load_metadata': load_history.load_metadata
        }
    
    def get_dataset_load_summary(self, dataset_name: str) -> Dict[str, Any]:
        """Get summary of all loads for a dataset
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            Dictionary containing load summary
        """
        loads = self.db.query(WarehouseLoadHistory).filter(
            WarehouseLoadHistory.dataset_name == dataset_name
        ).all()
        
        total_loads = len(loads)
        completed_loads = sum(1 for load in loads if load.status == 'completed')
        failed_loads = sum(1 for load in loads if load.status == 'failed')
        total_records_loaded = sum(load.records_loaded for load in loads)
        total_records_failed = sum(load.records_failed for load in loads)
        
        return {
            'dataset_name': dataset_name,
            'total_loads': total_loads,
            'completed_loads': completed_loads,
            'failed_loads': failed_loads,
            'total_records_loaded': total_records_loaded,
            'total_records_failed': total_records_failed,
            'success_rate': (completed_loads / total_loads * 100) if total_loads > 0 else 0
        }


# Backward compatibility alias
AuditLogger = WarehouseAuditLogger
