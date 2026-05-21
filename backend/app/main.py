from fastapi import FastAPI

app = FastAPI(
    title="Data Observability Platform",
    description="Basic API for data observability",
    version="0.1.0"
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Data Observability Platform API"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}
