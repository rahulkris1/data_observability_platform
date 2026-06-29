# Run Frontend Integration Tests
# Usage: .\run-frontend-tests.ps1 [options]

param(
    [switch]$Watch,
    [switch]$Coverage,
    [switch]$CI,
    [string]$TestFile = "",
    [switch]$UpdateSnapshots
)

$ErrorActionPreference = "Stop"

Write-Host "🧪 Running Frontend Integration Tests" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Navigate to frontend directory
Set-Location -Path "$PSScriptRoot\frontend"

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "📥 Installing dependencies..." -ForegroundColor Green
    npm install
}

Write-Host "`n🚀 Running tests..." -ForegroundColor Cyan

# Build npm command
$npmCmd = "npm"
$args = @()

if ($CI) {
    $args += "run", "test:ci"
} elseif ($Coverage) {
    $args += "run", "test:coverage"
} elseif ($Watch) {
    $args += "test"
} else {
    $args += "test", "--", "--watchAll=false"
}

# Add test file if specified
if ($TestFile) {
    $args += $TestFile
} elseif (-not $Watch -and -not $CI -and -not $Coverage) {
    $args += "__tests__/integration"
}

# Add update snapshots flag
if ($UpdateSnapshots) {
    $args += "-u"
}

Write-Host "Command: npm $($args -join ' ')" -ForegroundColor Gray
Write-Host ""

# Run tests
& npm @args

$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "`n✅ All tests passed!" -ForegroundColor Green
    
    if ($Coverage) {
        Write-Host "`n📊 Coverage report generated in frontend/coverage/" -ForegroundColor Cyan
        Write-Host "   View lcov-report/index.html in a browser" -ForegroundColor Cyan
    }
} else {
    Write-Host "`n❌ Tests failed with exit code $exitCode" -ForegroundColor Red
}

# Return to original directory
Set-Location -Path $PSScriptRoot

exit $exitCode
