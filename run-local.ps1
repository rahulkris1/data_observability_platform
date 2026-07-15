# Data Observability Platform - Local Development Runner
# This script starts infrastructure in Docker and runs backend/frontend locally

Write-Host "Starting Data Observability Platform in Local Development Mode" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is available
$dockerInstalled = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerInstalled) {
    Write-Host "ERROR: Docker is not installed!" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    exit 1
}

# Check if Docker is running
try {
    docker ps | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker is not running"
    }
} catch {
    Write-Host "ERROR: Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host "SUCCESS: Docker is running" -ForegroundColor Green
Write-Host ""

# Start infrastructure services
Write-Host "Starting infrastructure services (PostgreSQL, Redis, MinIO, Airflow)..." -ForegroundColor Cyan
docker compose -f docker-compose.dev.yml up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to start infrastructure services" -ForegroundColor Red
    exit 1
}

Write-Host "SUCCESS: Infrastructure services started" -ForegroundColor Green
Write-Host ""

# Wait for services to be healthy
Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Show service status
Write-Host ""
Write-Host "Service Status:" -ForegroundColor Cyan
docker compose -f docker-compose.dev.yml ps

Write-Host ""
Write-Host "SUCCESS: Infrastructure is ready!" -ForegroundColor Green
Write-Host ""
Write-Host "Available Services:" -ForegroundColor Cyan
Write-Host "  - PostgreSQL: localhost:5432" -ForegroundColor White
Write-Host "  - Redis: localhost:6379" -ForegroundColor White
Write-Host "  - MinIO Console: http://localhost:9001 (minioadmin/minioadmin123)" -ForegroundColor White
Write-Host "  - MinIO API: http://localhost:9000" -ForegroundColor White
Write-Host "  - Airflow: http://localhost:8080 (admin/admin123)" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Run backend: cd backend && uvicorn app.main:app --reload --port 8000" -ForegroundColor White
Write-Host "  2. Run frontend: cd frontend && npm run dev" -ForegroundColor White
Write-Host "  3. Run Celery worker: cd backend && celery -A app.celery_app worker --loglevel=info" -ForegroundColor White
Write-Host ""
Write-Host "To stop infrastructure: docker compose -f docker-compose.dev.yml down" -ForegroundColor Cyan
