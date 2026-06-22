"""
Task Queue Service for monitoring and managing Celery tasks.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from celery.result import AsyncResult
from celery import states

from app.celery_app import celery_app


class TaskQueueService:
    """Service for monitoring and managing async task queues."""
    
    def __init__(self):
        self.celery = celery_app
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a specific task.
        
        Args:
            task_id: Celery task ID
            
        Returns:
            Dictionary containing task status and metadata
        """
        result = AsyncResult(task_id, app=self.celery)
        
        response = {
            "task_id": task_id,
            "status": result.state,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None,
        }
        
        # Add result or error information
        if result.ready():
            if result.successful():
                response["result"] = result.result
            else:
                response["error"] = str(result.info) if result.info else "Task failed"
        elif result.state == states.PENDING:
            response["info"] = "Task is waiting to be executed"
        elif result.state == states.STARTED or result.state == "RUNNING":
            # Get task metadata if available
            if result.info:
                response["info"] = result.info
        
        return response
    
    def get_task_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """
        Get the result of a completed task.
        
        Args:
            task_id: Celery task ID
            timeout: Optional timeout in seconds to wait for result
            
        Returns:
            Task result
            
        Raises:
            TimeoutError: If timeout is reached before task completes
            Exception: If task failed
        """
        result = AsyncResult(task_id, app=self.celery)
        return result.get(timeout=timeout)
    
    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """
        Cancel a pending or running task.
        
        Args:
            task_id: Celery task ID
            
        Returns:
            Dictionary with cancellation status
        """
        result = AsyncResult(task_id, app=self.celery)
        result.revoke(terminate=True)
        
        return {
            "task_id": task_id,
            "cancelled": True,
            "message": "Task cancellation requested",
        }
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """
        Get statistics about active Celery workers.
        
        Returns:
            Dictionary containing worker statistics
        """
        # Get active workers
        inspect = self.celery.control.inspect()
        
        active_workers = inspect.active()
        registered_tasks = inspect.registered()
        stats = inspect.stats()
        
        worker_list = []
        
        if active_workers:
            for worker_name, tasks in active_workers.items():
                worker_info = {
                    "name": worker_name,
                    "active_tasks": len(tasks),
                    "tasks": [
                        {
                            "task_id": task["id"],
                            "task_name": task["name"],
                            "args": str(task.get("args", [])),
                            "kwargs": str(task.get("kwargs", {})),
                        }
                        for task in tasks
                    ],
                }
                
                # Add registered tasks for this worker
                if registered_tasks and worker_name in registered_tasks:
                    worker_info["registered_tasks"] = registered_tasks[worker_name]
                
                # Add worker stats
                if stats and worker_name in stats:
                    worker_info["stats"] = stats[worker_name]
                
                worker_list.append(worker_info)
        
        return {
            "total_workers": len(worker_list) if worker_list else 0,
            "workers": worker_list,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def get_queue_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about task queues.
        
        Returns:
            Dictionary containing queue metrics
        """
        inspect = self.celery.control.inspect()
        
        # Get reserved (queued) tasks
        reserved = inspect.reserved()
        active = inspect.active()
        scheduled = inspect.scheduled()
        
        total_queued = 0
        total_running = 0
        total_scheduled = 0
        
        if reserved:
            total_queued = sum(len(tasks) for tasks in reserved.values())
        
        if active:
            total_running = sum(len(tasks) for tasks in active.values())
        
        if scheduled:
            total_scheduled = sum(len(tasks) for tasks in scheduled.values())
        
        return {
            "queued_tasks": total_queued,
            "running_tasks": total_running,
            "scheduled_tasks": total_scheduled,
            "total_pending": total_queued + total_running + total_scheduled,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def get_task_history(
        self,
        task_name: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get history of recent tasks.
        
        Note: This is a simplified implementation. In production, you would
        store task history in a database for better persistence and querying.
        
        Args:
            task_name: Optional filter by task name
            limit: Maximum number of tasks to return
            
        Returns:
            List of task records
        """
        # This is a placeholder - in production, implement proper task history
        # storage in PostgreSQL or use Celery Flower for monitoring
        return []
    
    def purge_queue(self, queue_name: str = "default") -> Dict[str, Any]:
        """
        Purge all tasks from a specific queue.
        
        Args:
            queue_name: Name of the queue to purge
            
        Returns:
            Dictionary with purge results
        """
        purged_count = self.celery.control.purge()
        
        return {
            "queue": queue_name,
            "purged_tasks": purged_count,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def get_task_info_bulk(self, task_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get status information for multiple tasks.
        
        Args:
            task_ids: List of task IDs
            
        Returns:
            List of task status dictionaries
        """
        return [self.get_task_status(task_id) for task_id in task_ids]
    
    def get_active_task_summary(self) -> Dict[str, Any]:
        """
        Get a summary of currently active tasks grouped by task type.
        
        Returns:
            Dictionary with task summary by type
        """
        inspect = self.celery.control.inspect()
        active = inspect.active()
        
        task_summary = {}
        
        if active:
            for worker_name, tasks in active.items():
                for task in tasks:
                    task_name = task["name"]
                    if task_name not in task_summary:
                        task_summary[task_name] = {
                            "task_name": task_name,
                            "count": 0,
                            "task_ids": [],
                        }
                    task_summary[task_name]["count"] += 1
                    task_summary[task_name]["task_ids"].append(task["id"])
        
        return {
            "total_active_tasks": sum(info["count"] for info in task_summary.values()),
            "tasks_by_type": list(task_summary.values()),
            "timestamp": datetime.utcnow().isoformat(),
        }


# Singleton service instance
_task_queue_service: Optional[TaskQueueService] = None


def get_task_queue_service() -> TaskQueueService:
    """Get or create the task queue service singleton."""
    global _task_queue_service
    if _task_queue_service is None:
        _task_queue_service = TaskQueueService()
    return _task_queue_service
