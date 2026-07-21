# Complete End-to-End Workflow Test Script
# Tests: Upload → Ingestion → Validation → Profiling → Audit → Warehouse → Health Score

$BaseUrl = "http://localhost:8000"
$TestResults = @()

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Endpoint,
        [hashtable]$Body = $null,
        [string]$ContentType = "application/json"
    )
    
    Write-Host "`n=== Testing: $Name ===" -ForegroundColor Cyan
    Write-Host "Endpoint: $Method $Endpoint" -ForegroundColor Gray
    
    try {
        $params = @{
            Uri = "$BaseUrl$Endpoint"
            Method = $Method
            ErrorAction = "Stop"
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json -Depth 10)
            $params.ContentType = $ContentType
        }
        
        $response = Invoke-RestMethod @params
        Write-Host "[OK] SUCCESS" -ForegroundColor Green
        
        $global:TestResults += @{
            Test = $Name
            Status = "PASS"
            Endpoint = $Endpoint
            Response = $response
        }
        
        return $response
    }
    catch {
        Write-Host "[FAIL] FAILED: $($_.Exception.Message)" -ForegroundColor Red
        
        $global:TestResults += @{
            Test = $Name
            Status = "FAIL"
            Endpoint = $Endpoint
            Error = $_.Exception.Message
        }
        
        return $null
    }
}

Write-Host "========================================" -ForegroundColor Yellow
Write-Host "Data Observability Platform - E2E Test" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

# 1. Test System Health
Write-Host "`n[PHASE 1] System Health Checks" -ForegroundColor Magenta
Test-Endpoint -Name "Root Health" -Method "GET" -Endpoint "/"
Test-Endpoint -Name "System Health" -Method "GET" -Endpoint "/health"
Test-Endpoint -Name "Airflow Health" -Method "GET" -Endpoint "/api/v1/airflow/health"
Test-Endpoint -Name "Cache Health" -Method "GET" -Endpoint "/api/v1/cache/health"
Test-Endpoint -Name "Metrics Health" -Method "GET" -Endpoint "/api/v1/metrics/health"
Test-Endpoint -Name "Storage Status" -Method "GET" -Endpoint "/api/v1/storage/status"
Test-Endpoint -Name "Glue Health" -Method "GET" -Endpoint "/api/v1/glue/health"

# 2. Test Authentication
Write-Host "`n[PHASE 2] Authentication" -ForegroundColor Magenta
$registerData = @{
    username = "testuser_$(Get-Random)"
    email = "test_$(Get-Random)@example.com"
    password = "TestPass123!"
    full_name = "Test User"
}
$registerResponse = Test-Endpoint -Name "User Registration" -Method "POST" -Endpoint "/api/v1/auth/register" -Body $registerData

if ($registerResponse) {
    $loginData = @{
        username = $registerData.username
        password = $registerData.password
    }
    
    # Note: FastAPI OAuth2 expects form data, not JSON
    $loginResponse = try {
        $body = "username=$($loginData.username)`&password=$($loginData.password)"
        $response = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/login" -Method POST -Body $body -ContentType "application/x-www-form-urlencoded"
        Write-Host "[OK] Login SUCCESS" -ForegroundColor Green
        $response
    } catch {
        Write-Host "[FAIL] Login FAILED: $($_.Exception.Message)" -ForegroundColor Red
        $null
    }
    
    if ($loginResponse -and $loginResponse.access_token) {
        $global:AuthToken = $loginResponse.access_token
        Write-Host "Token obtained: $($AuthToken.Substring(0, 20))..." -ForegroundColor Gray
    }
}

# 3. Test Data Ingestion
Write-Host "`n[PHASE 3] Data Ingestion" -ForegroundColor Magenta

# Create a test CSV file
$testCsvPath = "c:\Users\User\Desktop\data_observability_platform\test_data.csv"
$csvContent = @"
id,name,email,age,city
1,John Doe,john@example.com,30,New York
2,Jane Smith,jane@example.com,25,San Francisco
3,Bob Johnson,bob@example.com,35,Chicago
4,Alice Williams,alice@example.com,28,Boston
5,Charlie Brown,charlie@example.com,32,Seattle
"@
Set-Content -Path $testCsvPath -Value $csvContent
Write-Host "Created test dataset: $testCsvPath" -ForegroundColor Gray

