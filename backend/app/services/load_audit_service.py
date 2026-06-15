"""Load Audit Service

Stores and manages batch execution audit logs for warehouse loads
"""
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from datetime import datetime, timedelta
import logging

from app.models.failed_load import LoadAuditLog, FailedLoad
from app.core.database import get_db

logger = logging.getLogger(__name__)


class LoadAuditService:
    """Service for managing load audit logs and tracking batch execution history"""
    
    def __init__(self, db: Session):
        """Initialize the load audit service
        
        Args:
            db: Database session
        """
        self.db = db
    
    def log_load_start(
        self,
        batch_id: str,
        dataset_name: str,
        source_system: Optional[str] = None,
        source_record_count: Optional[int] = None,
        triggered_by: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> LoadAuditLog:
        """Log the start of a batch load operation
        
        Args:
            batch_id: Unique identifier for the batch
            dataset_name: Name of the dataset being loaded
            source_system: System from which data originated
            source_record_count: Expected number of records from source
            triggered_by: User or system that triggered the load
            metadata: Additional context information
            
        Returns:
            Created LoadAuditLog instance
        """
        logger.info(f"Logging load start: batch_id={batch_id}, dataset={dataset_name}")
        
        audit_log = LoadAuditLog(
            batch_id=batch_id,
            dataset_name=dataset_name,
            source_system=source_system,
            load_status="started",
            load_started_at=datetime.utcnow(),
            source_record_count=source_record_count,
            triggered_by=triggered_by,
            metadata=metadata or {}
        )
        
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        
        logger.info(f"Load start logged: audit_log_id={audit_log.id}")
        return audit_log
    
    def log_load_completion(
        self,
        batch_id: str,
        warehouse_record_count: int,
        records_inserted: Optional[int] = None,
        records_updated: Optional[int] = None,
        records_failed: Optional[int] = None,
        notes: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> LoadAuditLog:
        """Log the successful completion of a batch load operation
        
        Args:
            batch_id: Unique identifier for the batch
            warehouse_record_count: Number of records loaded to warehouse
            records_inserted: Number of new records inserted
            records_updated: Number of existing records updated
            records_failed: Number of records that failed
            notes: Additional notes about the load
            metadata: Additional context information
            
        Returns:
            Updated LoadAuditLog instance
        """
        logger.info(f"Logging load completion: batch_id={batch_id}")
        
        # Find the most recent audit log for this batch
        audit_log = self.db.query(LoadAuditLog).filter(
            LoadAuditLog.batch_id == batch_id
        ).order_by(desc(LoadAuditLog.created_at)).first()
        
        if not audit_log:
            raise ValueError(f"No audit log found for batch_id: {batch_id}")
        
        # Calculate execution time
        execution_time = None
        if audit_log.load_started_at:
            execution_time = int((datetime.utcnow() - audit_log.load_started_at).total_seconds())
        
        # Update audit log
        audit_log.load_status = "completed"
        audit_log.load_completed_at = datetime.utcnow()
        audit_log.warehouse_record_count = warehouse_record_count
        audit_log.records_inserted = records_inserted
        audit_log.records_updated = records_updated
        audit_log.records_failed = records_failed
        audit_log.execution_time_seconds = execution_time
        audit_log.notes = notes
        
        if metadata:
            audit_log.metadata = {**(audit_log.metadata or {}), **metadata}
        
        self.db.commit()
        self.db.refresh(audit_log)
        
        logger.info(
            f"Load completion logged: batch_id={batch_id}, "
            f"warehouse_count={warehouse_record_count}, execution_time={execution_time}s"
        )
        return audit_log
    
    def log_load_failure(
        self,
        batch_id: str,
        failure_reason: str,
        error_message: Optional[str] = None,
        warehouse_record_count: Optional[int] = None,
        failed_record_count: Optional[int] = None,
        notes: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> tuple[LoadAuditLog, FailedLoad]:
        """Log a failed batch load operation
        
        Args:
            batch_id: Unique identifier for the batch
            failure_reason: Primary reason for failure
            error_message: Detailed error message or stack trace
            warehouse_record_count: Number of records successfully loaded before failure
            failed_record_count: Number of records that failed
            notes: Additional notes about the failure
            metadata: Additional context information
            
        Returns:
            Tuple of (updated LoadAuditLog, created FailedLoad)
        """
        logger.warning(f"Logging load failure: batch_id={batch_id}, reason={failure_reason}")
        
        # Find the most recent audit log for this batch
        audit_log = self.db.query(LoadAuditLog).filter(
            LoadAuditLog.batch_id == batch_id
        ).order_by(desc(LoadAuditLog.created_at)).first()
        
        if not audit_log:
            raise ValueError(f"No audit log found for batch_id: {batch_id}")
        
        # Calculate execution time
        execution_time = None
        if audit_log.load_started_at:
            execution_time = int((datetime.utcnow() - audit_log.load_started_at).total_seconds())
        
        # Update audit log
        audit_log.load_status = "failed"
        audit_log.load_completed_at = datetime.utcnow()
        audit_log.warehouse_record_count = warehouse_record_count
        audit_log.records_failed = failed_record_count
        audit_log.execution_time_seconds = execution_time
        audit_log.notes = notes
        
        if metadata:
            audit_log.metadata = {**(audit_log.metadata or {}), **metadata}
        
        # Create failed load record
        failed_load = FailedLoad(
            batch_id=batch_id,
            dataset_name=audit_log.dataset_name,
            source_system=audit_log.source_system,
            load_started_at=audit_log.load_started_at,
            load_failed_at=datetime.utcnow(),
            failure_reason=failure_reason,
            error_message=error_message,
            source_record_count=audit_log.source_record_count,
            warehouse_record_count=warehouse_record_count,
            failed_record_count=failed_record_count,
            retry_count=0,
            can_retry=False,  # Manual validation required before retry
            metadata=metadata or {}
        )
        
        self.db.add(failed_load)
        self.db.commit()
        self.db.refresh(audit_log)
        self.db.refresh(failed_load)
        
        logger.warning(
            f"Load failure logged: batch_id={batch_id}, failed_load_id={failed_load.id}"
        )
        return audit_log, failed_load
    
    def log_load_retry(
        self,
        batch_id: str,
        retry_count: int,
        triggered_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> LoadAuditLog:
        """Log a retry attempt for a failed batch load
        
        Args:
            batch_id: Unique identifier for the batch
            retry_count: Current retry attempt number
            triggered_by: User who initiated the retry
            notes: Additional notes about the retry
            
        Returns:
            Created LoadAuditLog instance for the retry
        """
        logger.info(f"Logging load retry: batch_id={batch_id}, retry_count={retry_count}")
        
        # Get original failed load
        failed_load = self.db.query(FailedLoad).filter(
            FailedLoad.batch_id == batch_id
        ).first()
        
        if not failed_load:
            raise ValueError(f"No failed load found for batch_id: {batch_id}")
        
        # Create new audit log for retry
        audit_log = LoadAuditLog(
            batch_id=batch_id,
            dataset_name=failed_load.dataset_name,
            source_system=failed_load.source_system,
            load_status="retrying",
            load_started_at=datetime.utcnow(),
            source_record_count=failed_load.source_record_count,
            triggered_by=triggered_by,
            notes=f"Retry attempt #{retry_count}. {notes or ''}",
            metadata={"retry_count": retry_count, "original_failure": failed_load.failure_reason}
        )
        
        self.db.add(audit_log)
        
        # Update failed load retry count
        failed_load.retry_count = retry_count
        failed_load.can_retry = False  # Reset after retry initiated
        
        self.db.commit()
        self.db.refresh(audit_log)
        
        logger.info(f"Load retry logged: audit_log_id={audit_log.id}")
        return audit_log
    
    def get_load_history(
        self,
        dataset_name: Optional[str] = None,
        status: Optional[str] = None,
        days: int = 7,
        limit: int = 100
    ) -> List[LoadAuditLog]:
        """Get load history with optional filters
        
        Args:
            dataset_name: Filter by dataset name
            status: Filter by load status
            days: Number of days to look back
            limit: Maximum number of records to return
            
        Returns:
            List of LoadAuditLog instances
        """
        query = self.db.query(LoadAuditLog)
        
        # Apply date filter
        since_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(LoadAuditLog.created_at >= since_date)
        
        # Apply optional filters
        if dataset_name:
            query = query.filter(LoadAuditLog.dataset_name == dataset_name)
        
        if status:
            query = query.filter(LoadAuditLog.load_status == status)
        
        # Order by most recent first
        query = query.order_by(desc(LoadAuditLog.created_at))
        
        return query.limit(limit).all()
    
    def get_load_statistics(
        self,
        dataset_name: Optional[str] = None,
        days: int = 7
    ) -> Dict:
        """Get load statistics and metrics
        
        Args:
            dataset_name: Optional filter by dataset name
            days: Number of days to analyze
            
        Returns:
            Dict containing load statistics
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(LoadAuditLog).filter(
            LoadAuditLog.created_at >= since_date
        )
        
        if dataset_name:
            query = query.filter(LoadAuditLog.dataset_name == dataset_name)
        
        total_loads = query.count()
        completed_loads = query.filter(LoadAuditLog.load_status == "completed").count()
        failed_loads = query.filter(LoadAuditLog.load_status == "failed").count()
        retrying_loads = query.filter(LoadAuditLog.load_status == "retrying").count()
        
        # Calculate average execution time for completed loads
        avg_exec_time = self.db.query(
            func.avg(LoadAuditLog.execution_time_seconds)
        ).filter(
            and_(
                LoadAuditLog.created_at >= since_date,
                LoadAuditLog.load_status == "completed"
            )
        )
        
        if dataset_name:
            avg_exec_time = avg_exec_time.filter(LoadAuditLog.dataset_name == dataset_name)
        
        avg_exec_time = avg_exec_time.scalar() or 0
        
        success_rate = (completed_loads / total_loads * 100) if total_loads > 0 else 0
        
        return {
            "total_loads": total_loads,
            "completed_loads": completed_loads,
            "failed_loads": failed_loads,
            "retrying_loads": retrying_loads,
            "success_rate": round(success_rate, 2),
            "average_execution_time_seconds": round(float(avg_exec_time), 2),
            "period_days": days,
            "dataset_name": dataset_name
        }
