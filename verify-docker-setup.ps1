# Verify Docker Setup for Data Observability Platform
# This script verifies all Docker containers are running and healthy

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Data Observability Platform - Docker Verification" -ForegroundColor Cyan
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
        # Will be handled in Docker running check
    }
}

# Function to check if Docker is running
function Test-DockerRunning {
    try {
        docker info | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Function to check container status
function Get-ContainerStatus {
    param([string]$containerName)
    
    $status = docker ps --filter "name=$containerName" --format "{{.Status}}"
    if ($status) {
        return $status
    }
    else {
        return "NOT RUNNING"
    }
}

# Function to check container health
function Get-ContainerHealth {
    param([string]$containerName)
    
    $health = docker inspect --format='{{.State.Health.Status}}' $containerName 2>$null
    if ($health) {
        return $health
    }
    else {
        $running = docker inspect --format='{{.State.Running}}' $containerName 2>$null
        if ($running -eq "true") {
            return "running (no healthcheck)"
        }
        else {
            return "not running"
        }
    }
}

# Function to test HTTP endpoint
function Test-HttpEndpoint {
    param(
        [string]$url,
        [string]$serviceName
    )
    
    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "  ✓ $serviceName endpoint is accessible" -ForegroundColor Green
            return $true
        }
    }
    catch {
        Write-Host "  ✗ $serviceName endpoint is NOT accessible" -ForegroundColor Red
        return $false
    }
}

# Check if Docker is running
Write-Host "1. Checking Docker daemon..." -ForegroundColor Yellow
if (Test-DockerRunning) {
    Write-Host "  ✓ Docker is running" -ForegroundColor Green
    if ($composeCmd) {
        Write-Host "  ✓ Using: $composeCmd`n" -ForegroundColor Green
    }
}
else {
    Write-Host "  ✗ Docker is not running. Please start Docker Desktop.`n" -ForegroundColor Red
    Write-Host "Run: .\check-docker-prerequisites.ps1" -ForegroundColor Yellow
    exit 1
}

# List of containers to check
$containers = @(
    @{Name="dop-postgres"; DisplayName="PostgreSQL Database"},
    @{Name="dop-redis"; DisplayName="Redis Cache"},
    @{Name="dop-minio"; DisplayName="MinIO Object Storage"},
    @{Name="dop-backend"; DisplayName="Backend API"},
    @{Name="dop-celery-worker"; DisplayName="Celery Worker"},
    @{Name="dop-airflow-webserver"; DisplayName="Airflow Webserver"},
    @{Name="dop-airflow-scheduler"; DisplayName="Airflow Scheduler"},
    @{Name="dop-frontend"; DisplayName="Frontend Application"}
)

# Check container status
Write-Host "2. Checking container status..." -ForegroundColor Yellow
$allRunning = $true
foreach ($container in $containers) {
    $status = Get-ContainerStatus -containerName $container.Name
    $health = Get-ContainerHealth -containerName $container.Name
    
    if ($status -ne "NOT RUNNING") {
        if ($health -eq "healthy") {
            Write-Host "  ✓ $($container.DisplayName) ($($container.Name)): $status - HEALTHY" -ForegroundColor Green
        }
        elseif ($health -eq "running (no healthcheck)") {
            Write-Host "  ✓ $($container.DisplayName) ($($container.Name)): $status" -ForegroundColor Green
        }
        else {
            Write-Host "  ⚠ $($container.DisplayName) ($($container.Name)): $status - $health" -ForegroundColor Yellow
            $allRunning = $false
        }
    }
    else {
        Write-Host "  ✗ $($container.DisplayName) ($($container.Name)): NOT RUNNING" -ForegroundColor Red
        $allRunning = $false
    }
}
Write-Host ""

# Check service endpoints
Write-Host "3. Checking service endpoints..." -ForegroundColor Yellow
$endpoints = @(
    @{Url="http://localhost:8000/health"; Name="Backend API"},
    @{Url="http://localhost:3000/api/health"; Name="Frontend"},
    @{Url="http://localhost:8080/health"; Name="Airflow Webserver"},
    @{Url="http://localhost:9000/minio/health/live"; Name="MinIO"}
)

$allEndpointsOk = $true
foreach ($endpoint in $endpoints) {
    $result = Test-HttpEndpoint -url $endpoint.Url -serviceName $endpoint.Name
    if (-not $result) {
        $allEndpointsOk = $false
    }
}
Write-Host ""

# Check network connectivity
Write-Host "4. Checking network connectivity..." -ForegroundColor Yellow
$networkExists = docker network ls --filter "name=dop-network" --format "{{.Name}}"
if ($networkExists) {
    Write-Host "  ✓ Docker network 'dop-network' exists" -ForegroundColor Green
    
    # Get network details
    $networkContainers = docker network inspect dop-network --format '{{range .Containers}}{{.Name}} {{end}}' 2>$null
    if ($networkContainers) {
        $containerCount = ($networkContainers -split " ").Count - 1
        Write-Host "  ✓ $containerCount containers connected to network" -ForegroundColor Green
    }
}
else {
    Write-Host "  ✗ Docker network 'dop-network' does not exist" -ForegroundColor Red
    $allEndpointsOk = $false
}
Write-Host ""

# Test backend-to-database connectivity
Write-Host "5. Testing inter-service connectivity..." -ForegroundColor Yellow
try {
    $backendLogs = docker logs dop-backend --tail 50 2>&1
    if ($backendLogs -match "PostgreSQL is up") {
        Write-Host "  ✓ Backend can connect to PostgreSQL" -ForegroundColor Green
    }
    if ($backendLogs -match "Redis is up") {
        Write-Host "  ✓ Backend can connect to Redis" -ForegroundColor Green
    }
    if ($backendLogs -match "MinIO is up") {
        Write-Host "  ✓ Backend can connect to MinIO" -ForegroundColor Green
    }
}
catch {
    Write-Host "  ⚠ Could not verify backend connectivity" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verification Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($allRunning -and $allEndpointsOk) {
    Write-Host "✓ All services are running and healthy!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Access the services at:" -ForegroundColor Cyan
    Write-Host "  - Frontend:          http://localhost:3000" -ForegroundColor White
    Write-Host "  - Backend API:       http://localhost:8000" -ForegroundColor White
    Write-Host "  - API Docs:          http://localhost:8000/docs" -ForegroundColor White
    Write-Host "  - Airflow UI:        http://localhost:8080 (admin/admin123)" -ForegroundColor White
    Write-Host "  - MinIO Console:     http://localhost:9001 (minioadmin/minioadmin123)" -ForegroundColor White
    Write-Host "  - PostgreSQL:        localhost:5432 (dop_user/dop_password)" -ForegroundColor White
    Write-Host "  - Redis:             localhost:6379" -ForegroundColor White
}
else {$composeCmd logs [service-name]" -ForegroundColor White
    Write-Host "  2. Restart services: $composeCmd restart" -ForegroundColor White
    Write-Host "  3. Rebuild containers: $composeCmd
    Write-Host "Troubleshooting steps:" -ForegroundColor Cyan
    Write-Host "  1. Check logs: docker-compose logs [service-name]" -ForegroundColor White
    Write-Host "  2. Restart services: docker-compose restart" -ForegroundColor White
    Write-Host "  3. Rebuild containers: docker-compose up --build -d" -ForegroundColor White
    Write-Host "  4. Check resource usage: docker stats" -ForegroundColor White
}

Write-Host ""
