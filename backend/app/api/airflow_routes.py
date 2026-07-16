"""
Airflow API Routes
Endpoints for Airflow monitoring and management
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from app.services.airflow_service import AirflowService, AirflowHealth, DAGInfo, DAGRun

router = APIRouter(prefix="/airflow", tags=["airflow"])

# Initialize Airflow service
airflow_service = AirflowService()


@router.get("/health", response_model=Dict[str, Any])
async def get_airflow_health():
    """Get Airflow health status"""
    health = airflow_service.get_health()
    if not health:
        raise HTTPException(status_code=503, detail="Unable to connect to Airflow")
    
    return {
        "metadatabase": health.metadatabase,
        "scheduler": health.scheduler,
        "triggerer": health.triggerer,
        "is_healthy": health.metadatabase == "healthy" and health.scheduler == "healthy"
    }


@router.get("/version")
async def get_airflow_version():
    """Get Airflow version"""
    version = airflow_service.get_version()
    if not version:
        raise HTTPException(status_code=503, detail="Unable to get Airflow version")
    
    return {"version": version}


@router.get("/scheduler/health")
async def get_scheduler_health():
    """Get detailed scheduler health"""
    health = airflow_service.get_scheduler_health()
    return health


@router.get("/statistics")
async def get_airflow_statistics():
    """Get Airflow statistics"""
    stats = airflow_service.get_statistics()
    return stats


@router.get("/dags", response_model=List[DAGInfo])
async def list_dags(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0)
):
    """List all DAGs"""
    dags = airflow_service.list_dags(limit=limit, offset=offset)
    return dags


@router.get("/dags/{dag_id}", response_model=DAGInfo)
async def get_dag(dag_id: str):
    """Get specific DAG information"""
    dag = airflow_service.get_dag(dag_id)
    if not dag:
        raise HTTPException(status_code=404, detail=f"DAG {dag_id} not found")
    return dag


@router.get("/dags/{dag_id}/runs", response_model=List[DAGRun])
async def list_dag_runs(
    dag_id: str,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    state: Optional[str] = None
):
    """List DAG runs for a specific DAG"""
    runs = airflow_service.list_dag_runs(
        dag_id=dag_id,
        limit=limit,
        offset=offset,
        state=state
    )
    return runs


@router.post("/dags/{dag_id}/trigger", response_model=DAGRun)
async def trigger_dag(
    dag_id: str,
    conf: Optional[Dict] = None
):
    """Trigger a DAG run"""
    run = airflow_service.trigger_dag(dag_id=dag_id, conf=conf)
    if not run:
        raise HTTPException(status_code=400, detail=f"Failed to trigger DAG {dag_id}")
    return run


@router.patch("/dags/{dag_id}/pause")
async def pause_dag(dag_id: str):
    """Pause a DAG"""
    success = airflow_service.pause_dag(dag_id)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to pause DAG {dag_id}")
    return {"message": f"DAG {dag_id} paused successfully"}


@router.patch("/dags/{dag_id}/unpause")
async def unpause_dag(dag_id: str):
    """Unpause a DAG"""
    success = airflow_service.unpause_dag(dag_id)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to unpause DAG {dag_id}")
    return {"message": f"DAG {dag_id} unpaused successfully"}


@router.get("/pipelines/summary")
async def get_pipeline_summary():
    """Get pipeline summary statistics"""
    dags = airflow_service.list_dags(limit=1000)
    
    total = len(dags)
    active = sum(1 for dag in dags if dag.is_active and not dag.is_paused)
    paused = sum(1 for dag in dags if dag.is_paused)
    
    # Get recent runs for active DAGs
    recent_runs = []
    for dag in dags[:10]:  # Check recent runs for first 10 DAGs
        runs = airflow_service.list_dag_runs(dag.dag_id, limit=5)
        recent_runs.extend(runs)
    
    # Count runs by state
    success_count = sum(1 for run in recent_runs if run.state == "success")
    failed_count = sum(1 for run in recent_runs if run.state == "failed")
    running_count = sum(1 for run in recent_runs if run.state == "running")
    
    return {
        "total_pipelines": total,
        "active_pipelines": active,
        "paused_pipelines": paused,
        "recent_runs": {
            "success": success_count,
            "failed": failed_count,
            "running": running_count,
            "total": len(recent_runs)
        }
    }
