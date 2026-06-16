# Retry System Setup Script
# Initializes the retry system for the Data Observability Platform

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Retry System Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if in correct directory
if (-not (Test-Path "backend\alembic.ini")) {
    Write-Host "Error: Please run this script from the data_observability_platform root directory" -ForegroundColor Red
    exit 1
}

Write-Host "[1/4] Checking Python virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "  ✓ Virtual environment found" -ForegroundColor Green
    & .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "  ! Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv .venv
    & .\.venv\Scripts\Activate.ps1
    Write-Host "  ✓ Virtual environment created" -ForegroundColor Green
}

Write-Host ""
Write-Host "[2/4] Installing dependencies..." -ForegroundColor Yellow
cd backend
pip install -q sqlalchemy alembic psycopg2-binary fastapi pydantic
Write-Host "  ✓ Dependencies installed" -ForegroundColor Green

Write-Host ""
Write-Host "[3/4] Running database migrations..." -ForegroundColor Yellow
try {
    alembic upgrade head
    Write-Host "  ✓ Database migrations completed" -ForegroundColor Green
} catch {
    Write-Host "  ! Warning: Migration may have failed. Check database connection." -ForegroundColor Yellow
    Write-Host "  Error: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "[4/4] Verifying retry system installation..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Running verification script..." -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Gray
try {
    python verify_retry_workflow.py
    Write-Host "----------------------------------------" -ForegroundColor Gray
    Write-Host "  ✓ Verification completed" -ForegroundColor Green
} catch {
    Write-Host "  ! Verification failed. See errors above." -ForegroundColor Yellow
}

cd ..

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Start the backend API server:" -ForegroundColor White
Write-Host "   cd backend && uvicorn app.main:app --reload" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Start the frontend development server:" -ForegroundColor White
Write-Host "   cd frontend && npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Access the Validation Retry page:" -ForegroundColor White
Write-Host "   http://localhost:3000/validation-retry" -ForegroundColor Gray
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Yellow
Write-Host "  RETRY_SYSTEM_README.md" -ForegroundColor Gray
Write-Host ""
Write-Host "API Documentation:" -ForegroundColor Yellow
Write-Host "  http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""
