# Verify Complete Production Deployment
# This script runs all production verification tests

$ErrorActionPreference = "Stop"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Complete Production Deployment Verification" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$totalTests = 0
$totalPassed = 0
$totalFailed = 0

# Step 1: Validate environment configuration
Write-Host "STEP 1: Validating environment configuration..." -ForegroundColor Cyan
Write-Host ""
& .\validate-production.ps1
$envValidation = $LASTEXITCODE
Write-Host ""

if ($envValidation -ne 0) {
    Write-Host "❌ Environment validation failed. Cannot proceed." -ForegroundColor Red
    exit 1
}

# Step 2: Check if services are running
Write-Host "STEP 2: Checking if production services are running..." -ForegroundColor Cyan
Write-Host ""

$runningContainers = docker ps --filter "name=dop.*prod" --format "{{.Names}}"
$expectedContainers = @(
    "dop-postgres-prod",
    "dop-redis-prod",
    "dop-minio-prod",
    "dop-backend-prod",
    "dop-celery-worker-prod",
    "dop-frontend-prod",
    "dop-airflow-webserver-prod",
    "dop-airflow-scheduler-prod"
)

$missingContainers = @()
foreach ($container in $expectedContainers) {
    if ($runningContainers -notcontains $container) {
        $missingContainers += $container
    }
}

if ($missingContainers.Count -gt 0) {
    Write-Host "⚠️  WARNING: Some containers are not running:" -ForegroundColor Yellow
    foreach ($container in $missingContainers) {
        Write-Host "   - $container" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "Run: .\deploy-production.ps1 -Start" -ForegroundColor Cyan
    Write-Host ""
}
else {
    Write-Host "✅ All expected containers are running" -ForegroundColor Green
    Write-Host ""
}

# Step 3: Wait for services to be healthy
Write-Host "STEP 3: Waiting for services to be healthy..." -ForegroundColor Cyan
Write-Host ""

$maxAttempts = 30
$attempt = 1
while ($attempt -le $maxAttempts) {
    $unhealthy = docker ps --filter "name=dop.*prod" --filter "health=unhealthy" --format "{{.Names}}"
    
    if ($unhealthy.Count -eq 0) {
        Write-Host "✅ All services are healthy" -ForegroundColor Green
        break
    }
    
    Write-Host "⏳ Attempt $attempt/$maxAttempts - Waiting for services to be healthy..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    $attempt++
}

if ($attempt -gt $maxAttempts) {
    Write-Host "⚠️  WARNING: Some services may not be fully healthy yet" -ForegroundColor Yellow
}
Write-Host ""

# Step 4: Verify backend
Write-Host "STEP 4: Verifying backend..." -ForegroundColor Cyan
Write-Host ""
& .\verify-backend-production.ps1
$backendVerification = $LASTEXITCODE
Write-Host ""

# Step 5: Verify frontend
Write-Host "STEP 5: Verifying frontend..." -ForegroundColor Cyan
Write-Host ""
& .\verify-frontend-production.ps1
$frontendVerification = $LASTEXITCODE
Write-Host ""

# Step 6: Test frontend-backend integration
Write-Host "STEP 6: Testing frontend-backend integration..." -ForegroundColor Cyan
Write-Host ""

Write-Host "Testing: API connectivity from frontend" -ForegroundColor Yellow -NoNewline
try {
    # Test if frontend can reach backend through internal network
    $result = docker exec dop-frontend-prod node -e "
        const http = require('http');
        const options = {
            hostname: 'backend',
            port: 8000,
            path: '/health',
            method: 'GET',
            timeout: 5000
        };
        const req = http.request(options, (res) => {
            process.exit(res.statusCode === 200 ? 0 : 1);
        });
        req.on('error', () => process.exit(1));
        req.on('timeout', () => process.exit(1));
        req.end();
    " 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✅ PASS" -ForegroundColor Green
    }
    else {
        Write-Host " ❌ FAIL" -ForegroundColor Red
    }
}
catch {
    Write-Host " ❌ FAIL" -ForegroundColor Red
}
Write-Host ""

# Step 7: Display service status
Write-Host "STEP 7: Service status overview..." -ForegroundColor Cyan
Write-Host ""

docker-compose -f docker-compose.production.yml ps
Write-Host ""

# Final Summary
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Deployment Verification Summary" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

$overallSuccess = $true

Write-Host "Environment Validation: " -NoNewline
if ($envValidation -eq 0) {
    Write-Host "✅ PASS" -ForegroundColor Green
}
else {
    Write-Host "❌ FAIL" -ForegroundColor Red
    $overallSuccess = $false
}

Write-Host "Backend Verification:   " -NoNewline
if ($backendVerification -eq 0) {
    Write-Host "✅ PASS" -ForegroundColor Green
}
else {
    Write-Host "❌ FAIL" -ForegroundColor Red
    $overallSuccess = $false
}

Write-Host "Frontend Verification:  " -NoNewline
if ($frontendVerification -eq 0) {
    Write-Host "✅ PASS" -ForegroundColor Green
}
else {
    Write-Host "❌ FAIL" -ForegroundColor Red
    $overallSuccess = $false
}

Write-Host ""

if ($overallSuccess) {
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "✅ PRODUCTION DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Access your application at:" -ForegroundColor Cyan
    Write-Host "   Frontend:  http://localhost:3000" -ForegroundColor White
    Write-Host "   Backend:   http://localhost:8000" -ForegroundColor White
    Write-Host "   API Docs:  http://localhost:8000/docs" -ForegroundColor White
    Write-Host "   Airflow:   http://localhost:8080 (admin/CHANGE_THIS_AIRFLOW_PASSWORD)" -ForegroundColor White
    Write-Host "   MinIO:     http://localhost:9001 (CHANGE_THIS_MINIO_ACCESS_KEY)" -ForegroundColor White
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "   1. Update all default passwords in backend/.env.production" -ForegroundColor White
    Write-Host "   2. Configure CORS origins for your domain" -ForegroundColor White
    Write-Host "   3. Set up SSL/TLS certificates for HTTPS" -ForegroundColor White
    Write-Host "   4. Configure backup strategy for volumes" -ForegroundColor White
    Write-Host "   5. Set up monitoring and alerting" -ForegroundColor White
    exit 0
}
else {
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host "❌ PRODUCTION DEPLOYMENT HAS ISSUES" -ForegroundColor Red
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Cyan
    Write-Host "   View logs:    docker-compose -f docker-compose.production.yml logs" -ForegroundColor White
    Write-Host "   Restart:      .\deploy-production.ps1 -Restart" -ForegroundColor White
    Write-Host "   Clean deploy: .\deploy-production.ps1 -All" -ForegroundColor White
    exit 1
}
