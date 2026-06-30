# Start Data Observability Platform with Docker
# This script builds and starts all services

param(
    [switch]$Rebuild,
    [switch]$Clean
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Data Observability Platform" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Determine Docker Compose command
$composeCmd = $null
try {
    docker compose version | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $composeCmd = "docker compose"
    }
}
catch {
    try {
        docker-compose --version | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $composeCmd = "docker-compose"
        }
    }
    catch {
        Write-Host "✗ Docker Compose not found. Please install Docker Desktop.`n" -ForegroundColor Red
        Write-Host "Run: .\check-docker-prerequisites.ps1" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "Using: $composeCmd`n" -ForegroundColor Gray

# Check if Docker is running
Write-Host "Checking Docker..." -ForegroundColor Yellow
try {
    docker info | Out-Null
    Write-Host "✓ Docker is running`n" -ForegroundColor Green
}
catch {
    Write-Host "✗ Docker is not running. Please start Docker Desktop.`n" -ForegroundColor Red
    exit 1
}

# Clean up if requested
if ($Clean) {
    Write-Host "Cleaning up existing containers and volumes..." -ForegroundColor Yellow
    Invoke-Expression "$composeCmd down -v"
    Write-Host "✓ Cleanup complete`n" -ForegroundColor Green
}

# Build and start services
if ($Rebuild -or $Clean) {
    Write-Host "Building and starting all services (this may take a few minutes)..." -ForegroundColor Yellow
    Invoke-Expression "$composeCmd up -d --build"
}
else {
    Write-Host "Starting all services..." -ForegroundColor Yellow
    Invoke-Expression "$composeCmd up -d"
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Services started successfully`n" -ForegroundColor Green
    
    Write-Host "Waiting for services to become healthy (this may take up to 2 minutes)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    # Wait for backend to be healthy
    $maxAttempts = 24  # 2 minutes with 5-second intervals
    $attempt = 0
    $backendHealthy = $false
    
    while ($attempt -lt $maxAttempts -and -not $backendHealthy) {
        $attempt++
        $health = docker inspect --format='{{.State.Health.Status}}' dop-backend 2>$null
        
        if ($health -eq "healthy") {
            $backendHealthy = $true
            Write-Host "✓ Backend is healthy" -ForegroundColor Green
        }
        else {
            Write-Host "  Waiting for backend... ($attempt/$maxAttempts)" -ForegroundColor Gray
            Start-Sleep -Seconds 5
        }
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Services are starting up!" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    Write-Host "Access the platform at:" -ForegroundColor White
    Write-Host "  Frontend:          http://localhost:3000" -ForegroundColor Cyan
    Write-Host "  Backend API:       http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  API Docs:          http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "  Airflow UI:        http://localhost:8080 (admin/admin123)" -ForegroundColor Cyan
    Write-Host "  MinIO Console:     http://localhost:9001 (minioadmin/minioadmin123)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Run verification:" -ForegroundColor White
    Write-Host "  .\verify-docker-setup.ps1" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "View logs:" -ForegroundColor White
    Write-Host "  $composeCmd logs -f" -ForegroundColor Yellow
    Write-Host ""
}
else {
    Write-Host "✗ Failed to start services`n" -ForegroundColor Red
    Write-Host "Check logs with: $composeCmd logs" -ForegroundColor Yellow
    exit 1
}
