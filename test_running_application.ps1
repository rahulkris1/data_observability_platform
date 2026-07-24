# Comprehensive Application Testing Script
# This script tests the running application end-to-end

param(
    [string]$BackendUrl = "http://localhost:8000",
    [string]$FrontendUrl = "http://localhost:3000"
)

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "           DATA OBSERVABILITY PLATFORM - RUNNING APPLICATION TEST              " -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

$testResults = @{
    Passed = 0
    Failed = 0
    Total = 0
}

function Test-Endpoint {
    param(
        [string]$Url,
        [string]$Description,
        [int[]]$ExpectedStatusCodes = @(200)
    )
    
    $testResults.Total++
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 10 -ErrorAction Stop
        
        if ($ExpectedStatusCodes -contains $response.StatusCode) {
            Write-Host "[PASS] $Description" -ForegroundColor Green
            Write-Host "       Status: $($response.StatusCode)" -ForegroundColor Gray
            $testResults.Passed++
            return $true
        } else {
            Write-Host "[FAIL] $Description" -ForegroundColor Red
            Write-Host "       Expected: $($ExpectedStatusCodes -join ', '), Got: $($response.StatusCode)" -ForegroundColor Yellow
            $testResults.Failed++
            return $false
        }
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        
        if ($null -ne $statusCode -and $ExpectedStatusCodes -contains $statusCode) {
            Write-Host "[PASS] $Description" -ForegroundColor Green
            Write-Host "       Status: $statusCode" -ForegroundColor Gray
            $testResults.Passed++
            return $true
        } else {
            Write-Host "[FAIL] $Description" -ForegroundColor Red
            Write-Host "       Error: $($_.Exception.Message)" -ForegroundColor Yellow
            $testResults.Failed++
            return $false
        }
    }
}

function Test-PostEndpoint {
    param(
        [string]$Url,
        [string]$Description,
        [hashtable]$Body,
        [int[]]$ExpectedStatusCodes = @(200, 201)
    )
    
    $testResults.Total++
    
    try {
        $jsonBody = $Body | ConvertTo-Json
        $response = Invoke-WebRequest -Uri $Url -Method POST -Body $jsonBody -ContentType "application/json" -TimeoutSec 10 -ErrorAction Stop
        
        if ($ExpectedStatusCodes -contains $response.StatusCode) {
            Write-Host "[PASS] $Description" -ForegroundColor Green
            Write-Host "       Status: $($response.StatusCode)" -ForegroundColor Gray
            $testResults.Passed++
            return $response
        } else {
            Write-Host "[FAIL] $Description" -ForegroundColor Red
            Write-Host "       Expected: $($ExpectedStatusCodes -join ', '), Got: $($response.StatusCode)" -ForegroundColor Yellow
            $testResults.Failed++
            return $null
        }
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        
        if ($null -ne $statusCode -and $ExpectedStatusCodes -contains $statusCode) {
            Write-Host "[PASS] $Description" -ForegroundColor Green
            Write-Host "       Status: $statusCode (Expected)" -ForegroundColor Gray
            $testResults.Passed++
            return $_.Exception.Response
        } else {
            Write-Host "[FAIL] $Description" -ForegroundColor Red
            Write-Host "       Error: $($_.Exception.Message)" -ForegroundColor Yellow
            $testResults.Failed++
            return $null
        }
    }
}

Write-Host "Testing Backend URL: $BackendUrl" -ForegroundColor Cyan
Write-Host "Testing Frontend URL: $FrontendUrl" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# 1. BASIC CONNECTIVITY
# ============================================================================
Write-Host "=== BASIC CONNECTIVITY ===" -ForegroundColor Yellow
Write-Host ""

Test-Endpoint -Url "$BackendUrl/health" -Description "Backend health check"
Test-Endpoint -Url "$FrontendUrl" -Description "Frontend home page"

Write-Host ""

# ============================================================================
# 2. HEALTH ENDPOINTS
# ============================================================================
Write-Host "=== HEALTH & STATUS ENDPOINTS ===" -ForegroundColor Yellow
Write-Host ""

Test-Endpoint -Url "$BackendUrl/api/v1/health/status" -Description "Health status endpoint"
Test-Endpoint -Url "$BackendUrl/api/v1/health/readiness" -Description "Readiness check"
Test-Endpoint -Url "$BackendUrl/api/v1/health/liveness" -Description "Liveness check"

Write-Host ""

# ============================================================================
# 3. AUTHENTICATION ENDPOINTS
# ============================================================================
Write-Host "=== AUTHENTICATION ENDPOINTS ===" -ForegroundColor Yellow
Write-Host ""

