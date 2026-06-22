# Start Celery Worker Script
# Starts a local Celery worker for async task processing

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "   Data Observability Platform" -ForegroundColor Cyan
Write-Host "   Celery Worker Startup" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-Not (Test-Path ".venv")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please create a virtual environment first:" -ForegroundColor Yellow
    Write-Host "  python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Check if Redis is running
Write-Host "🔍 Checking Redis connection..." -ForegroundColor Yellow
try {
    $redisTest = python -c "import redis; r = redis.Redis(host='localhost', port=6379); r.ping(); print('OK')" 2>&1
    if ($redisTest -like "*OK*") {
        Write-Host "✅ Redis is running" -ForegroundColor Green
    } else {
        Write-Host "❌ Redis is not responding!" -ForegroundColor Red
        Write-Host "Please start Redis first." -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ Failed to connect to Redis!" -ForegroundColor Red
    Write-Host "Please ensure Redis is running on localhost:6379" -ForegroundColor Yellow
    exit 1
}

# Navigate to backend directory
Set-Location backend

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "   Starting Celery Worker" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Worker Configuration:" -ForegroundColor Cyan
Write-Host "   • Broker: Redis (localhost:6379)" -ForegroundColor White
Write-Host "   • Backend: Redis (localhost:6379)" -ForegroundColor White
Write-Host "   • Concurrency: 4 workers" -ForegroundColor White
Write-Host "   • Queue: default" -ForegroundColor White
Write-Host ""
Write-Host "📊 Available Tasks:" -ForegroundColor Cyan
Write-Host "   • validate_dataset_async" -ForegroundColor White
Write-Host "   • run_validation_rules_async" -ForegroundColor White
Write-Host "   • batch_validate_datasets" -ForegroundColor White
Write-Host "   • profile_dataset_async" -ForegroundColor White
Write-Host "   • calculate_data_quality_score" -ForegroundColor White
Write-Host "   • generate_data_lineage" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Starting worker..." -ForegroundColor Green
Write-Host "   Press Ctrl+C to stop the worker" -ForegroundColor Yellow
Write-Host ""

# Start Celery worker
# Use -A to specify the app, -l for log level, --pool=solo for Windows compatibility
celery -A app.celery_app worker --loglevel=info --pool=solo --concurrency=4 --queues=default

# If worker exits
Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "   Celery Worker Stopped" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
