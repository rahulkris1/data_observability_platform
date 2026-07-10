# Production Deployment Startup Script
# Starts all services in production mode using Docker Compose

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Data Observability Platform" -ForegroundColor Cyan
Write-Host "Production Deployment (Local Docker)" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker status..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker is installed: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not installed or not running" -ForegroundColor Red
    Write-Host "   Please install Docker Desktop and try again" -ForegroundColor Red
    exit 1
}

try {
    docker ps | Out-Null
    Write-Host "✅ Docker daemon is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker daemon is not running" -ForegroundColor Red
    Write-Host "   Please start Docker Desktop and try again" -ForegroundColor Red
    exit 1
}

# Check if docker-compose is available
try {
    docker-compose --version | Out-Null
    Write-Host "✅ docker-compose is available" -ForegroundColor Green
} catch {
    Write-Host "❌ docker-compose is not available" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Validating production configuration..." -ForegroundColor Yellow

# Run backend validation
Write-Host ""
Write-Host "--- Backend Validation ---" -ForegroundColor Cyan
& .\verify-backend-production-config.ps1
if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 1) {
    Write-Host "❌ Backend validation failed with critical errors" -ForegroundColor Red
    $response = Read-Host "Continue anyway? (y/N)"
    if ($response -ne "y" -and $response -ne "Y") {
        exit 1
    }
}

# Run frontend validation
Write-Host ""
Write-Host "--- Frontend Validation ---" -ForegroundColor Cyan
& .\verify-frontend-production-config.ps1
if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 1) {
    Write-Host "❌ Frontend validation failed with critical errors" -ForegroundColor Red
    $response = Read-Host "Continue anyway? (y/N)"
    if ($response -ne "y" -and $response -ne "Y") {
        exit 1
    }
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Starting Production Services" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Stop any existing containers
Write-Host "Stopping any existing containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.production.yml down 2>$null
Write-Host "✅ Cleaned up existing containers" -ForegroundColor Green
Write-Host ""

# Build production images
Write-Host "Building production Docker images..." -ForegroundColor Yellow
Write-Host "This may take several minutes..." -ForegroundColor Gray
docker-compose -f docker-compose.production.yml build --no-cache

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to build Docker images" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker images built successfully" -ForegroundColor Green
Write-Host ""

# Start services
Write-Host "Starting production services..." -ForegroundColor Yellow
docker-compose -f docker-compose.production.yml up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start services" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Services started successfully" -ForegroundColor Green
Write-Host ""

# Wait for services to be healthy
Write-Host "Waiting for services to become healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check service status
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Service Status" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

docker-compose -f docker-compose.production.yml ps

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Production Deployment Complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Services Available:" -ForegroundColor Cyan
Write-Host "   Frontend:   http://localhost:3000" -ForegroundColor White
Write-Host "   Backend:    http://localhost:8000" -ForegroundColor White
Write-Host "   API Docs:   http://localhost:8000/docs" -ForegroundColor White
Write-Host "   Airflow:    http://localhost:8080" -ForegroundColor White
Write-Host "   MinIO:      http://localhost:9001" -ForegroundColor White
Write-Host ""
Write-Host "📋 Useful Commands:" -ForegroundColor Cyan
Write-Host "   View logs:        docker-compose -f docker-compose.production.yml logs -f" -ForegroundColor Gray
Write-Host "   View backend:     docker-compose -f docker-compose.production.yml logs -f backend" -ForegroundColor Gray
Write-Host "   View frontend:    docker-compose -f docker-compose.production.yml logs -f frontend" -ForegroundColor Gray
Write-Host "   Stop services:    docker-compose -f docker-compose.production.yml down" -ForegroundColor Gray
Write-Host "   Restart services: docker-compose -f docker-compose.production.yml restart" -ForegroundColor Gray
Write-Host ""
Write-Host "🔍 To validate deployment, run:" -ForegroundColor Cyan
Write-Host "   .\validate-production-deployment.ps1" -ForegroundColor White
Write-Host ""