# Test upload (multipart/form-data)
Write-Host "`nTesting file upload..." -ForegroundColor Cyan
try {
    $boundary = [System.Guid]::NewGuid().ToString()
    $LF = "`r`n"
    
    $fileContent = Get-Content $testCsvPath -Raw
    $fileName = "test_data.csv"
    
    $bodyLines = @(
        "--$boundary",
        "Content-Disposition: form-data; name=`"file`"; filename=`"$fileName`"",
        "Content-Type: text/csv",
        "",
        $fileContent,
        "--$boundary",
        "Content-Disposition: form-data; name=`"dataset_name`"",
        "",
        "test_customers",
        "--$boundary",
        "Content-Disposition: form-data; name=`"description`"",
        "",
        "Test customer dataset",
        "--$boundary--"
    )
    
    $body = $bodyLines -join $LF
    
    $uploadResponse = Invoke-RestMethod -Uri "$BaseUrl/api/v1/ingest" -Method POST -Body $body -ContentType "multipart/form-data; boundary=$boundary"
    Write-Host "[OK] File upload SUCCESS" -ForegroundColor Green
    Write-Host "Response: $($uploadResponse | ConvertTo-Json -Depth 5)" -ForegroundColor Gray
} catch {
    Write-Host "[FAIL] File upload FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# 4. Test Validation
Write-Host "`n[PHASE 4] Validation Workflows" -ForegroundColor Magenta
Test-Endpoint -Name "Get Validation Rules" -Method "GET" -Endpoint "/api/v1/rules"
Test-Endpoint -Name "Get Rule Types" -Method "GET" -Endpoint "/api/v1/rules/types/list"

# Execute validation if we have uploaded data
if ($uploadResponse) {
    $validationData = @{
        dataset_name = "test_customers"
        validation_type = "schema"
    }
    Test-Endpoint -Name "Execute Validation" -Method "POST" -Endpoint "/api/v1/validations/execute" -Body $validationData
}

# 5. Test Profiling
Write-Host "`n[PHASE 5] Data Profiling" -ForegroundColor Magenta
if ($uploadResponse) {
    $profilingData = @{
        dataset_name = "test_customers"
        include_statistics = $true
        include_quality_metrics = $true
    }
    Test-Endpoint -Name "Execute Profiling" -Method "POST" -Endpoint "/api/v1/profiling/execute" -Body $profilingData
    
    Start-Sleep -Seconds 2
    Test-Endpoint -Name "Get Profiling History" -Method "GET" -Endpoint "/api/v1/profiling/history"
}

# 6. Test Audit Logging
Write-Host "`n[PHASE 6] Audit Logging" -ForegroundColor Magenta
Test-Endpoint -Name "Get Audit Logs" -Method "GET" -Endpoint "/api/v1/audit/"
Test-Endpoint -Name "Get Audit Statistics" -Method "GET" -Endpoint "/api/v1/audit/statistics/summary"
Test-Endpoint -Name "Get Recent Audits" -Method "GET" -Endpoint "/api/v1/audit/recent/list"

# 7. Test Metrics
Write-Host "`n[PHASE 7] Metrics and Monitoring" -ForegroundColor Magenta
Test-Endpoint -Name "Get Metrics Summary" -Method "GET" -Endpoint "/api/v1/metrics/summary"
Test-Endpoint -Name "Get Metrics List" -Method "GET" -Endpoint "/api/v1/metrics/list"
Test-Endpoint -Name "Get Cache Stats" -Method "GET" -Endpoint "/api/v1/cache/stats"
Test-Endpoint -Name "Get Observability Metrics" -Method "GET" -Endpoint "/api/v1/observability/metrics"

# 8. Test Warehouse Operations
Write-Host "`n[PHASE 8] Data Warehouse" -ForegroundColor Magenta
Test-Endpoint -Name "Get Warehouse Statistics" -Method "GET" -Endpoint "/api/v1/warehouse/statistics"
Test-Endpoint -Name "Get Load History" -Method "GET" -Endpoint "/api/v1/warehouse/load-history"

# 9. Test Health Scores
Write-Host "`n[PHASE 9] Pipeline Health Scores" -ForegroundColor Magenta
Test-Endpoint -Name "Get All Health Scores" -Method "GET" -Endpoint "/api/v1/health/all"

if ($uploadResponse) {
    $healthData = @{
        pipeline_name = "test_customers"
    }
    Test-Endpoint -Name "Calculate Health Score" -Method "POST" -Endpoint "/api/v1/health/calculate" -Body $healthData
}

# 10. Test Retry Workflows
Write-Host "`n[PHASE 10] Retry and Error Handling" -ForegroundColor Magenta
Test-Endpoint -Name "Get Pending Retries" -Method "GET" -Endpoint "/api/v1/retries/pending"
Test-Endpoint -Name "Get Retry Statistics" -Method "GET" -Endpoint "/api/v1/retries/statistics"
Test-Endpoint -Name "Get Retry Metrics" -Method "GET" -Endpoint "/api/v1/retries/metrics"

# Summary
Write-Host "`n========================================" -ForegroundColor Yellow
Write-Host "Test Results Summary" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

$passed = ($TestResults | Where-Object { $_.Status -eq "PASS" }).Count
$failed = ($TestResults | Where-Object { $_.Status -eq "FAIL" }).Count
$total = $TestResults.Count

Write-Host "`nTotal Tests: $total" -ForegroundColor White
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red
Write-Host "Success Rate: $([math]::Round(($passed / $total) * 100, 2))%" -ForegroundColor Cyan

if ($failed -gt 0) {
    Write-Host "`nFailed Tests:" -ForegroundColor Red
    $TestResults | Where-Object { $_.Status -eq "FAIL" } | ForEach-Object {
        Write-Host "  x $($_.Test) - $($_.Endpoint)" -ForegroundColor Red
        Write-Host "    Error: $($_.Error)" -ForegroundColor Gray
    }
}

Write-Host "`n========================================" -ForegroundColor Yellow
