# Production Deployment Validation Script
# Validates that all production services are running correctly

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Production Deployment Validation" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorCount = 0
$WarningCount = 0

# Function to test HTTP endpoint
function Test-HttpEndpoint {
    param(
        [string]$Url,
        [string]$Description,
        [int]$ExpectedStatusCode = 200,
        [int]$TimeoutSeconds = 30
    )
    
    try {
        Write-Host "Testing $Description..." -ForegroundColor Yellow
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec $TimeoutSeconds -UseBasicParsing
        
        if ($response.StatusCode -eq $ExpectedStatusCode) {
            Write-Host "✅ $Description is responding (Status: $($response.StatusCode))" -ForegroundColor Green
            return $true
        } else {
            Write-Host "⚠️  $Description responded with unexpected status: $($response.StatusCode)" -ForegroundColor Yellow
            $script:WarningCount++
            return $false
        }
    } catch {
        Write-Host "❌ $Description is not responding: $($_.Exception.Message)" -ForegroundColor Red
        $script:ErrorCount++
        return $false
    }
}

# Function to check Docker container status
function Test-ContainerHealth {
    param(
        [string]$ContainerName,
        [string]$Description
    )
    
    Write-Host "Checking $Description container..." -ForegroundColor Yellow
    
    try {
        $container = docker ps --filter "name=$ContainerName" --format "{{.Names}}\t{{.Status}}" | Select-String $ContainerName
        
        if ($container) {
            $status = $container.ToString()
            if ($status -match "Up") {
                if ($status -match "healthy") {
                    Write-Host "✅ $Description is running and healthy" -ForegroundColor Green
                    return $true
                } elseif ($status -match "health: starting") {
                    Write-Host "⚠️  $Description is starting up" -ForegroundColor Yellow
                    $script:WarningCount++
                    return $false
                } else {
                    Write-Host "✅ $Description is running" -ForegroundColor Green
                    return $true
                }
            } else {
                Write-Host "❌ $Description is not running properly: $status" -ForegroundColor Red
                $script:ErrorCount++
                return $false
            }
        } else {
            Write-Host "❌ $Description container not found" -ForegroundColor Red
            $script:ErrorCount++
            return $false
        }
    } catch {
        Write-Host "❌ Error checking $Description: $($_.Exception.Message)" -ForegroundColor Red
        $script:ErrorCount++
        return $false
    }
}

Write-Host "1. Checking Docker Containers..." -ForegroundColor Cyan
Write-Host "---------------------------------------------"

# Check all production containers
Test-ContainerHealth "dop-postgres-prod" "PostgreSQL"
Test-ContainerHealth "dop-redis-prod" "Redis"
Test-ContainerHealth "dop-minio-prod" "MinIO"
Test-ContainerHealth "dop-backend-prod" "Backend API"
Test-ContainerHealth "dop-frontend-prod" "Frontend"
Test-ContainerHealth "dop-celery-worker-prod" "Celery Worker"
Test-ContainerHealth "dop-airflow-webserver-prod" "Airflow Webserver"
Test-ContainerHealth "dop-airflow-scheduler-prod" "Airflow Scheduler"

Write-Host ""
Write-Host "2. Testing HTTP Endpoints..." -ForegroundColor Cyan
Write-Host "---------------------------------------------"

# Wait a moment for services to be fully ready
Start-Sleep -Seconds 5

# Test backend health endpoint
Test-HttpEndpoint "http://localhost:8000/health" "Backend Health Endpoint"

# Test backend API docs
Test-HttpEndpoint "http://localhost:8000/docs" "Backend API Documentation"

# Test frontend health endpoint
Test-HttpEndpoint "http://localhost:3000/api/health" "Frontend Health Endpoint"

# Test frontend main page
Test-HttpEndpoint "http://localhost:3000" "Frontend Main Page"

# Test MinIO
Test-HttpEndpoint "http://localhost:9000/minio/health/live" "MinIO Health Check"

# Test Airflow (may require authentication, so we just check if it responds)
try {
    $airflowResponse = Invoke-WebRequest -Uri "http://localhost:8080/health" -TimeoutSec 10 -UseBasicParsing -ErrorAction SilentlyContinue
    Write-Host "✅ Airflow Webserver is responding" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Airflow Webserver check inconclusive (may require authentication)" -ForegroundColor Yellow
    $WarningCount++
}

Write-Host ""
Write-Host "3. Testing Backend API..." -ForegroundColor Cyan
Write-Host "---------------------------------------------"

# Test backend API version endpoint
Test-HttpEndpoint "http://localhost:8000/api/v1/health" "Backend API v1 Health"

Write-Host ""
Write-Host "4. Checking Service Logs for Errors..." -ForegroundColor Cyan
Write-Host "---------------------------------------------"

# Check backend logs for critical errors
Write-Host "Checking backend logs..." -ForegroundColor Yellow
$backendLogs = docker logs dop-backend-prod --tail 50 2>&1

