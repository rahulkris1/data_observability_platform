# Verify Production Frontend Deployment
# This script verifies that the frontend is running correctly in production mode

param(
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"
$testsPassed = 0
$testsFailed = 0

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Frontend Production Verification" -ForegroundColor Cyan
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

# Wait for frontend to be ready
Write-Host "⏳ Waiting for frontend to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Test 1: Frontend home page
Test-Endpoint "Frontend home page" "http://localhost:3000"

# Test 2: Frontend health endpoint
Test-Endpoint "Frontend health endpoint" "http://localhost:3000/api/health"

# Test 3: Check if frontend container is running
Test-Service "Frontend container is running" {
    $container = docker ps --filter "name=dop-frontend-prod" --filter "status=running" --format "{{.Names}}"
    $container -eq "dop-frontend-prod"
}

# Test 4: Check if frontend container is healthy
Test-Service "Frontend container is healthy" {
    $health = docker inspect --format='{{.State.Health.Status}}' dop-frontend-prod 2>$null
    $health -eq "healthy"
}

# Test 5: Check frontend logs for errors
Write-Host "Testing: Frontend logs (no critical errors)" -ForegroundColor Yellow -NoNewline
$logs = docker logs dop-frontend-prod --tail 100 2>&1
$criticalErrors = $logs | Select-String -Pattern "ERROR|CRITICAL|Failed" -CaseSensitive:$false
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

# Test 6: Check if Node.js process is running
Write-Host "Testing: Node.js process is running" -ForegroundColor Yellow -NoNewline
$processes = docker exec dop-frontend-prod ps aux 2>$null
if ($processes -match "node") {
    Write-Host " ✅ PASS" -ForegroundColor Green
    $testsPassed++
}
else {
    Write-Host " ❌ FAIL" -ForegroundColor Red
    $testsFailed++
}

# Test 7: Test frontend-backend communication
Write-Host "Testing: Frontend-Backend communication" -ForegroundColor Yellow -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -Method GET -TimeoutSec 10 -ErrorAction Stop
    # Check if the page loads without backend connection errors
    if ($response.Content -notmatch "Failed to fetch" -and $response.Content -notmatch "Network Error") {
        Write-Host " ✅ PASS" -ForegroundColor Green
        $testsPassed++
    }
    else {
        Write-Host " ⚠️  WARNING (Backend connection issues detected)" -ForegroundColor Yellow
    }
}
catch {
    Write-Host " ❌ FAIL" -ForegroundColor Red
    $testsFailed++
}

# Test 8: Check if production build is being served
Write-Host "Testing: Production build is active" -ForegroundColor Yellow -NoNewline
$env = docker exec dop-frontend-prod env 2>$null
if ($env -match "NODE_ENV=production") {
    Write-Host " ✅ PASS" -ForegroundColor Green
    $testsPassed++
}
else {
    Write-Host " ❌ FAIL" -ForegroundColor Red
    $testsFailed++
}

# Test 9: Check static assets are being served
Test-Endpoint "Static assets (_next/static)" "http://localhost:3000/_next/static/chunks/webpack.js" 200

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Verification Summary" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Tests Passed:  $testsPassed" -ForegroundColor Green
Write-Host "Tests Failed:  $testsFailed" -ForegroundColor $(if ($testsFailed -gt 0) { "Red" } else { "White" })
Write-Host ""

if ($testsFailed -eq 0) {
    Write-Host "✅ Frontend is running successfully in production mode!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Access points:" -ForegroundColor Cyan
    Write-Host "   Frontend:  http://localhost:3000" -ForegroundColor White
    Write-Host "   Health:    http://localhost:3000/api/health" -ForegroundColor White
    exit 0
}
else {
    Write-Host "❌ Frontend verification failed. Check the logs for details." -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting commands:" -ForegroundColor Cyan
    Write-Host "   docker logs dop-frontend-prod" -ForegroundColor White
    Write-Host "   docker-compose -f docker-compose.production.yml ps" -ForegroundColor White
    exit 1
}
