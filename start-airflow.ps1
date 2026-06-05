# Airflow Quick Start Script
# Run this script to start all services and verify Airflow setup

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Airflow Integration - Quick Start" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Start Docker services
Write-Host "[1/4] Starting Docker services..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to start Docker services" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Docker services started" -ForegroundColor Green
Write-Host ""

# Step 2: Wait for Airflow to initialize
Write-Host "[2/4] Waiting for Airflow to initialize (60 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 60
Write-Host "✓ Initialization wait complete" -ForegroundColor Green
Write-Host ""

# Step 3: Verify Airflow health
Write-Host "[3/4] Verifying Airflow health..." -ForegroundColor Yellow
Set-Location -Path "backend"

# Check if virtual environment exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & .\.venv\Scripts\Activate.ps1
    python verify_airflow.py
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Airflow health check failed" -ForegroundColor Red
        Write-Host "  Check logs with: docker logs dop-airflow-webserver" -ForegroundColor Yellow
        Set-Location -Path ".."
        exit 1
    }
} else {
    Write-Host "⚠ Virtual environment not found. Skipping health check." -ForegroundColor Yellow
    Write-Host "  Install dependencies: pip install -r requirements.txt" -ForegroundColor Yellow
}

Set-Location -Path ".."
Write-Host ""

# Step 4: Display access information
Write-Host "[4/4] Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Access Information" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Airflow UI:" -ForegroundColor White
Write-Host "  URL: http://localhost:8080" -ForegroundColor Gray
Write-Host "  Username: admin" -ForegroundColor Gray
Write-Host "  Password: admin123" -ForegroundColor Gray
Write-Host ""
Write-Host "Backend API:" -ForegroundColor White
Write-Host "  URL: http://localhost:8000" -ForegroundColor Gray
Write-Host "  Docs: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "Frontend (if running):" -ForegroundColor White
Write-Host "  URL: http://localhost:3000" -ForegroundColor Gray
Write-Host "  Pipelines: http://localhost:3000/pipelines" -ForegroundColor Gray
Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Next Steps" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Start backend API:" -ForegroundColor White
Write-Host "   cd backend" -ForegroundColor Gray
Write-Host "   .\.venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "   uvicorn app.main:app --reload" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Start frontend:" -ForegroundColor White
Write-Host "   cd frontend" -ForegroundColor Gray
Write-Host "   npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "3. View pipelines dashboard:" -ForegroundColor White
Write-Host "   http://localhost:3000/pipelines" -ForegroundColor Gray
Write-Host ""
Write-Host "For more information, see AIRFLOW_SETUP.md" -ForegroundColor Cyan
Write-Host ""
