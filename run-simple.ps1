# Run simplified backend (no Docker needed)
Write-Host "Starting Data Observability Platform - Simplified Mode" -ForegroundColor Cyan
Write-Host "(Backend only, no external services required)" -ForegroundColor Yellow
Write-Host ""

# Check Python
$pythonInstalled = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonInstalled) {
    Write-Host "ERROR: Python is not installed!" -ForegroundColor Red
    exit 1
}

Write-Host "Installing/updating dependencies..." -ForegroundColor Cyan
cd backend
pip install -r requirements.txt

Write-Host ""
Write-Host "Starting FastAPI backend on http://localhost:8000..." -ForegroundColor Green
Write-Host ""

# Copy simplified env
Copy-Item ..\.env.simple .\.env -Force

# Start backend
uvicorn app.main:app --reload --port 8000
