# Production Deployment Script for Data Observability Platform
# Usage: .\deploy-production.ps1 [-Clean] [-Build] [-Start] [-Stop]

param(
    [switch]$Clean,
    [switch]$Build,
    [switch]$Start,
    [switch]$Stop,
    [switch]$Restart,
    [switch]$All
)

$ErrorActionPreference = "Stop"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Data Observability Platform - Production Deployment" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if Docker is running
function Test-DockerRunning {
    try {
        docker info | Out-Null
        return $true
    }
    catch {
        Write-Host "❌ ERROR: Docker is not running. Please start Docker Desktop." -ForegroundColor Red
        exit 1
    }
}

# Function to validate environment files
function Test-EnvironmentFiles {
    Write-Host "🔍 Validating environment files..." -ForegroundColor Yellow
    
    $backendEnv = "backend\.env.production"
    $frontendEnv = "frontend\.env.production"
    
    if (-not (Test-Path $backendEnv)) {
        Write-Host "❌ ERROR: $backendEnv not found!" -ForegroundColor Red
        exit 1
    }
    
    if (-not (Test-Path $frontendEnv)) {
        Write-Host "❌ ERROR: $frontendEnv not found!" -ForegroundColor Red
        exit 1
    }
    
    # Check for default passwords in backend .env
    $envContent = Get-Content $backendEnv -Raw
    $warnings = @()
    
    if ($envContent -match "CHANGE_THIS") {
        $warnings += "Backend .env.production contains default passwords/keys"
    }
    
    if ($warnings.Count -gt 0) {
        Write-Host "⚠️  WARNING: Security issues detected:" -ForegroundColor Yellow
        foreach ($warning in $warnings) {
            Write-Host "   - $warning" -ForegroundColor Yellow
        }
        Write-Host ""
        $response = Read-Host "Continue anyway? (y/N)"
        if ($response -ne "y" -and $response -ne "Y") {
            Write-Host "Deployment cancelled." -ForegroundColor Yellow
            exit 0
        }
    }
    
    Write-Host "✅ Environment files validated" -ForegroundColor Green
}

# Function to clean up Docker resources
function Invoke-CleanUp {
    Write-Host "🧹 Cleaning up Docker resources..." -ForegroundColor Yellow
    
    docker-compose -f docker-compose.production.yml down -v 2>$null
    
    # Remove production images
    docker images | Select-String "dop.*prod" | ForEach-Object {
        $imageName = ($_ -split '\s+')[0] + ":" + ($_ -split '\s+')[1]
        Write-Host "   Removing image: $imageName" -ForegroundColor Gray
        docker rmi $imageName -f 2>$null
    }
    
    Write-Host "✅ Cleanup completed" -ForegroundColor Green
}

# Function to build production images
function Invoke-Build {
    Write-Host "🔨 Building production Docker images..." -ForegroundColor Yellow
    Write-Host "   This may take several minutes..." -ForegroundColor Gray
    Write-Host ""
    
    docker-compose -f docker-compose.production.yml build --no-cache
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ ERROR: Build failed!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Build completed successfully" -ForegroundColor Green
}

# Function to start production services
function Invoke-Start {
    Write-Host "🚀 Starting production services..." -ForegroundColor Yellow
    Write-Host ""
    
    docker-compose -f docker-compose.production.yml up -d
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ ERROR: Failed to start services!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    # Wait for services to be healthy
    $maxAttempts = 30
    $attempt = 1
    
    while ($attempt -le $maxAttempts) {
        $healthStatus = docker-compose -f docker-compose.production.yml ps --format json | ConvertFrom-Json
        $unhealthy = $healthStatus | Where-Object { $_.Health -ne "healthy" -and $_.State -eq "running" }
        
        if ($unhealthy.Count -eq 0) {
            Write-Host "✅ All services are healthy!" -ForegroundColor Green
            break
        }
        
        Write-Host "   Attempt $attempt/$maxAttempts - Waiting for services..." -ForegroundColor Gray
        Start-Sleep -Seconds 5
        $attempt++
    }
    
    if ($attempt -gt $maxAttempts) {
        Write-Host "⚠️  WARNING: Some services may not be fully healthy yet" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "✅ Production services started successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Access points:" -ForegroundColor Cyan
    Write-Host "   Frontend:  http://localhost:3000" -ForegroundColor White
    Write-Host "   Backend:   http://localhost:8000" -ForegroundColor White
    Write-Host "   API Docs:  http://localhost:8000/docs" -ForegroundColor White
    Write-Host "   Airflow:   http://localhost:8080" -ForegroundColor White
    Write-Host "   MinIO:     http://localhost:9001" -ForegroundColor White
}

# Function to stop production services
function Invoke-Stop {
    Write-Host "🛑 Stopping production services..." -ForegroundColor Yellow
    
    docker-compose -f docker-compose.production.yml down
    
    Write-Host "✅ Production services stopped" -ForegroundColor Green
}

# Main execution
Test-DockerRunning

if ($All) {
    Test-EnvironmentFiles
    Invoke-CleanUp
    Invoke-Build
    Invoke-Start
}
elseif ($Restart) {
    Invoke-Stop
    Invoke-Start
}
else {
    if ($Clean) {
        Invoke-CleanUp
    }
    
    if ($Build) {
        Test-EnvironmentFiles
        Invoke-Build
    }
    
    if ($Start) {
        Test-EnvironmentFiles
        Invoke-Start
    }
    
    if ($Stop) {
        Invoke-Stop
    }
    
    if (-not $Clean -and -not $Build -and -not $Start -and -not $Stop) {
        Write-Host "Usage: .\deploy-production.ps1 [-Clean] [-Build] [-Start] [-Stop] [-Restart] [-All]" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Options:" -ForegroundColor Cyan
        Write-Host "   -Clean    : Remove all production Docker resources" -ForegroundColor White
        Write-Host "   -Build    : Build production Docker images" -ForegroundColor White
        Write-Host "   -Start    : Start production services" -ForegroundColor White
        Write-Host "   -Stop     : Stop production services" -ForegroundColor White
        Write-Host "   -Restart  : Restart production services" -ForegroundColor White
        Write-Host "   -All      : Clean, build, and start (full deployment)" -ForegroundColor White
        Write-Host ""
        Write-Host "Examples:" -ForegroundColor Cyan
        Write-Host "   .\deploy-production.ps1 -All          # Full deployment" -ForegroundColor Gray
        Write-Host "   .\deploy-production.ps1 -Build -Start # Build and start" -ForegroundColor Gray
        Write-Host "   .\deploy-production.ps1 -Restart      # Restart services" -ForegroundColor Gray
    }
}

Write-Host ""
