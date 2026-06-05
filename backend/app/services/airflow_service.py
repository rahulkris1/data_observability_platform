"""
Airflow Service
Handles interaction with Airflow REST API
"""
from typing import Dict, List, Optional
import requests
from datetime import datetime
from pydantic import BaseModel


class AirflowHealth(BaseModel):
    """Airflow health status"""
    metadatabase: str
    scheduler: str
    triggerer: Optional[str] = None


class DAGInfo(BaseModel):
    """DAG information"""
    dag_id: str
    is_paused: bool
    is_active: bool
    last_parsed_time: Optional[str] = None
    tags: List[str] = []


class DAGRun(BaseModel):
    """DAG run information"""
    dag_run_id: str
    dag_id: str
    execution_date: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    state: str
    external_trigger: bool


class AirflowService:
    """Service for Airflow API interactions"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        username: str = "admin",
        password: str = "admin123"
    ):
        self.base_url = base_url.rstrip('/')
        self.auth = (username, password)
        self.session = requests.Session()
        self.session.auth = self.auth
    
    def get_health(self) -> Optional[AirflowHealth]:
        """Get Airflow health status"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/health",
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            
            return AirflowHealth(
                metadatabase=data.get("metadatabase", {}).get("status", "unknown"),
                scheduler=data.get("scheduler", {}).get("status", "unknown"),
                triggerer=data.get("triggerer", {}).get("status")
            )
        except Exception as e:
            print(f"Error getting Airflow health: {e}")
            return None
    
    def get_version(self) -> Optional[str]:
        """Get Airflow version"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/version",
                timeout=5
            )
            response.raise_for_status()
            return response.json().get("version")
        except Exception as e:
            print(f"Error getting Airflow version: {e}")
            return None
    
    def list_dags(self, limit: int = 100, offset: int = 0) -> List[DAGInfo]:
        """List all DAGs"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/dags",
                params={"limit": limit, "offset": offset},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            dags = []
            for dag_data in data.get("dags", []):
                dags.append(DAGInfo(
                    dag_id=dag_data["dag_id"],
                    is_paused=dag_data.get("is_paused", False),
                    is_active=dag_data.get("is_active", False),
                    last_parsed_time=dag_data.get("last_parsed_time"),
                    tags=[tag["name"] for tag in dag_data.get("tags", [])]
                ))
            
            return dags
        except Exception as e:
            print(f"Error listing DAGs: {e}")
            return []
    
    def get_dag(self, dag_id: str) -> Optional[DAGInfo]:
        """Get specific DAG information"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/dags/{dag_id}",
                timeout=5
            )
            response.raise_for_status()
            dag_data = response.json()
            
            return DAGInfo(
                dag_id=dag_data["dag_id"],
                is_paused=dag_data.get("is_paused", False),
                is_active=dag_data.get("is_active", False),
                last_parsed_time=dag_data.get("last_parsed_time"),
                tags=[tag["name"] for tag in dag_data.get("tags", [])]
            )
        except Exception as e:
            print(f"Error getting DAG {dag_id}: {e}")
            return None
    
    def list_dag_runs(
        self,
        dag_id: str,
        limit: int = 25,
        offset: int = 0,
        state: Optional[str] = None
    ) -> List[DAGRun]:
        """List DAG runs for a specific DAG"""
        try:
            params = {"limit": limit, "offset": offset}
            if state:
                params["state"] = state
            
            response = self.session.get(
                f"{self.base_url}/api/v1/dags/{dag_id}/dagRuns",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            dag_runs = []
            for run_data in data.get("dag_runs", []):
                dag_runs.append(DAGRun(
                    dag_run_id=run_data["dag_run_id"],
                    dag_id=run_data["dag_id"],
                    execution_date=run_data["execution_date"],
                    start_date=run_data.get("start_date"),
                    end_date=run_data.get("end_date"),
                    state=run_data.get("state", "unknown"),
                    external_trigger=run_data.get("external_trigger", False)
                ))
            
            return dag_runs
        except Exception as e:
            print(f"Error listing DAG runs for {dag_id}: {e}")
            return []
    
    def trigger_dag(
        self,
        dag_id: str,
        conf: Optional[Dict] = None,
        execution_date: Optional[str] = None
    ) -> Optional[DAGRun]:
        """Trigger a DAG run"""
        try:
            payload = {}
            if conf:
                payload["conf"] = conf
            if execution_date:
                payload["execution_date"] = execution_date
            
            response = self.session.post(
                f"{self.base_url}/api/v1/dags/{dag_id}/dagRuns",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            run_data = response.json()
            
            return DAGRun(
                dag_run_id=run_data["dag_run_id"],
                dag_id=run_data["dag_id"],
                execution_date=run_data["execution_date"],
                start_date=run_data.get("start_date"),
                end_date=run_data.get("end_date"),
                state=run_data.get("state", "unknown"),
                external_trigger=run_data.get("external_trigger", False)
            )
        except Exception as e:
            print(f"Error triggering DAG {dag_id}: {e}")
            return None
    
    def pause_dag(self, dag_id: str) -> bool:
        """Pause a DAG"""
        try:
            response = self.session.patch(
                f"{self.base_url}/api/v1/dags/{dag_id}",
                json={"is_paused": True},
                timeout=5
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error pausing DAG {dag_id}: {e}")
            return False
    
    def unpause_dag(self, dag_id: str) -> bool:
        """Unpause a DAG"""
        try:
            response = self.session.patch(
                f"{self.base_url}/api/v1/dags/{dag_id}",
                json={"is_paused": False},
                timeout=5
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error unpausing DAG {dag_id}: {e}")
            return False
    
    def get_scheduler_health(self) -> Dict[str, any]:
        """Get detailed scheduler health information"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/health",
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            
            scheduler = data.get("scheduler", {})
            return {
                "status": scheduler.get("status", "unknown"),
                "latest_heartbeat": scheduler.get("latest_scheduler_heartbeat"),
                "is_healthy": scheduler.get("status") == "healthy"
            }
        except Exception as e:
            print(f"Error getting scheduler health: {e}")
            return {
                "status": "error",
                "latest_heartbeat": None,
                "is_healthy": False,
                "error": str(e)
            }
    
    def get_statistics(self) -> Dict[str, any]:
        """Get Airflow statistics"""
        try:
            # Get DAG count
            dags_response = self.session.get(
                f"{self.base_url}/api/v1/dags",
                params={"limit": 1},
                timeout=5
            )
            dags_response.raise_for_status()
            total_dags = dags_response.json().get("total_entries", 0)
            
            # Get health
            health = self.get_health()
            
            return {
                "total_dags": total_dags,
                "scheduler_healthy": health.scheduler == "healthy" if health else False,
                "database_healthy": health.metadatabase == "healthy" if health else False,
                "version": self.get_version()
            }
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {
                "total_dags": 0,
                "scheduler_healthy": False,
                "database_healthy": False,
                "version": None,
                "error": str(e)
            }
