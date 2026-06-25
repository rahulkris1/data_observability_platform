"""
Async Celery tasks for calculating pipeline health scores.
"""
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.pipeline_health_service import PipelineHealthService


@celery_app.task(bind=True, name="calculate_pipeline_health_async")
def calculate_pipeline_health_async(
    self,
    pipeline_name: str,
    lookback_hours: int = 24
) -> Dict[str, Any]:
    """
    Asynchronously calculate health score for a pipeline.
    
    Args:
        self: Task instance (injected by Celery)
        pipeline_name: Name of the pipeline to score
        lookback_hours: Hours to look back for metric data
        
    Returns:
        Dictionary containing health score results
    """
    start_time = time.time()
    
    # Update task state to running
    self.update_state(
        state="RUNNING",
        meta={
            "status": "running",
            "pipeline": pipeline_name,
            "started_at": datetime.utcnow().isoformat(),
        }
    )
    
    db = SessionLocal()
    
    try:
        # Calculate health score
        service = PipelineHealthService(db)
        health_score = service.calculate_pipeline_health(
            pipeline_name=pipeline_name,
            lookback_hours=lookback_hours
        )
        
        execution_time = time.time() - start_time
        
        return {
            "status": "completed",
            "pipeline": pipeline_name,
            "health_score_id": health_score.id,
            "overall_score": health_score.overall_score,
            "validation_score": health_score.validation_score,
            "freshness_score": health_score.freshness_score,
            "latency_score": health_score.latency_score,
            "health_status": health_score.status,
            "timestamp": health_score.timestamp.isoformat(),
            "execution_time": execution_time,
            "completed_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        
        # Log the error
        error_msg = f"Health score calculation failed: {str(e)}"
        
        return {
            "status": "failed",
            "pipeline": pipeline_name,
            "error": error_msg,
            "execution_time": execution_time,
            "completed_at": datetime.utcnow().isoformat(),
        }
    
    finally:
        db.close()


@celery_app.task(bind=True, name="calculate_all_pipeline_health_async")
def calculate_all_pipeline_health_async(
    self,
    pipeline_names: List[str],
    lookback_hours: int = 24
) -> Dict[str, Any]:
    """
    Asynchronously calculate health scores for multiple pipelines.
    
    Args:
        self: Task instance (injected by Celery)
        pipeline_names: List of pipeline names to score
        lookback_hours: Hours to look back for metric data
        
    Returns:
        Dictionary containing batch results
    """
    start_time = time.time()
    
    # Update task state to running
    self.update_state(
        state="RUNNING",
        meta={
            "status": "running",
            "total_pipelines": len(pipeline_names),
            "started_at": datetime.utcnow().isoformat(),
        }
    )
    
    db = SessionLocal()
    results = []
    successful = 0
    failed = 0
    
    try:
        service = PipelineHealthService(db)
        
        for idx, pipeline_name in enumerate(pipeline_names):
            # Update progress
            self.update_state(
                state="RUNNING",
                meta={
                    "status": "running",
                    "current_pipeline": pipeline_name,
                    "progress": f"{idx + 1}/{len(pipeline_names)}",
                }
            )
            
            try:
                health_score = service.calculate_pipeline_health(
                    pipeline_name=pipeline_name,
                    lookback_hours=lookback_hours
                )
                
                results.append({
                    "pipeline": pipeline_name,
                    "success": True,
                    "health_score_id": health_score.id,
                    "overall_score": health_score.overall_score,
                    "status": health_score.status
                })
                successful += 1
                
            except Exception as e:
                results.append({
                    "pipeline": pipeline_name,
                    "success": False,
                    "error": str(e)
                })
                failed += 1
        
        execution_time = time.time() - start_time
        
        return {
            "status": "completed",
            "total_pipelines": len(pipeline_names),
            "successful": successful,
            "failed": failed,
            "results": results,
            "execution_time": execution_time,
            "completed_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        
        return {
            "status": "failed",
            "total_pipelines": len(pipeline_names),
            "error": str(e),
            "execution_time": execution_time,
            "completed_at": datetime.utcnow().isoformat(),
        }
    
    finally:
        db.close()
