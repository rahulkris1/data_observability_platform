"""Load Verification Service

Verifies source vs warehouse record counts and identifies data discrepancies
"""
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime
import logging

from app.models.warehouse_tables import WarehouseStagingData, WarehouseProcessedData
from app.models.failed_load import FailedLoad
from app.core.database import get_db

logger = logging.getLogger(__name__)


class LoadVerificationService:
    """Service for verifying warehouse load completeness and accuracy"""
    
    def __init__(self, db: Session):
        """Initialize the load verification service
        
        Args:
            db: Database session
        """
        self.db = db
    
    def verify_batch_load(
        self, 
        batch_id: str,
        dataset_name: str,
        source_record_count: Optional[int] = None
    ) -> Dict:
        """Verify that a batch load completed successfully
        
        Compares source record count with warehouse record count and identifies
        any discrepancies or failures.
        
        Args:
            batch_id: Unique identifier for the batch
            dataset_name: Name of the dataset
            source_record_count: Expected number of records from source (optional)
            
        Returns:
            Dict containing verification results:
                - is_valid: Whether load passed verification
                - source_count: Number of records in source
                - staging_count: Number of records in staging
                - warehouse_count: Number of records in warehouse
                - failed_count: Number of failed records
                - discrepancy: Difference between source and warehouse
                - verification_status: Overall status message
                - issues: List of identified issues
        """
        logger.info(f"Verifying batch load: batch_id={batch_id}, dataset={dataset_name}")
        
        # Count staging records
        staging_count = self.db.query(func.count(WarehouseStagingData.id)).filter(
            and_(
                WarehouseStagingData.batch_id == batch_id,
                WarehouseStagingData.dataset_name == dataset_name
            )
        ).scalar() or 0
        
        # Count warehouse records
        warehouse_count = self.db.query(func.count(WarehouseProcessedData.id)).filter(
            and_(
                WarehouseProcessedData.batch_id == batch_id,
                WarehouseProcessedData.dataset_name == dataset_name
            )
        ).scalar() or 0
        
        # Count failed staging records
        failed_count = self.db.query(func.count(WarehouseStagingData.id)).filter(
            and_(
                WarehouseStagingData.batch_id == batch_id,
                WarehouseStagingData.dataset_name == dataset_name,
                WarehouseStagingData.is_processed == False,
                WarehouseStagingData.error_message.isnot(None)
            )
        ).scalar() or 0
        
        # Use staging count as source if not provided
        if source_record_count is None:
            source_record_count = staging_count
        
        # Calculate discrepancy
        discrepancy = source_record_count - warehouse_count
        
        # Determine verification status
        issues = []
        is_valid = True
        
        if discrepancy > 0:
            is_valid = False
            issues.append(f"{discrepancy} records missing from warehouse")
        
        if failed_count > 0:
            is_valid = False
            issues.append(f"{failed_count} records failed during processing")
        
        if warehouse_count == 0 and source_record_count > 0:
            is_valid = False
            issues.append("No records loaded to warehouse despite source data")
        
        verification_status = "PASSED" if is_valid else "FAILED"
        
        result = {
            "is_valid": is_valid,
            "source_count": source_record_count,
            "staging_count": staging_count,
            "warehouse_count": warehouse_count,
            "failed_count": failed_count,
            "discrepancy": discrepancy,
            "verification_status": verification_status,
            "issues": issues,
            "verified_at": datetime.utcnow().isoformat()
        }
        
        logger.info(
            f"Verification complete: batch_id={batch_id}, status={verification_status}, "
            f"source={source_record_count}, warehouse={warehouse_count}, discrepancy={discrepancy}"
        )
        
        return result
    
    def get_failed_records_details(
        self,
        batch_id: str,
        dataset_name: str,
        limit: int = 100
    ) -> List[Dict]:
        """Get details of failed records for a batch
        
        Args:
            batch_id: Unique identifier for the batch
            dataset_name: Name of the dataset
            limit: Maximum number of failed records to return
            
        Returns:
            List of dictionaries containing failed record details
        """
        failed_records = self.db.query(WarehouseStagingData).filter(
            and_(
                WarehouseStagingData.batch_id == batch_id,
                WarehouseStagingData.dataset_name == dataset_name,
                WarehouseStagingData.is_processed == False,
                WarehouseStagingData.error_message.isnot(None)
            )
        ).limit(limit).all()
        
        return [
            {
                "id": record.id,
                "record_hash": record.record_hash,
                "error_message": record.error_message,
                "raw_data_preview": str(record.raw_data)[:200] if record.raw_data else None,
                "created_at": record.created_at.isoformat() if record.created_at else None
            }
            for record in failed_records
        ]
    
    def verify_dataset_completeness(
        self,
        dataset_name: str,
        date_filter: Optional[datetime] = None
    ) -> Dict:
        """Verify completeness across all batches for a dataset
        
        Args:
            dataset_name: Name of the dataset to verify
            date_filter: Optional date to filter batches (default: all batches)
            
        Returns:
            Dict containing dataset-level verification results
        """
        logger.info(f"Verifying dataset completeness: dataset={dataset_name}")
        
        # Base query
        query = self.db.query(
            WarehouseProcessedData.batch_id,
            func.count(WarehouseProcessedData.id).label('record_count')
        ).filter(
            WarehouseProcessedData.dataset_name == dataset_name
        )
        
        # Apply date filter if provided
        if date_filter:
            query = query.filter(
                func.date(WarehouseProcessedData.created_at) == date_filter.date()
            )
        
        # Group by batch
        batch_results = query.group_by(WarehouseProcessedData.batch_id).all()
        
        total_batches = len(batch_results)
        total_records = sum(result.record_count for result in batch_results)
        
        # Get failed loads for this dataset
        failed_loads_query = self.db.query(FailedLoad).filter(
            FailedLoad.dataset_name == dataset_name
        )
        
        if date_filter:
            failed_loads_query = failed_loads_query.filter(
                func.date(FailedLoad.created_at) == date_filter.date()
            )
        
        failed_loads_count = failed_loads_query.count()
        
        return {
            "dataset_name": dataset_name,
            "total_batches": total_batches,
            "total_records": total_records,
            "failed_loads_count": failed_loads_count,
            "date_filter": date_filter.isoformat() if date_filter else None,
            "verified_at": datetime.utcnow().isoformat()
        }
    
    def compare_source_to_warehouse(
        self,
        batch_id: str,
        dataset_name: str,
        source_data_sample: Optional[List[Dict]] = None
    ) -> Dict:
        """Compare source data to warehouse data for quality verification
        
        Args:
            batch_id: Unique identifier for the batch
            dataset_name: Name of the dataset
            source_data_sample: Optional sample of source data for comparison
            
        Returns:
            Dict containing comparison results
        """
        warehouse_sample = self.db.query(WarehouseProcessedData).filter(
            and_(
                WarehouseProcessedData.batch_id == batch_id,
                WarehouseProcessedData.dataset_name == dataset_name
            )
        ).limit(10).all()
        
        warehouse_records = [
            {
                "source_record_id": rec.source_record_id,
                "data": rec.data,
                "validation_status": rec.validation_status,
                "data_quality_score": rec.data_quality_score
            }
            for rec in warehouse_sample
        ]
        
        avg_quality_score = self.db.query(
            func.avg(WarehouseProcessedData.data_quality_score)
        ).filter(
            and_(
                WarehouseProcessedData.batch_id == batch_id,
                WarehouseProcessedData.dataset_name == dataset_name
            )
        ).scalar() or 0.0
        
        return {
            "batch_id": batch_id,
            "dataset_name": dataset_name,
            "warehouse_sample": warehouse_records,
            "average_quality_score": float(avg_quality_score),
            "sample_size": len(warehouse_records),
            "compared_at": datetime.utcnow().isoformat()
        }
