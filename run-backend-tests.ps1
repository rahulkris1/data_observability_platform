# Run Backend Integration Tests
# Usage: .\run-backend-tests.ps1 [options]

param(
    [switch]$All,
    [switch]$Fast,
    [switch]$Slow,
    [switch]$Spark,
    [switch]$Airflow,
    [switch]$Coverage,
    [string]$TestFile = "",
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

Write-Host "🧪 Running Backend Integration Tests" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Navigate to backend directory
Set-Location -Path "$PSScriptRoot\backend"

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "⚠️  Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "📦 Activating virtual environment..." -ForegroundColor Green
& .\.venv\Scripts\Activate.ps1

# Install dependencies if needed
if (-not (Test-Path ".venv\Lib\site-packages\pytest")) {
    Write-Host "📥 Installing test dependencies..." -ForegroundColor Green
    pip install pytest pytest-asyncio pytest-cov pytest-timeout
    pip install -r requirements.txt
}

# Check if required services are running
Write-Host "`n🔍 Checking required services..." -ForegroundColor Green

# Check PostgreSQL
try {
    $pgResult = Test-NetConnection -ComputerName localhost -Port 5432 -WarningAction SilentlyContinue
    if ($pgResult.TcpTestSucceeded) {
        Write-Host "✅ PostgreSQL is running" -ForegroundColor Green
    } else {
        Write-Host "❌ PostgreSQL is not running on port 5432" -ForegroundColor Red
        Write-Host "   Start it with: docker-compose up -d postgres" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Could not check PostgreSQL status" -ForegroundColor Yellow
}

# Check MinIO
try {
    $minioResult = Test-NetConnection -ComputerName localhost -Port 9000 -WarningAction SilentlyContinue
    if ($minioResult.TcpTestSucceeded) {
        Write-Host "✅ MinIO is running" -ForegroundColor Green
    } else {
        Write-Host "❌ MinIO is not running on port 9000" -ForegroundColor Red
        Write-Host "   Start it with: docker-compose up -d minio" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Could not check MinIO status" -ForegroundColor Yellow
}

# Check Redis
try {
    $redisResult = Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue
    if ($redisResult.TcpTestSucceeded) {
        Write-Host "✅ Redis is running" -ForegroundColor Green
    } else {
        Write-Host "❌ Redis is not running on port 6379" -ForegroundColor Red
        Write-Host "   Start it with: docker-compose up -d redis" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Could not check Redis status" -ForegroundColor Yellow
}

Write-Host "`n🚀 Running tests..." -ForegroundColor Cyan

# Build pytest command
$pytestCmd = "pytest"
$markers = @()

if ($TestFile) {
    $pytestCmd += " $TestFile"
} else {
    $pytestCmd += " tests/integration"
}

# Add markers based on flags
if ($Fast) {
    $markers += "integration and not slow"
} elseif ($Slow) {
    $markers += "slow"
} elseif ($Spark) {
    $markers += "requires_spark"
} elseif ($Airflow) {
    $markers += "requires_airflow"
} elseif (-not $All) {
    # Default: run integration tests but not slow ones
    $markers += "integration and not slow"
}

if ($markers.Count -gt 0) {
    $pytestCmd += " -m `"$($markers -join ' and ')`""
}

# Add verbose flag
if ($Verbose) {
    $pytestCmd += " -v"
} else {
    $pytestCmd += " -v"
}

# Add coverage
if ($Coverage) {
    $pytestCmd += " --cov=app --cov-report=html --cov-report=term"
}

# Add other options
$pytestCmd += " --tb=short --disable-warnings"

Write-Host "Command: $pytestCmd" -ForegroundColor Gray
Write-Host ""

# Run tests
Invoke-Expression $pytestCmd

$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "`n✅ All tests passed!" -ForegroundColor Green
    
    if ($Coverage) {
        Write-Host "`n📊 Coverage report generated in backend/htmlcov/index.html" -ForegroundColor Cyan
    }
} else {
    Write-Host "`n❌ Tests failed with exit code $exitCode" -ForegroundColor Red
}

# Return to original directory
Set-Location -Path $PSScriptRoot

exit $exitCode
