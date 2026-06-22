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
    dataset_path: str,
    dataset_name: str,
    columns: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Asynchronously profile a dataset and generate quality metrics.
    
    Args:
        self: Task instance (injected by Celery)
        dataset_path: Path to the dataset file
        dataset_name: Name of the dataset
        columns: Optional list of specific columns to profile
        
    Returns:
        Dictionary containing profiling results
    """
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
        from pyspark.sql import SparkSession
        from pyspark.sql.functions import col, count, countDistinct, mean, stddev, min as spark_min, max as spark_max
        
        # Initialize Spark session
        spark = SparkSession.builder.appName("DataProfiling").getOrCreate()
        
        # Load dataset
        df = spark.read.csv(dataset_path, header=True, inferSchema=True)
        
        total_rows = df.count()
        
        # Profile each column
        column_profiles = []
        columns_to_profile = columns if columns else df.columns
        
        for col_name in columns_to_profile:
            # Update progress
            self.update_state(
                state="RUNNING",
                meta={
                    "status": "running",
                    "current_column": col_name,
                    "progress": f"{len(column_profiles)}/{len(columns_to_profile)}",
                }
            )
            
            # Calculate statistics
            stats = df.select(
                count(col(col_name)).alias("non_null_count"),
                countDistinct(col(col_name)).alias("distinct_count"),
            ).collect()[0]
            
            non_null_count = stats["non_null_count"]
            distinct_count = stats["distinct_count"]
            null_count = total_rows - non_null_count
            null_percentage = (null_count / total_rows * 100) if total_rows > 0 else 0
            
            profile = {
                "column_name": col_name,
                "data_type": str(df.schema[col_name].dataType),
                "total_rows": total_rows,
                "non_null_count": non_null_count,
                "null_count": null_count,
                "null_percentage": round(null_percentage, 2),
                "distinct_count": distinct_count,
                "distinct_percentage": round((distinct_count / total_rows * 100) if total_rows > 0 else 0, 2),
            }
            
            # Add numeric statistics if applicable
            if df.schema[col_name].dataType.typeName() in ["integer", "long", "float", "double"]:
                numeric_stats = df.select(
                    mean(col(col_name)).alias("mean"),
                    stddev(col(col_name)).alias("stddev"),
                    spark_min(col(col_name)).alias("min"),
                    spark_max(col(col_name)).alias("max"),
                ).collect()[0]
                
                profile.update({
                    "mean": round(numeric_stats["mean"], 2) if numeric_stats["mean"] else None,
                    "stddev": round(numeric_stats["stddev"], 2) if numeric_stats["stddev"] else None,
                    "min": numeric_stats["min"],
                    "max": numeric_stats["max"],
                })
            
            column_profiles.append(profile)
        
        execution_time = time.time() - start_time
        
        return {
            "status": "completed",
            "dataset": dataset_name,
            "total_rows": total_rows,
            "total_columns": len(columns_to_profile),
            "column_profiles": column_profiles,
            "execution_time": execution_time,
            "completed_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        
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