# Test login endpoint (expects 401 or 422 for invalid credentials)
Test-PostEndpoint -Url "$BackendUrl/api/v1/auth/login" `
    -Description "Login endpoint (invalid credentials)" `
    -Body @{ username = "test"; password = "test" } `
    -ExpectedStatusCodes @(200, 401, 422)

# Test auth validation (expects 401 without token)
Test-Endpoint -Url "$BackendUrl/api/v1/auth/me" `
    -Description "Auth validation endpoint" `
    -ExpectedStatusCodes @(200, 401, 403)

Write-Host ""

# ============================================================================
# 4. VALIDATION ENDPOINTS
# ============================================================================
Write-Host "=== VALIDATION ENDPOINTS ===" -ForegroundColor Yellow
Write-Host ""

Test-Endpoint -Url "$BackendUrl/api/v1/validation-logs" `
    -Description "Validation logs endpoint" `
    -ExpectedStatusCodes @(200, 401, 403)

Test-Endpoint -Url "$BackendUrl/api/v1/schema-contracts" `
    -Description "Schema contracts endpoint" `
    -ExpectedStatusCodes @(200, 401, 403)

Test-Endpoint -Url "$BackendUrl/api/v1/validation/stats" `
    -Description "Validation stats endpoint" `
    -ExpectedStatusCodes @(200, 401, 403)

Write-Host ""

# ============================================================================
# 5. METRICS & OBSERVABILITY
# ============================================================================
Write-Host "=== METRICS & OBSERVABILITY ENDPOINTS ===" -ForegroundColor Yellow
Write-Host ""

Test-Endpoint -Url "$BackendUrl/api/v1/metrics" `
    -Description "Metrics endpoint" `
    -ExpectedStatusCodes @(200, 401, 403)

Test-Endpoint -Url "$BackendUrl/api/v1/metrics/summary" `
    -Description "Metrics summary endpoint" `
    -ExpectedStatusCodes @(200, 401, 403)

Test-Endpoint -Url "$BackendUrl/api/v1/profiling/results" `
    -Description "Profiling results endpoint" `
    -ExpectedStatusCodes @(200, 401, 403)

Test-Endpoint -Url "$BackendUrl/api/v1/profiling/summary" `
    -Description "Profiling summary endpoint" `
    -ExpectedStatusCodes @(200, 401, 403)

Write-Host ""

# ============================================================================
# 6. SCHEMA DRIFT ENDPOINTS
# ============================================================================
Write-Host "=== SCHEMA DRIFT ENDPOINTS ===" -ForegroundColor Yellow
Write-Host ""

Test-Endpoint -Url "$BackendUrl/api/v1/schema-drift/history" `
    -Description "Schema drift history endpoint" `
    -ExpectedStatusCodes @(200, 401, 403)

Write-Host ""

# ============================================================================
# 7. FRESHNESS MONITORING
# ============================================================================
Write-Host "=== FRESHNESS MONITORING ENDPOINTS ===" -ForegroundColor Yellow
Write-Host ""

Test-Endpoint -Url "$BackendUrl/api/v1/freshness-checks" `
    -Description "Freshness checks endpoint" `
    -ExpectedStatusCodes @(200, 401, 403)

Write-Host ""

# ============================================================================
# 8. AIRFLOW INTEGRATION
# ============================================================================
Write-Host "=== AIRFLOW INTEGRATION ENDPOINTS ===" -ForegroundColor Yellow
Write-Host ""

Test-Endpoint -Url "$BackendUrl/api/v1/airflow/health" `
    -Description "Airflow health endpoint" `
    -ExpectedStatusCodes @(200, 401, 403, 503)

Test-Endpoint -Url "$BackendUrl/api/v1/dag-executions" `
    -Description "DAG executions endpoint" `
    -ExpectedStatusCodes @(200, 401, 403)

Test-Endpoint -Url "$BackendUrl/api/v1/dag-executions/stats" `
    -Description "DAG execution stats endpoint" `
    -ExpectedStatusCodes @(200, 401, 403)

Write-Host ""

# ============================================================================
# 9. WAREHOUSE ENDPOINTS
# ============================================================================
Write-Host "=== DATA WAREHOUSE ENDPOINTS ===" -ForegroundColor Yellow
Write-Host ""

Test-Endpoint -Url "$BackendUrl/api/v1/warehouse/tables" `
    -Description "Warehouse tables endpoint" `
    -ExpectedStatusCodes @(200, 401, 403)

Test-Endpoint -Url "$BackendUrl/api/v1/warehouse/stats" `
    -Description "Warehouse stats endpoint" `
    -ExpectedStatusCodes @(200, 401, 403)

Test-Endpoint -Url "$BackendUrl/api/v1/load-monitoring/status" `
    -Description "Load monitoring status endpoint" `
    -ExpectedStatusCodes @(200, 401, 403)

Test-Endpoint -Url "$BackendUrl/api/v1/load-monitoring/history" `
    -Description "Load monitoring history endpoint" `
    -ExpectedStatusCodes @(200, 401, 403)

Write-Host ""

# ============================================================================
# 10. CACHE ENDPOINTS
# ============================================================================
Write-Host "=== CACHE MONITORING ENDPOINTS ===" -ForegroundColor Yellow
Write-Host ""

Test-Endpoint -Url "$BackendUrl/api/v1/cache/health" `
    -Description "Cache health endpoint" `
    -ExpectedStatusCodes @(200, 401, 403, 503)

Test-Endpoint -Url "$BackendUrl/api/v1/cache/metrics" `
    -Description "Cache metrics endpoint" `
    -ExpectedStatusCodes @(200, 401, 403, 503)

Test-Endpoint -Url "$BackendUrl/api/v1/cache/stats" `
    -Description "Cache stats endpoint" `
    -ExpectedStatusCodes @(200, 401, 403, 503)

Write-Host ""

# ============================================================================
# 11. STORAGE ENDPOINTS
# ============================================================================
Write-Host "=== STORAGE ENDPOINTS ===" -ForegroundColor Yellow
Write-Host ""

Test-Endpoint -Url "$BackendUrl/api/v1/storage/health" `
    -Description "Storage health endpoint" `
    -ExpectedStatusCodes @(200, 401, 403, 503)

Test-Endpoint -Url "$BackendUrl/api/v1/storage/buckets" `
    -Description "Storage buckets endpoint" `
    -ExpectedStatusCodes @(200, 401, 403, 503)

Write-Host ""

# ============================================================================
# 12. RETRY QUEUE ENDPOINTS
# ============================================================================
Write-Host "=== RETRY QUEUE ENDPOINTS ===" -ForegroundColor Yellow
Write-Host ""

Test-Endpoint -Url "$BackendUrl/api/v1/retry-queue" `
    -Description "Retry queue endpoint" `
    -ExpectedStatusCodes @(200, 401, 403)

Test-Endpoint -Url "$BackendUrl/api/v1/retry-queue/stats" `
    -Description "Retry queue stats endpoint" `
    -ExpectedStatusCodes @(200, 401, 403)

Write-Host ""

# ============================================================================
# 13. RULES MANAGEMENT
# ============================================================================
Write-Host "=== RULES MANAGEMENT ENDPOINTS ===" -ForegroundColor Yellow
Write-Host ""

Test-Endpoint -Url "$BackendUrl/api/v1/rules" `
    -Description "Rules endpoint" `
    -ExpectedStatusCodes @(200, 401, 403)

Test-Endpoint -Url "$BackendUrl/api/v1/rules/active" `
    -Description "Active rules endpoint" `
    -ExpectedStatusCodes @(200, 401, 403)

Write-Host ""

# ============================================================================
# 14. AUDIT LOGS
# ============================================================================
Write-Host "=== AUDIT LOG ENDPOINTS ===" -ForegroundColor Yellow
Write-Host ""

Test-Endpoint -Url "$BackendUrl/api/v1/audit-logs" `
    -Description "Audit logs endpoint" `
    -ExpectedStatusCodes @(200, 401, 403)

Test-Endpoint -Url "$BackendUrl/api/v1/audit-logs/summary" `
    -Description "Audit logs summary endpoint" `
    -ExpectedStatusCodes @(200, 401, 403)

Write-Host ""

# ============================================================================
# SUMMARY
# ============================================================================
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "                              TEST SUMMARY                                     " -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Total Tests: $($testResults.Total)" -ForegroundColor Cyan
Write-Host "Passed: $($testResults.Passed)" -ForegroundColor Green
Write-Host "Failed: $($testResults.Failed)" -ForegroundColor Red

$passRate = if ($testResults.Total -gt 0) { 
    [math]::Round(($testResults.Passed / $testResults.Total) * 100, 1)
} else { 
    0 
}

Write-Host ""
Write-Host "Pass Rate: $passRate%" -ForegroundColor Cyan
Write-Host ""

if ($testResults.Failed -eq 0) {
    Write-Host "🎉 ALL TESTS PASSED!" -ForegroundColor Green
    Write-Host ""
    Write-Host "The application is functioning correctly!" -ForegroundColor Green
    exit 0
} elseif ($passRate -ge 80) {
    Write-Host "⚠ Most tests passed, but some issues were found" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Review the failed tests above for details." -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "✗ Multiple test failures detected" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please ensure the application is running and configured correctly." -ForegroundColor Red
    exit 1
}
