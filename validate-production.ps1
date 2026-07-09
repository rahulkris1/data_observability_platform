# Validate Production Environment Configuration
# This script validates that the production environment is correctly configured

param(
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"
$testsPassed = 0
$testsFailed = 0
$warnings = 0

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Production Environment Validation" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

function Test-Configuration {
    param(
        [string]$TestName,
        [scriptblock]$TestScript
    )
    
    Write-Host "Testing: $TestName" -ForegroundColor Yellow -NoNewline
    
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

function Test-Warning {
    param(
        [string]$Message
    )
    Write-Host "   ⚠️  WARNING: $Message" -ForegroundColor Yellow
    $script:warnings++
}

# Test 1: Check if Docker is running
Test-Configuration "Docker is running" {
    try {
        docker info | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Test 2: Backend .env.production exists
Test-Configuration "Backend .env.production exists" {
    Test-Path "backend\.env.production"
}

# Test 3: Frontend .env.production exists
Test-Configuration "Frontend .env.production exists" {
    Test-Path "frontend\.env.production"
}

# Test 4: Backend startup.production.sh exists
Test-Configuration "Backend startup.production.sh exists" {
    Test-Path "backend\startup.production.sh"
}

# Test 5: Production Dockerfiles exist
Test-Configuration "Production Dockerfiles exist" {
    (Test-Path "docker\backend\Dockerfile.production") -and
    (Test-Path "docker\frontend\Dockerfile.production")
}

# Test 6: docker-compose.production.yml exists
Test-Configuration "docker-compose.production.yml exists" {
    Test-Path "docker-compose.production.yml"
}

# Test 7: Check for default passwords in backend .env
Write-Host "Testing: Security - checking for default passwords" -ForegroundColor Yellow -NoNewline
$envContent = Get-Content "backend\.env.production" -Raw -ErrorAction SilentlyContinue
if ($envContent -match "CHANGE_THIS") {
    Write-Host " ⚠️  WARNING" -ForegroundColor Yellow
    Test-Warning "Default passwords/keys found in backend .env.production"
    Test-Warning "Please update all 'CHANGE_THIS' values before production deployment"
}
else {
    Write-Host " ✅ PASS" -ForegroundColor Green
    $testsPassed++
}

# Test 8: Check required environment variables in backend
Write-Host "Testing: Backend environment variables" -ForegroundColor Yellow -NoNewline
$requiredVars = @(
    "APP_NAME",
    "DEBUG",
    "POSTGRES_HOST",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
    "REDIS_HOST",
    "REDIS_URL",
    "STORAGE_PROVIDER",
    "CELERY_BROKER_URL"
)

$missingVars = @()
foreach ($var in $requiredVars) {
    if ($envContent -notmatch "$var=") {
        $missingVars += $var
    }
}

if ($missingVars.Count -eq 0) {
    Write-Host " ✅ PASS" -ForegroundColor Green
    $testsPassed++
}
else {
    Write-Host " ❌ FAIL" -ForegroundColor Red
    foreach ($var in $missingVars) {
        Write-Host "   Missing: $var" -ForegroundColor Red
    }
    $testsFailed++
}

# Test 9: Check DEBUG is set to False
Test-Configuration "DEBUG mode is disabled" {
    $envContent -match 'DEBUG=False'
}

# Test 10: Check frontend environment variables
Write-Host "Testing: Frontend environment variables" -ForegroundColor Yellow -NoNewline
$frontendEnv = Get-Content "frontend\.env.production" -Raw -ErrorAction SilentlyContinue
$requiredFrontendVars = @(
    "NEXT_PUBLIC_API_URL",
    "NEXT_PUBLIC_API_VERSION",
    "NODE_ENV"
)

$missingFrontendVars = @()
foreach ($var in $requiredFrontendVars) {
    if ($frontendEnv -notmatch "$var=") {
        $missingFrontendVars += $var
    }
}

if ($missingFrontendVars.Count -eq 0) {
    Write-Host " ✅ PASS" -ForegroundColor Green
    $testsPassed++
}
else {
    Write-Host " ❌ FAIL" -ForegroundColor Red
    foreach ($var in $missingFrontendVars) {
        Write-Host "   Missing: $var" -ForegroundColor Red
    }
    $testsFailed++
}

# Test 11: Check if startup.production.sh is executable (has content)
Test-Configuration "Startup script has content" {
    $startupContent = Get-Content "backend\startup.production.sh" -Raw -ErrorAction SilentlyContinue
    $startupContent.Length -gt 100
}

# Test 12: Check backend requirements.txt contains gunicorn
Test-Configuration "Backend requirements includes gunicorn" {
    $requirements = Get-Content "backend\requirements.txt" -Raw -ErrorAction SilentlyContinue
    $requirements -match "gunicorn"
}

# Test 13: Validate docker-compose.production.yml syntax
Test-Configuration "docker-compose.production.yml is valid YAML" {
    try {
        docker-compose -f docker-compose.production.yml config | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Test 14: Check for proper network configuration
Test-Configuration "Production network is configured" {
    $composeContent = Get-Content "docker-compose.production.yml" -Raw
    $composeContent -match "dop-prod-network"
}

# Test 15: Check for health checks in docker-compose
Test-Configuration "Health checks are configured" {
    $composeContent = Get-Content "docker-compose.production.yml" -Raw
    ($composeContent -match "healthcheck:") -and
    ($composeContent -match "test:")
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Validation Summary" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Tests Passed:  $testsPassed" -ForegroundColor Green
Write-Host "Tests Failed:  $testsFailed" -ForegroundColor $(if ($testsFailed -gt 0) { "Red" } else { "White" })
Write-Host "Warnings:      $warnings" -ForegroundColor $(if ($warnings -gt 0) { "Yellow" } else { "White" })
Write-Host ""

if ($testsFailed -eq 0 -and $warnings -eq 0) {
    Write-Host "✅ Production environment is ready for deployment!" -ForegroundColor Green
    exit 0
}
elseif ($testsFailed -eq 0 -and $warnings -gt 0) {
    Write-Host "⚠️  Production environment has warnings. Review before deployment." -ForegroundColor Yellow
    exit 0
}
else {
    Write-Host "❌ Production environment has errors. Fix them before deployment." -ForegroundColor Red
    exit 1
}
