"""
Verification script for Celery task execution.
Tests that tasks can be submitted and executed successfully.
"""
import time
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.celery_app import celery_app
from app.tasks.async_validation_task import validate_dataset_async
from app.tasks.async_profiling_task import profile_dataset_async, calculate_data_quality_score


def test_celery_connection():
    """Test basic Celery and Redis connectivity."""
    print("=" * 60)
    print("CELERY TASK EXECUTION VERIFICATION")
    print("=" * 60)
    print()
    
    print("1. Testing Celery connection...")
    try:
        # Test broker connection
        inspect = celery_app.control.inspect()
        
        # Check if any workers are active
        active_workers = inspect.active()
        
        if active_workers is None:
            print("❌ No Celery workers detected!")
            print("   Please start a worker with: celery -A app.celery_app worker --loglevel=info")
            return False
        
        worker_count = len(active_workers)
        print(f"✅ Celery broker connected")
        print(f"✅ {worker_count} worker(s) available")
        
        for worker_name in active_workers.keys():
            print(f"   - {worker_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to Celery: {str(e)}")
        print("   Make sure Redis is running on localhost:6379")
        return False


def test_task_submission():
    """Test submitting a simple task."""
    print()
    print("2. Testing task submission...")
    
    try:
        # Submit a simple validation task (mock data)
        task = validate_dataset_async.delay(
            contract_name="test_contract",
            dataset_columns=[
                {"name": "id", "type": "integer"},
                {"name": "name", "type": "string"},
            ],
            dataset_name="test_dataset",
        )
        
        print(f"✅ Task submitted successfully")
        print(f"   Task ID: {task.id}")
        print(f"   Status: {task.status}")
        
        return task
        
    except Exception as e:
        print(f"❌ Failed to submit task: {str(e)}")
        return None


def test_task_execution(task):
    """Wait for task to complete and check result."""
    print()
    print("3. Waiting for task execution...")
    print("   (This may take a few seconds...)")
    
    try:
        # Wait up to 30 seconds for task to complete
        result = task.get(timeout=30)
        
        print(f"✅ Task completed successfully")
        print(f"   Status: {result.get('status', 'unknown')}")
        print(f"   Execution time: {result.get('execution_time', 'N/A')} seconds")
        
        return True
        
    except TimeoutError:
        print(f"❌ Task did not complete within 30 seconds")
        print(f"   Current status: {task.status}")
        return False
        
    except Exception as e:
        print(f"❌ Task execution failed: {str(e)}")
        return False


def test_queue_metrics():
    """Test queue metrics retrieval."""
    print()
    print("4. Testing queue metrics...")
    
    try:
        from app.services.task_queue_service import get_task_queue_service
        
        service = get_task_queue_service()
        metrics = service.get_queue_metrics()
        
        print(f"✅ Queue metrics retrieved")
        print(f"   Queued tasks: {metrics['queued_tasks']}")
        print(f"   Running tasks: {metrics['running_tasks']}")
        print(f"   Total pending: {metrics['total_pending']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to get queue metrics: {str(e)}")
        return False


def test_worker_stats():
    """Test worker statistics retrieval."""
    print()
    print("5. Testing worker statistics...")
    
    try:
        from app.services.task_queue_service import get_task_queue_service
        
        service = get_task_queue_service()
        stats = service.get_worker_stats()
        
        print(f"✅ Worker stats retrieved")
        print(f"   Total workers: {stats['total_workers']}")
        
        for worker in stats['workers']:
            print(f"   - {worker['name']}: {worker['active_tasks']} active tasks")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to get worker stats: {str(e)}")
        return False


def main():
    """Run all verification tests."""
    results = []
    
    # Test 1: Connection
    results.append(test_celery_connection())
    
    if not results[0]:
        print()
        print("=" * 60)
        print("⚠️  SETUP REQUIRED")
        print("=" * 60)
        print()
        print("Before running this verification:")
        print("1. Make sure Redis is running:")
        print("   docker-compose up -d redis")
        print()
        print("2. Start a Celery worker:")
        print("   cd backend")
        print("   celery -A app.celery_app worker --loglevel=info --pool=solo")
        print()
        return
    
    # Test 2: Task submission
    task = test_task_submission()
    results.append(task is not None)
    
    # Test 3: Task execution (only if submission succeeded)
    if task:
        results.append(test_task_execution(task))
    else:
        results.append(False)
    
    # Test 4: Queue metrics
    results.append(test_queue_metrics())
    
    # Test 5: Worker stats
    results.append(test_worker_stats())
    
    # Summary
    print()
    print("=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    print()
    
    test_names = [
        "Celery Connection",
        "Task Submission",
        "Task Execution",
        "Queue Metrics",
        "Worker Statistics",
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results), 1):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i}. {name}: {status}")
    
    total_passed = sum(results)
    total_tests = len(results)
    
    print()
    print(f"Total: {total_passed}/{total_tests} tests passed")
    print()
    
    if total_passed == total_tests:
        print("🎉 All tests passed! Celery task system is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    print()


if __name__ == "__main__":
    main()
