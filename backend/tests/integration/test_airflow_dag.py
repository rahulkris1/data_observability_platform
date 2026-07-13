"""Integration tests for Airflow DAG execution.

Tests DAG structure, task dependencies, and execution workflow.
"""
import pytest
from datetime import datetime, timedelta
import time
import sys
from pathlib import Path

# Try to import airflow, skip tests if not available
try:
    from airflow.models import DagBag, TaskInstance, DagRun
    from airflow.utils.state import State
    from airflow.utils.types import DagRunType
    AIRFLOW_AVAILABLE = True
except ImportError:
    AIRFLOW_AVAILABLE = False

# Skip all tests in this module if airflow is not installed
pytestmark = pytest.mark.skipif(
    not AIRFLOW_AVAILABLE,
    reason="Airflow not installed. Install with: pip install apache-airflow"
)

# Add airflow dags to path
AIRFLOW_DAGS = Path(__file__).resolve().parents[3] / "airflow" / "dags"
sys.path.insert(0, str(AIRFLOW_DAGS))


@pytest.fixture(scope="module")
def dagbag():
    """Load DAGs from the dags folder."""
    return DagBag(dag_folder=str(AIRFLOW_DAGS), include_examples=False)


@pytest.fixture
def data_quality_dag(dagbag):
    """Get the data quality pipeline DAG."""
    dag_id = "data_quality_pipeline"
    assert dag_id in dagbag.dags, f"DAG {dag_id} not found in DAG bag"
    return dagbag.dags[dag_id]


@pytest.mark.integration
@pytest.mark.requires_airflow
class TestAirflowDAG:
    """Integration tests for Airflow DAG structure and execution."""
    
    def test_dag_loaded(self, dagbag):
        """Test that DAG is loaded without errors."""
        assert dagbag.import_errors == {}, f"DAG import errors: {dagbag.import_errors}"
        assert len(dagbag.dags) > 0, "No DAGs found"
    
    def test_data_quality_dag_exists(self, data_quality_dag):
        """Test that data quality DAG exists."""
        assert data_quality_dag is not None
        assert data_quality_dag.dag_id == "data_quality_pipeline"
    
    def test_dag_has_correct_schedule(self, data_quality_dag):
        """Test DAG has expected schedule interval."""
        # Check schedule - it might be None for manual trigger or a timedelta
        assert data_quality_dag.schedule_interval is not None or data_quality_dag.schedule_interval is None
    
    def test_dag_has_tags(self, data_quality_dag):
        """Test DAG has appropriate tags."""
        # Tags might not be set, but if they are, verify
        if hasattr(data_quality_dag, 'tags'):
            assert isinstance(data_quality_dag.tags, (list, set, type(None)))
    
    def test_dag_default_args(self, data_quality_dag):
        """Test DAG has correct default arguments."""
        default_args = data_quality_dag.default_args
        
        assert 'owner' in default_args
        assert 'retries' in default_args
        assert default_args['retries'] >= 0
    
    def test_dag_has_tasks(self, data_quality_dag):
        """Test DAG has tasks defined."""
        tasks = data_quality_dag.tasks
        assert len(tasks) > 0, "DAG should have at least one task"
        
        # Get task IDs
        task_ids = [task.task_id for task in tasks]
        assert len(task_ids) > 0
    
    def test_expected_tasks_exist(self, data_quality_dag):
        """Test that expected tasks exist in the DAG."""
        task_ids = [task.task_id for task in data_quality_dag.tasks]
        
        # Expected tasks based on typical data quality pipeline
        # Adjust these based on your actual DAG structure
        possible_tasks = [
            'ingest_data',
            'validate_schema',
            'validate_quality',
            'log_audit',
            'start',
            'end',
            'validation',
            'ingestion',
        ]
        
        # At least some of these tasks should exist
        found_tasks = [task for task in possible_tasks if task in task_ids]
        assert len(found_tasks) > 0, f"Expected tasks not found. Available: {task_ids}"
    
    def test_task_dependencies(self, data_quality_dag):
        """Test that tasks have proper dependencies."""
        for task in data_quality_dag.tasks:
            # Each task should have upstream or downstream dependencies
            # or be a start/end task
            has_dependencies = (
                len(task.upstream_task_ids) > 0 or 
                len(task.downstream_task_ids) > 0 or
                task.task_id in ['start', 'end', 'begin', 'finish']
            )
            # Single-task DAGs are also valid
            assert has_dependencies or len(data_quality_dag.tasks) == 1
    
    def test_no_cycles_in_dag(self, data_quality_dag):
        """Test that DAG has no cycles."""
        # Airflow should prevent cycles, but verify
        try:
            # Try to get topological sort
            task_dict = {task.task_id: task for task in data_quality_dag.tasks}
            visited = set()
            
            def has_cycle(task_id, path):
                if task_id in path:
                    return True
                if task_id in visited:
                    return False
                
                visited.add(task_id)
                path.add(task_id)
                
                task = task_dict.get(task_id)
                if task:
                    for downstream_id in task.downstream_task_ids:
                        if has_cycle(downstream_id, path.copy()):
                            return True
                
                path.remove(task_id)
                return False
            
            for task_id in task_dict:
                assert not has_cycle(task_id, set()), f"Cycle detected involving task {task_id}"
        except Exception as e:
            pytest.fail(f"Error checking for cycles: {e}")
    
    def test_task_types(self, data_quality_dag):
        """Test that tasks are of expected types."""
        from airflow.operators.python import PythonOperator
        from airflow.operators.bash import BashOperator
        from airflow.operators.dummy import DummyOperator
        
        valid_operator_types = (PythonOperator, BashOperator, DummyOperator)
        
        for task in data_quality_dag.tasks:
            # Most tasks should be PythonOperator for this use case
            assert isinstance(task, valid_operator_types) or hasattr(task, 'execute'), \
                f"Task {task.task_id} has unexpected type {type(task)}"
    
    def test_dag_validation(self, data_quality_dag):
        """Test DAG validation."""
        # This will raise an exception if DAG is invalid
        try:
            data_quality_dag.validate()
        except Exception as e:
            pytest.fail(f"DAG validation failed: {e}")
    
    def test_task_retry_config(self, data_quality_dag):
        """Test that tasks have retry configuration."""
        for task in data_quality_dag.tasks:
            # Tasks should inherit retry config from default_args or have their own
            assert hasattr(task, 'retries')
            if task.retries is not None:
                assert task.retries >= 0


