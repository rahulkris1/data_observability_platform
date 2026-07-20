from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.services.ingestion_service import IngestionService
from app.api.audit_logs import router as audit_router
from app.api.observability_routes import router as observability_router
from app.api.profiling_routes import router as profiling_router
from app.api.schema_drift_routes import router as schema_drift_router
from app.api.health_routes import router as health_router
from app.api.storage_routes import router as storage_router
from app.api.glue_routes import router as glue_router
from app.api.auth_routes import router as auth_router
from app.api.validation_routes import router as validation_router
from app.api.metrics_routes import router as metrics_router
from app.api.freshness_routes import router as freshness_router
from app.api.dag_execution_routes import router as dag_execution_router
from app.api.cache_routes import router as cache_router
from app.api.airflow_routes import router as airflow_router
from app.api.retry_routes import router as retry_router
from app.api.rules_routes import router as rules_router
from app.api.task_routes import router as task_router
from app.api.warehouse_routes import router as warehouse_router
from app.api.load_monitoring_routes import router as load_monitoring_router
from app.api.schema_contracts import router as schema_contracts_router
from app.observability import configure_logging, get_metrics_service
from app.observability.middleware import RequestLoggingMiddleware
from app.core.exception_handler import (
    configure_exception_handlers,
    build_success_response,
    BadRequestException,
    ServiceUnavailableException
)
from app.core.startup_validator import run_startup_validation

# Configure logging on startup
configure_logging(
    log_level="INFO",
    enable_console=True,
    enable_json=True,
)

logger = logging.getLogger(__name__)

# Run startup validation
is_valid, warnings, errors = run_startup_validation()
if not is_valid:
    logger.error("Startup validation failed! Application may not function correctly.")
    logger.error(f"Errors: {errors}")
if warnings:
    logger.warning(f"Startup warnings: {warnings}")

app = FastAPI(
    title="Data Observability Platform",
    description="Basic API for data observability",
    version="0.1.0"
)

# Configure centralized exception handling
configure_exception_handlers(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware
metrics_service = get_metrics_service()
app.add_middleware(RequestLoggingMiddleware, metrics_service=metrics_service)

# Include routers
app.include_router(auth_router)  # Authentication routes
app.include_router(audit_router)
app.include_router(observability_router)
app.include_router(profiling_router)
app.include_router(schema_drift_router, prefix="/api/v1")  # Add prefix for schema-drift
app.include_router(health_router)
app.include_router(storage_router, prefix="/api/v1/storage", tags=["storage"])
app.include_router(glue_router, prefix="/api/v1", tags=["glue"])
app.include_router(validation_router)
app.include_router(metrics_router)
app.include_router(freshness_router)
app.include_router(dag_execution_router, prefix="/api/v1")  # Fix path mismatch: backend uses /dag-executions, frontend expects /api/v1/dag-executions
app.include_router(cache_router)
app.include_router(airflow_router, prefix="/api/v1")  # Add prefix for airflow
app.include_router(retry_router)
app.include_router(rules_router)
app.include_router(task_router, prefix="/api/v1")  # Add prefix for tasks
app.include_router(warehouse_router)
app.include_router(load_monitoring_router, prefix="/api/v1")  # Add prefix for load-monitoring
app.include_router(schema_contracts_router)

ingestion_service = IngestionService()


@app.get("/")
async def root():
    """Root endpoint"""
    return build_success_response(
        data={"message": "Data Observability Platform API"},
        message="Welcome to Data Observability Platform"
    )


@app.get("/health")
async def health():
    """Health check endpoint"""
    return build_success_response(
        data={"status": "healthy"},
        message="Service is healthy"
    )


@app.post("/api/v1/ingest")
async def ingest_file(file: UploadFile = File(...)):
    """Upload a local dataset file and ingest it into MinIO."""
    try:
        file_bytes = await file.read()
        summary = ingestion_service.ingest_dataset(file.filename, file_bytes, file.content_type)
        return build_success_response(
            data=summary,
            message="File ingested successfully"
        )
    except ValueError as exc:
        raise BadRequestException(str(exc))
    except RuntimeError as exc:
        raise ServiceUnavailableException(str(exc))
    except Exception as exc:
        raise ServiceUnavailableException("Unexpected ingestion error")
