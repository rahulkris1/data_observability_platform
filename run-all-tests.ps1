# Run All Integration Tests
# Usage: .\run-all-tests.ps1 [options]

param(
    [switch]$Backend,
    [switch]$Frontend,
    [switch]$Coverage,
    [switch]$Fast
)

$ErrorActionPreference = "Stop"

Write-Host "🧪 Data Observability Platform - Integration Tests" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

$script:backendFailed = $false
$script:frontendFailed = $false

# Run backend tests if requested or if running all
if ($Backend -or (-not $Frontend)) {
    Write-Host "📦 BACKEND TESTS" -ForegroundColor Yellow
    Write-Host "================" -ForegroundColor Yellow
    
    $backendArgs = @()
    if ($Coverage) { $backendArgs += "-Coverage" }
    if ($Fast) { $backendArgs += "-Fast" }
    
    & "$PSScriptRoot\run-backend-tests.ps1" @backendArgs
    
    if ($LASTEXITCODE -ne 0) {
        $script:backendFailed = $true
        Write-Host "`n❌ Backend tests failed" -ForegroundColor Red
    } else {
        Write-Host "`n✅ Backend tests passed" -ForegroundColor Green
    }
    
    Write-Host "`n"
}

# Run frontend tests if requested or if running all
if ($Frontend -or (-not $Backend)) {
    Write-Host "🎨 FRONTEND TESTS" -ForegroundColor Yellow
    Write-Host "=================" -ForegroundColor Yellow
    
    $frontendArgs = @()
    if ($Coverage) { $frontendArgs += "-Coverage" }
    
    & "$PSScriptRoot\run-frontend-tests.ps1" @frontendArgs
    
    if ($LASTEXITCODE -ne 0) {
        $script:frontendFailed = $true
        Write-Host "`n❌ Frontend tests failed" -ForegroundColor Red
    } else {
        Write-Host "`n✅ Frontend tests passed" -ForegroundColor Green
    }
}

# Summary
Write-Host "`n" + ("=" * 50) -ForegroundColor Cyan
Write-Host "TEST SUMMARY" -ForegroundColor Cyan
Write-Host ("=" * 50) -ForegroundColor Cyan

if ($Backend -or (-not $Frontend)) {
    if ($script:backendFailed) {
        Write-Host "❌ Backend:  FAILED" -ForegroundColor Red
    } else {
        Write-Host "✅ Backend:  PASSED" -ForegroundColor Green
    }
}

if ($Frontend -or (-not $Backend)) {
    if ($script:frontendFailed) {
        Write-Host "❌ Frontend: FAILED" -ForegroundColor Red
    } else {
        Write-Host "✅ Frontend: PASSED" -ForegroundColor Green
    }
}

Write-Host ("=" * 50) -ForegroundColor Cyan

if ($Coverage) {
    Write-Host "`n📊 Coverage Reports:" -ForegroundColor Cyan
    if ($Backend -or (-not $Frontend)) {
        Write-Host "   Backend:  backend/htmlcov/index.html" -ForegroundColor Gray
    }
    if ($Frontend -or (-not $Backend)) {
        Write-Host "   Frontend: frontend/coverage/lcov-report/index.html" -ForegroundColor Gray
    }
}

# Exit with error if any tests failed
if ($script:backendFailed -or $script:frontendFailed) {
    exit 1
} else {
    Write-Host "`n🎉 All integration tests passed!" -ForegroundColor Green
    exit 0
}
