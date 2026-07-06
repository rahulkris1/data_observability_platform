# Test AWS and Snowflake Connectivity
# Validates S3, Glue, CloudWatch, and Snowflake connections

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AWS & Snowflake Connectivity Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & .venv\Scripts\Activate.ps1
} else {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# Change to backend directory
Set-Location -Path "backend"

# Run connectivity validation
Write-Host ""
Write-Host "Running connectivity validation..." -ForegroundColor Yellow
Write-Host ""

python validate_aws_connectivity.py

$exitCode = $LASTEXITCODE

# Return to root directory
Set-Location -Path ".."

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "✓ Connectivity validation passed!" -ForegroundColor Green
} else {
    Write-Host "✗ Connectivity validation failed!" -ForegroundColor Red
    Write-Host "Please check your AWS and Snowflake configuration in .env" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

exit $exitCode
