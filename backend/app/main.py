from fastapi import FastAPI, File, HTTPException, UploadFile

from app.services.ingestion_service import IngestionService
from app.api.audit_logs import router as audit_router
from app.api.observability_routes import router as observability_router
from app.api.profiling_routes import router as profiling_router
from app.api.schema_drift_routes import router as schema_drift_router
from app.api.health_routes import router as health_router
from app.api.storage_routes import router as storage_router
from app.observability import configure_logging, get_metrics_service
from app.observability.middleware import RequestLoggingMiddleware

# Configure logging on startup
configure_logging(
    log_level="INFO",
    enable_console=True,
    enable_json=True,
)

app = FastAPI(
    title="Data Observability Platform",
    description="Basic API for data observability",
    version="0.1.0"
)

# Add middleware
metrics_service = get_metrics_service()
app.add_middleware(RequestLoggingMiddleware, metrics_service=metrics_service)

# Include routers
app.include_router(audit_router)
app.include_router(observability_router)
app.include_router(profiling_router)
app.include_router(schema_drift_router)
app.include_router(health_router)
app.include_router(storage_router, prefix="/api/v1/storage", tags=["storage"])

ingestion_service = IngestionService()


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Data Observability Platform API"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/api/v1/ingest")
async def ingest_file(file: UploadFile = File(...)):
    """Upload a local dataset file and ingest it into MinIO."""
    try:
        file_bytes = await file.read()
        summary = ingestion_service.ingest_dataset(file.filename, file_bytes, file.content_type)
        return {"success": True, "result": summary}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unexpected ingestion error")