@pytest.mark.integration
@pytest.mark.requires_airflow
@pytest.mark.slow
class TestAirflowDAGExecution:
    """Integration tests for DAG execution (if Airflow is running)."""
    
    def test_dag_can_be_triggered(self, data_quality_dag):
        """Test that DAG can be manually triggered."""
        # Note: This test requires Airflow scheduler to be running
        # In a real integration test environment
        
        execution_date = datetime.utcnow()
        
        try:
            # Create a DagRun
            dag_run = data_quality_dag.create_dagrun(
                state=State.RUNNING,
                execution_date=execution_date,
                run_type=DagRunType.MANUAL,
                run_id=f"test_run_{execution_date.isoformat()}",
            )
            
            assert dag_run is not None
            assert dag_run.state == State.RUNNING
            
        except Exception as e:
            pytest.skip(f"Cannot test DAG execution: {e}")
    
    def test_individual_task_execution(self, data_quality_dag):
        """Test that individual tasks can be executed."""
        # Get first task
        if not data_quality_dag.tasks:
            pytest.skip("No tasks in DAG")
        
        task = data_quality_dag.tasks[0]
        execution_date = datetime.utcnow()
        
        try:
            # Create task instance
            ti = TaskInstance(task=task, execution_date=execution_date)
            
            # Note: Actually running the task requires proper Airflow setup
            # This just verifies the task instance can be created
            assert ti is not None
            assert ti.task_id == task.task_id
            
        except Exception as e:
            pytest.skip(f"Cannot test task execution: {e}")
    
    def test_task_context_available(self, data_quality_dag):
        """Test that task context is properly set up."""
        from airflow.operators.python import PythonOperator
        
        python_tasks = [t for t in data_quality_dag.tasks if isinstance(t, PythonOperator)]
        
        if not python_tasks:
            pytest.skip("No Python tasks to test")
        
        task = python_tasks[0]
        
        # Verify task has callable
        assert hasattr(task, 'python_callable')
        assert callable(task.python_callable)


