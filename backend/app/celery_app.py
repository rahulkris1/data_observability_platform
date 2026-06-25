"""
Celery application configuration for async task execution.
Uses Redis as the broker and result backend.
"""
from celery import Celery
from app.core.config import Settings

settings = Settings()

# Initialize Celery app
celery_app = Celery(
    "data_observability_platform",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.async_validation_task",
        "app.tasks.async_profiling_task",
        "app.tasks.health_score_tasks",
    ]
)

# Celery Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max task execution
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks (prevent memory leaks)
    result_expires=3600,  # Keep results for 1 hour
    broker_connection_retry_on_startup=True,
)

# Task routing - all tasks go to default queue
celery_app.conf.task_routes = {
    "app.tasks.async_validation_task.*": {"queue": "default"},
    "app.tasks.async_profiling_task.*": {"queue": "default"},
    "app.tasks.health_score_tasks.*": {"queue": "default"},
}
