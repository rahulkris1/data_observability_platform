# Complete Production Setup Test
# This script performs a comprehensive test of the entire production configuration

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Data Observability Platform - Production Setup Verification" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

$TotalTests = 0
$PassedTests = 0
$FailedTests = 0
$Warnings = 0

function Test-Step {
    param(
        [string]$StepName,
        [scriptblock]$TestCode,
        [string]$SuccessMessage = "Passed",
        [string]$FailureMessage = "Failed"
    )
    
    $script:TotalTests++
    Write-Host "[$script:TotalTests] Testing: $StepName..." -ForegroundColor Yellow
    
    try {
        $result = & $TestCode
        if ($result) {
            Write-Host "    ✅ $SuccessMessage" -ForegroundColor Green
            $script:PassedTests++
            return $true
        } else {
            Write-Host "    ❌ $FailureMessage" -ForegroundColor Red
            $script:FailedTests++
            return $false
        }
    } catch {
        Write-Host "    ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        $script:FailedTests++
        return $false
    }
}

Write-Host "Phase 1: Environment Validation" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

# Test Docker installation
Test-Step "Docker Installation" {
    try {
        docker --version | Out-Null
        return $true
    } catch {
        return $false
    }
} "Docker is installed" "Docker is not installed"

# Test Docker daemon
Test-Step "Docker Daemon" {
    try {
        docker ps | Out-Null
        return $true
    } catch {
        return $false
    }
} "Docker daemon is running" "Docker daemon is not running"

# Test docker-compose
Test-Step "Docker Compose" {
    try {
        docker-compose --version | Out-Null
        return $true
    } catch {
        return $false
    }
} "docker-compose is available" "docker-compose is not available"

Write-Host ""
Write-Host "Phase 2: Backend Configuration" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

# Backend files
$backendFiles = @{
    ".env.production" = "backend\.env.production"
    "production_config.py" = "backend\config\production_config.py"
    "startup.production.sh" = "backend\startup.production.sh"
    "Dockerfile.production" = "docker\backend\Dockerfile.production"
    "main.py" = "backend\app\main.py"
    "requirements.txt" = "backend\requirements.txt"
}

foreach ($file in $backendFiles.GetEnumerator()) {
    Test-Step "Backend - $($file.Key)" {
        return Test-Path $file.Value
    } "File exists: $($file.Value)" "File missing: $($file.Value)"
}

Write-Host ""
Write-Host "Phase 3: Frontend Configuration" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

# Frontend files
$frontendFiles = @{
    ".env.production" = "frontend\.env.production"
    "next.config.js" = "frontend\next.config.js"
    "package.json" = "frontend\package.json"
    "Dockerfile.production" = "docker\frontend\Dockerfile.production"
    "health.ts" = "frontend\src\pages\api\health.ts"
}

foreach ($file in $frontendFiles.GetEnumerator()) {
    Test-Step "Frontend - $($file.Key)" {
        return Test-Path $file.Value
    } "File exists: $($file.Value)" "File missing: $($file.Value)"
}

Write-Host ""
Write-Host "Phase 4: Docker Compose Configuration" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

# Docker Compose file
Test-Step "docker-compose.production.yml" {
    return Test-Path "docker-compose.production.yml"
} "Docker Compose file exists" "Docker Compose file missing"

# Check services in docker-compose
if (Test-Path "docker-compose.production.yml") {
    $composeContent = Get-Content "docker-compose.production.yml" -Raw
    
    $services = @("backend", "frontend", "postgres", "redis", "minio", "celery-worker", "airflow-webserver", "airflow-scheduler")
    
    foreach ($service in $services) {
        Test-Step "Service: $service" {
            return $composeContent -match "${service}:"
        } "Service defined in docker-compose" "Service not found in docker-compose"
    }
}

Write-Host ""
Write-Host "Phase 5: Deployment Scripts" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

$scripts = @(
    "verify-backend-production-config.ps1",
    "verify-frontend-production-config.ps1",
    "start-production.ps1",
    "validate-production-deployment.ps1",
    "generate-production-keys.ps1"
)

foreach ($script in $scripts) {
    Test-Step "Script: $script" {
        return Test-Path $script
    } "Script exists" "Script missing"
}

Write-Host ""
Write-Host "Phase 6: Documentation" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