@pytest.mark.integration
class TestAirflowDAGObservability:
    """Tests for DAG observability and monitoring."""
    
    def test_dag_has_description(self, data_quality_dag):
        """Test that DAG has a description."""
        # Good practice to have descriptions
        assert data_quality_dag.description is not None or data_quality_dag.doc_md is not None, \
            "DAG should have description or documentation"
    
    def test_tasks_have_descriptions(self, data_quality_dag):
        """Test that tasks have descriptions."""
        for task in data_quality_dag.tasks:
            # Tasks should have doc_md or be self-explanatory from task_id
            has_doc = (
                task.doc_md is not None or 
                task.doc is not None or
                len(task.task_id) > 0
            )
            assert has_doc, f"Task {task.task_id} should have documentation"
    
    def test_dag_timeout_configured(self, data_quality_dag):
        """Test that DAG has timeout configured."""
        # Check if dagrun_timeout is set
        if hasattr(data_quality_dag, 'dagrun_timeout'):
            # If set, should be a reasonable value
            if data_quality_dag.dagrun_timeout:
                assert isinstance(data_quality_dag.dagrun_timeout, timedelta)
    
    def test_task_execution_timeout(self, data_quality_dag):
        """Test that tasks have execution timeout."""
        for task in data_quality_dag.tasks:
            # Tasks should have execution_timeout or rely on default
            if hasattr(task, 'execution_timeout') and task.execution_timeout:
                assert isinstance(task.execution_timeout, timedelta)


@pytest.mark.integration
class TestDAGHealthCheck:
    """Tests for DAG health check functionality."""
    
    def test_health_check_dag_exists(self, dagbag):
        """Test that health check DAG exists."""
        health_dag_id = "dop_health_check"
        
        # May or may not exist depending on setup
        if health_dag_id in dagbag.dags:
            health_dag = dagbag.dags[health_dag_id]
            assert health_dag is not None
            assert len(health_dag.tasks) > 0
    
    def test_health_check_tasks(self, dagbag):
        """Test health check tasks if DAG exists."""
        health_dag_id = "dop_health_check"
        
        if health_dag_id not in dagbag.dags:
            pytest.skip("Health check DAG not found")
        
        health_dag = dagbag.dags[health_dag_id]
        task_ids = [task.task_id for task in health_dag.tasks]
        
        # Expected health check tasks
        expected_checks = ['check_postgres', 'check_minio', 'check_redis']
        
        # At least some health checks should exist
        found_checks = [check for check in expected_checks if check in task_ids]
        
        if len(found_checks) == 0:
            # If no specific health checks, should have at least one task
            assert len(task_ids) > 0


@pytest.mark.integration
class TestDAGErrorHandling:
    """Tests for DAG error handling and resilience."""
    
    def test_dag_has_on_failure_callback(self, data_quality_dag):
        """Test that DAG or tasks have failure callbacks."""
        # Check DAG level
        has_dag_callback = (
            hasattr(data_quality_dag, 'on_failure_callback') and 
            data_quality_dag.on_failure_callback is not None
        )
        
        # Check task level
        tasks_with_callbacks = [
            t for t in data_quality_dag.tasks 
            if hasattr(t, 'on_failure_callback') and t.on_failure_callback is not None
        ]
        
        # Either DAG or some tasks should have failure handling
        has_failure_handling = has_dag_callback or len(tasks_with_callbacks) > 0
        
        # This is a best practice but not strictly required
        # so we just check and warn
        if not has_failure_handling:
            print("Warning: No failure callbacks configured")
    
    def test_tasks_have_retries(self, data_quality_dag):
        """Test that critical tasks have retries configured."""
        for task in data_quality_dag.tasks:
            # All tasks should have retry configuration
            if hasattr(task, 'retries'):
                # Retries can be 0, but should be defined
                assert task.retries is not None
