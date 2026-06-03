from fastapi import FastAPI, File, HTTPException, UploadFile

from app.services.ingestion_service import IngestionService
from app.api.audit_logs import router as audit_router

app = FastAPI(
    title="Data Observability Platform",
    description="Basic API for data observability",
    version="0.1.0"
)

# Include routers
app.include_router(audit_router)

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
