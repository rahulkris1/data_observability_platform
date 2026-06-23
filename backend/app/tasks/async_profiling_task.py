"""
Async Celery tasks for data profiling and quality metrics.
"""
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.celery_app import celery_app


@celery_app.task(bind=True, name="profile_dataset_async")
def profile_dataset_async(
    self,
    dataset_name: str,
    bucket_name: str,
    object_name: str,
    profiled_by: str = 'system'
) -> Dict[str, Any]:
    """
    Asynchronously profile a dataset from MinIO storage and store results in PostgreSQL.
    
    Args:
        self: Task instance (injected by Celery)
        dataset_name: Name of the dataset to profile
        bucket_name: MinIO bucket name
        object_name: Object name in MinIO
        profiled_by: User or system initiating profiling
        
    Returns:
        Dictionary containing profiling results
    """
    import pandas as pd
    from app.services.dataset_profiling_service import get_profiling_service
    from app.storage.minio_client import minio_client
    
    start_time = time.time()
    
    # Update task state to running
    self.update_state(
        state="RUNNING",
        meta={
            "status": "running",
            "dataset": dataset_name,
            "started_at": datetime.utcnow().isoformat(),
        }
    )
    
    try:
        # Download dataset from MinIO
        self.update_state(
            state="RUNNING",
            meta={
                "status": "downloading",
                "dataset": dataset_name,
                "message": "Downloading dataset from storage",
            }
        )
        
        file_obj = minio_client.get_object(bucket_name, object_name)
        
        # Read into pandas DataFrame based on file type
        if object_name.endswith('.csv'):
            df = pd.read_csv(file_obj)
        elif object_name.endswith('.parquet'):
            df = pd.read_parquet(file_obj)
        elif object_name.endswith('.json'):
            df = pd.read_json(file_obj)
        else:
            raise ValueError(f"Unsupported file type: {object_name}")
        
        # Profile the dataset
        self.update_state(
            state="RUNNING",
            meta={
                "status": "profiling",
                "dataset": dataset_name,
                "message": "Calculating statistics",
            }
        )
        
        service = get_profiling_service()
        result = service.profile_dataset(
            df=df,
            dataset_name=dataset_name,
            profiled_by=profiled_by
        )
        
        execution_time = time.time() - start_time
        
        return {
            "status": "completed",
            "profiling_id": result.id,
            "dataset_name": result.dataset_name,
            "row_count": result.row_count,
            "column_count": result.column_count,
            "execution_time_seconds": execution_time,
            "profiled_at": result.created_at.isoformat() if result.created_at else None,
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        
        # Log the failed profiling
        try:
            from app.services.dataset_profiling_service import get_profiling_service
            from app.models.profiling_result import ProfilingResult
            from app.core.database import SessionLocal
            
            db = SessionLocal()
            failed_result = ProfilingResult(
                dataset_name=dataset_name,
                status='failed',
                execution_time_ms=execution_time * 1000,
                error_message=str(e),
                profiled_by=profiled_by
            )
            db.add(failed_result)
            db.commit()
            db.close()
        except Exception as log_error:
            print(f"Failed to log error: {log_error}")
        
        error_msg = f"Dataset profiling failed: {str(e)}"
        
        return {
            "status": "failed",
            "dataset": dataset_name,
            "error": error_msg,
            "execution_time": execution_time,
            "completed_at": datetime.utcnow().isoformat(),
        }


@celery_app.task(bind=True, name="calculate_data_quality_score")
def calculate_data_quality_score(
    self,
    dataset_name: str,
    validation_results: Dict[str, Any],
    profiling_results: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Calculate a comprehensive data quality score based on validation and profiling results.
    
    Args:
        self: Task instance (injected by Celery)
        dataset_name: Name of the dataset
        validation_results: Results from validation tasks
        profiling_results: Results from profiling tasks
        
    Returns:
        Dictionary containing quality score and breakdown
    """
    start_time = time.time()
    
    self.update_state(
        state="RUNNING",
        meta={
            "status": "running",
            "dataset": dataset_name,
            "started_at": datetime.utcnow().isoformat(),
        }
    )
    
    try:
        # Calculate validation score (40% weight)
        validation_score = 0
        if validation_results.get("total_rules", 0) > 0:
            validation_score = (
                validation_results.get("passed_rules", 0) / 
                validation_results["total_rules"] * 40
            )
        
        # Calculate completeness score (30% weight)
        completeness_score = 0
        if profiling_results.get("column_profiles"):
            avg_non_null_pct = sum(
                (cp["non_null_count"] / cp["total_rows"] * 100) if cp["total_rows"] > 0 else 0
                for cp in profiling_results["column_profiles"]
            ) / len(profiling_results["column_profiles"])
            completeness_score = avg_non_null_pct * 0.3
        
        # Calculate uniqueness score (30% weight)
        uniqueness_score = 0
        if profiling_results.get("column_profiles"):
            # Higher distinct percentage is better (but capped at 100%)
            avg_distinct_pct = min(
                sum(
                    cp["distinct_percentage"]
                    for cp in profiling_results["column_profiles"]
                ) / len(profiling_results["column_profiles"]),
                100
            )
            uniqueness_score = avg_distinct_pct * 0.3
        
        # Total quality score
        total_score = validation_score + completeness_score + uniqueness_score
        
        execution_time = time.time() - start_time
        
        return {
            "status": "completed",
            "dataset": dataset_name,
            "quality_score": round(total_score, 2),
            "breakdown": {
                "validation_score": round(validation_score, 2),
                "completeness_score": round(completeness_score, 2),
                "uniqueness_score": round(uniqueness_score, 2),
            },
            "grade": (
                "A" if total_score >= 90 else
                "B" if total_score >= 80 else
                "C" if total_score >= 70 else
                "D" if total_score >= 60 else
                "F"
            ),
            "execution_time": execution_time,
            "completed_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        
        return {
            "status": "failed",
            "dataset": dataset_name,
            "error": str(e),
            "execution_time": execution_time,
            "completed_at": datetime.utcnow().isoformat(),
        }


@celery_app.task(bind=True, name="generate_data_lineage")
def generate_data_lineage(
    self,
    dataset_name: str,
    upstream_datasets: List[str],
    transformations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Generate data lineage tracking for a dataset.
    
    Args:
        self: Task instance (injected by Celery)
        dataset_name: Name of the target dataset
        upstream_datasets: List of upstream source datasets
        transformations: List of transformation operations applied
        
    Returns:
        Dictionary containing lineage information
    """
    start_time = time.time()
    
    self.update_state(
        state="RUNNING",
        meta={
            "status": "running",
            "dataset": dataset_name,
            "started_at": datetime.utcnow().isoformat(),
        }
    )
    
    try:
        lineage = {
            "target_dataset": dataset_name,
            "upstream_datasets": upstream_datasets,
            "transformations": transformations,
            "generated_at": datetime.utcnow().isoformat(),
            "lineage_depth": len(upstream_datasets),
        }
        
        execution_time = time.time() - start_time
        
        return {
            "status": "completed",
            "lineage": lineage,
            "execution_time": execution_time,
            "completed_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        
        return {
            "status": "failed",
            "dataset": dataset_name,
            "error": str(e),
            "execution_time": execution_time,
            "completed_at": datetime.utcnow().isoformat(),
        }
