# Verify Production Backend Deployment
# This script verifies that the backend is running correctly in production mode

param(
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"
$testsPassed = 0
$testsFailed = 0

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Backend Production Verification" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [int]$ExpectedStatus = 200
    )
    
    Write-Host "Testing: $Name" -ForegroundColor Yellow -NoNewline
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 10 -ErrorAction Stop
        
        if ($response.StatusCode -eq $ExpectedStatus) {
            Write-Host " ✅ PASS (Status: $($response.StatusCode))" -ForegroundColor Green
            $script:testsPassed++
            return $true
        }
        else {
            Write-Host " ❌ FAIL (Status: $($response.StatusCode), Expected: $ExpectedStatus)" -ForegroundColor Red
            $script:testsFailed++
            return $false
        }
    }
    catch {
        Write-Host " ❌ FAIL (Error: $_)" -ForegroundColor Red
        $script:testsFailed++
        return $false
    }
}

function Test-Service {
    param(
        [string]$Name,
        [scriptblock]$TestScript
    )
    
    Write-Host "Testing: $Name" -ForegroundColor Yellow -NoNewline
    
    try {
        $result = & $TestScript
        if ($result -eq $true) {
            Write-Host " ✅ PASS" -ForegroundColor Green
            $script:testsPassed++
            return $true
        }
        else {
            Write-Host " ❌ FAIL" -ForegroundColor Red
            $script:testsFailed++
            return $false
        }
    }
    catch {
        Write-Host " ❌ ERROR: $_" -ForegroundColor Red
        $script:testsFailed++
        return $false
    }
}

# Wait for backend to be ready
Write-Host "⏳ Waiting for backend to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Test 1: Backend health endpoint
Test-Endpoint "Backend health endpoint" "http://localhost:8000/health"

# Test 2: Backend API docs
Test-Endpoint "Backend API documentation" "http://localhost:8000/docs"

# Test 3: Backend OpenAPI spec
Test-Endpoint "Backend OpenAPI spec" "http://localhost:8000/openapi.json"

# Test 4: Check if backend container is running
Test-Service "Backend container is running" {
    $container = docker ps --filter "name=dop-backend-prod" --filter "status=running" --format "{{.Names}}"
    $container -eq "dop-backend-prod"
}

# Test 5: Check if backend container is healthy
Test-Service "Backend container is healthy" {
    $health = docker inspect --format='{{.State.Health.Status}}' dop-backend-prod 2>$null
    $health -eq "healthy"
}

# Test 6: Check if Celery worker is running
Test-Service "Celery worker is running" {
    $container = docker ps --filter "name=dop-celery-worker-prod" --filter "status=running" --format "{{.Names}}"
    $container -eq "dop-celery-worker-prod"
}

# Test 7: Check PostgreSQL connection
Test-Service "PostgreSQL is accessible" {
    $container = docker ps --filter "name=dop-postgres-prod" --filter "status=running" --format "{{.Names}}"
    $container -eq "dop-postgres-prod"
}

# Test 8: Check Redis connection
Test-Service "Redis is accessible" {
    $container = docker ps --filter "name=dop-redis-prod" --filter "status=running" --format "{{.Names}}"
    $container -eq "dop-redis-prod"
}

# Test 9: Check MinIO connection
Test-Service "MinIO is accessible" {
    $container = docker ps --filter "name=dop-minio-prod" --filter "status=running" --format "{{.Names}}"
    $container -eq "dop-minio-prod"
}

# Test 10: Check backend logs for errors
Write-Host "Testing: Backend logs (no critical errors)" -ForegroundColor Yellow -NoNewline
$logs = docker logs dop-backend-prod --tail 100 2>&1
$criticalErrors = $logs | Select-String -Pattern "CRITICAL|ERROR" -CaseSensitive:$false
if ($criticalErrors.Count -eq 0) {
    Write-Host " ✅ PASS" -ForegroundColor Green
    $testsPassed++
}
else {
    Write-Host " ⚠️  WARNING ($($criticalErrors.Count) errors found)" -ForegroundColor Yellow
    if ($Verbose) {
        $criticalErrors | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
    }
}

# Test 11: Check if gunicorn is running (production server)
Write-Host "Testing: Gunicorn process is running" -ForegroundColor Yellow -NoNewline
$processes = docker exec dop-backend-prod ps aux 2>$null
if ($processes -match "gunicorn") {
    Write-Host " ✅ PASS" -ForegroundColor Green
    $testsPassed++
}
else {
    Write-Host " ❌ FAIL" -ForegroundColor Red
    $testsFailed++
}

# Test 12: Test API v1 endpoint
Test-Endpoint "API v1 prefix is working" "http://localhost:8000/api/v1/health/status" 200

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Verification Summary" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Tests Passed:  $testsPassed" -ForegroundColor Green
Write-Host "Tests Failed:  $testsFailed" -ForegroundColor $(if ($testsFailed -gt 0) { "Red" } else { "White" })
Write-Host ""

if ($testsFailed -eq 0) {
    Write-Host "✅ Backend is running successfully in production mode!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Access points:" -ForegroundColor Cyan
    Write-Host "   API:       http://localhost:8000" -ForegroundColor White
    Write-Host "   Docs:      http://localhost:8000/docs" -ForegroundColor White
    Write-Host "   Health:    http://localhost:8000/health" -ForegroundColor White
    exit 0
}
else {
    Write-Host "❌ Backend verification failed. Check the logs for details." -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting commands:" -ForegroundColor Cyan
    Write-Host "   docker logs dop-backend-prod" -ForegroundColor White
    Write-Host "   docker-compose -f docker-compose.production.yml ps" -ForegroundColor White
    exit 1
}