$docs = @(
    "PRODUCTION_CONFIGURATION_COMPLETE.md",
    "PRODUCTION_QUICK_START.md",
    "PRODUCTION_CONFIGURATION_SUMMARY.md"
)

foreach ($doc in $docs) {
    Test-Step "Documentation: $doc" {
        return Test-Path $doc
    } "Document exists" "Document missing"
}

Write-Host ""
Write-Host "Phase 7: Security Configuration Check" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

# Check for insecure defaults in .env.production
if (Test-Path "backend\.env.production") {
    $envContent = Get-Content "backend\.env.production" -Raw
    
    $insecurePatterns = @(
        @{Pattern = "CHANGE_THIS"; Name = "Placeholder values"},
        @{Pattern = "changeme"; Name = "Default passwords"}
    )
    
    foreach ($check in $insecurePatterns) {
        $found = $envContent -match $check.Pattern
        if ($found) {
            Write-Host "    ⚠️  WARNING: $($check.Name) detected in .env.production" -ForegroundColor Yellow
            Write-Host "       Run generate-production-keys.ps1 and update the file" -ForegroundColor Gray
            $script:Warnings++
        }
    }
    
    if ($script:Warnings -eq 0) {
        Write-Host "    ✅ No obvious security issues detected" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Phase 8: Port Availability Check" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

$ports = @{
    3000 = "Frontend"
    8000 = "Backend"
    8080 = "Airflow"
    9000 = "MinIO"
    9001 = "MinIO Console"
    5432 = "PostgreSQL"
    6379 = "Redis"
}

foreach ($port in $ports.GetEnumerator()) {
    Test-Step "Port $($port.Key) ($($port.Value))" {
        $connection = Test-NetConnection -ComputerName localhost -Port $port.Key -InformationLevel Quiet -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
        return -not $connection
    } "Port is available" "Port is in use (may conflict)"
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Test Results Summary" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Total Tests:   $TotalTests" -ForegroundColor White
Write-Host "Passed:        $PassedTests" -ForegroundColor Green
Write-Host "Failed:        $FailedTests" -ForegroundColor $(if ($FailedTests -eq 0) { "Green" } else { "Red" })
Write-Host "Warnings:      $Warnings" -ForegroundColor $(if ($Warnings -eq 0) { "Green" } else { "Yellow" })
Write-Host ""

$successRate = [math]::Round(($PassedTests / $TotalTests) * 100, 2)
Write-Host "Success Rate:  $successRate%" -ForegroundColor $(if ($successRate -ge 90) { "Green" } elseif ($successRate -ge 70) { "Yellow" } else { "Red" })

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan

if ($FailedTests -eq 0 -and $Warnings -eq 0) {
    Write-Host ""
    Write-Host "🎉 EXCELLENT! Production configuration is complete and ready!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "  1. Generate secure keys: .\generate-production-keys.ps1" -ForegroundColor White
    Write-Host "  2. Update backend\.env.production with generated keys" -ForegroundColor White
    Write-Host "  3. Start production: .\start-production.ps1" -ForegroundColor White
    Write-Host "  4. Validate deployment: .\validate-production-deployment.ps1" -ForegroundColor White
    Write-Host ""
    exit 0
} elseif ($FailedTests -eq 0) {
    Write-Host ""
    Write-Host "⚠️  Production configuration is complete but has warnings" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Action Required:" -ForegroundColor Cyan
    Write-Host "  1. Generate secure keys: .\generate-production-keys.ps1" -ForegroundColor White
    Write-Host "  2. Update backend\.env.production with generated keys" -ForegroundColor White
    Write-Host "  3. Re-run this test to confirm" -ForegroundColor White
    Write-Host ""
    Write-Host "Then proceed with:" -ForegroundColor Cyan
    Write-Host "  4. Start production: .\start-production.ps1" -ForegroundColor White
    Write-Host "  5. Validate deployment: .\validate-production-deployment.ps1" -ForegroundColor White
    Write-Host ""
    exit 0
} else {
    Write-Host ""
    Write-Host "❌ Some tests failed. Please review the failures above." -ForegroundColor Red
    Write-Host ""
    Write-Host "Common Issues:" -ForegroundColor Cyan
    Write-Host "  - Docker not installed or not running" -ForegroundColor Gray
    Write-Host "  - Missing files (check git status)" -ForegroundColor Gray
    Write-Host "  - Ports in use (stop conflicting services)" -ForegroundColor Gray
    Write-Host ""
    exit 1
}