if ($backendLogs -match "ERROR|CRITICAL|Exception" -and $backendLogs -notmatch "No errors") {
    Write-Host "⚠️  Backend logs contain error messages" -ForegroundColor Yellow
    $WarningCount++
} else {
    Write-Host "✅ Backend logs look clean" -ForegroundColor Green
}

# Check frontend logs for critical errors
Write-Host "Checking frontend logs..." -ForegroundColor Yellow
$frontendLogs = docker logs dop-frontend-prod --tail 50 2>&1

if ($frontendLogs -match "ERROR|Error:" -and $frontendLogs -notmatch "No errors") {
    Write-Host "⚠️  Frontend logs contain error messages" -ForegroundColor Yellow
    $WarningCount++
} else {
    Write-Host "✅ Frontend logs look clean" -ForegroundColor Green
}

Write-Host ""
Write-Host "5. Testing Frontend-Backend Communication..." -ForegroundColor Cyan
Write-Host "---------------------------------------------"

# Test if frontend can reach backend through Docker network
Write-Host "Testing frontend-backend connectivity..." -ForegroundColor Yellow

try {
    # Execute a curl command from frontend container to backend
    $result = docker exec dop-frontend-prod node -e "require('http').get('http://backend:8000/health', (r) => {console.log('Status:', r.statusCode); process.exit(r.statusCode === 200 ? 0 : 1)})" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Frontend can communicate with backend" -ForegroundColor Green
    } else {
        Write-Host "❌ Frontend cannot reach backend" -ForegroundColor Red
        $ErrorCount++
    }
} catch {
    Write-Host "⚠️  Could not test frontend-backend communication" -ForegroundColor Yellow
    $WarningCount++
}

Write-Host ""
Write-Host "6. Testing Database Connectivity..." -ForegroundColor Cyan
Write-Host "---------------------------------------------"

Write-Host "Testing database connection from backend..." -ForegroundColor Yellow
try {
    $dbTest = docker exec dop-backend-prod pg_isready -h postgres -U dop_prod_user 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Backend can connect to PostgreSQL" -ForegroundColor Green
    } else {
        Write-Host "❌ Backend cannot connect to PostgreSQL" -ForegroundColor Red
        $ErrorCount++
    }
} catch {
    Write-Host "⚠️  Could not test database connectivity" -ForegroundColor Yellow
    $WarningCount++
}

Write-Host ""
Write-Host "7. Testing Redis Connectivity..." -ForegroundColor Cyan
Write-Host "---------------------------------------------"

Write-Host "Testing Redis connection from backend..." -ForegroundColor Yellow
try {
    $redisTest = docker exec dop-backend-prod redis-cli -h redis -p 6379 ping 2>&1
    if ($redisTest -match "PONG") {
        Write-Host "✅ Backend can connect to Redis" -ForegroundColor Green
    } else {
        Write-Host "❌ Backend cannot connect to Redis" -ForegroundColor Red
        $ErrorCount++
    }
} catch {
    Write-Host "⚠️  Could not test Redis connectivity" -ForegroundColor Yellow
    $WarningCount++
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Validation Summary" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Errors: $ErrorCount" -ForegroundColor $(if ($ErrorCount -eq 0) { "Green" } else { "Red" })
Write-Host "Warnings: $WarningCount" -ForegroundColor $(if ($WarningCount -eq 0) { "Green" } else { "Yellow" })
Write-Host ""

if ($ErrorCount -eq 0 -and $WarningCount -eq 0) {
    Write-Host "✅ Production deployment is HEALTHY!" -ForegroundColor Green
    Write-Host "   All services are running correctly" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Access your application at:" -ForegroundColor Cyan
    Write-Host "   Frontend: http://localhost:3000" -ForegroundColor White
    Write-Host "   Backend:  http://localhost:8000/docs" -ForegroundColor White
    exit 0
} elseif ($ErrorCount -eq 0) {
    Write-Host "⚠️  Production deployment has WARNINGS" -ForegroundColor Yellow
    Write-Host "   Services are running but some checks failed" -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "❌ Production deployment has ERRORS" -ForegroundColor Red
    Write-Host "   Some services are not running correctly" -ForegroundColor Red
    Write-Host ""
    Write-Host "📋 Troubleshooting:" -ForegroundColor Cyan
    Write-Host "   View all logs:     docker-compose -f docker-compose.production.yml logs" -ForegroundColor Gray
    Write-Host "   View backend logs: docker-compose -f docker-compose.production.yml logs backend" -ForegroundColor Gray
    Write-Host "   View frontend logs: docker-compose -f docker-compose.production.yml logs frontend" -ForegroundColor Gray
    Write-Host "   Restart services:  docker-compose -f docker-compose.production.yml restart" -ForegroundColor Gray
    exit 1
}
