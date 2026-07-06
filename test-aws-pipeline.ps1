# Run End-to-End AWS Pipeline Smoke Test
# Tests complete pipeline flow with S3, Glue, CloudWatch, and Snowflake

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "End-to-End AWS Pipeline Smoke Test" -ForegroundColor Cyan
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

# Run smoke test
Write-Host ""
Write-Host "Running AWS pipeline smoke test..." -ForegroundColor Yellow
Write-Host ""

python test_aws_pipeline_smoke.py

$exitCode = $LASTEXITCODE

# Return to root directory
Set-Location -Path ".."

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "✓ All smoke tests passed!" -ForegroundColor Green
} else {
    Write-Host "✗ Some smoke tests failed!" -ForegroundColor Red
    Write-Host "Please check logs for details" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

exit $exitCode
