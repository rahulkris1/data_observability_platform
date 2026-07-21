# Simple Backend API Test Script
$BaseUrl = "http://localhost:8000"
$TestResults = [System.Collections.ArrayList]::new()

function Test-API {
    param([string]$Name, [string]$Url, [hashtable]$Body = $null)
    
    Write-Host "`n[$Name]" -ForegroundColor Cyan
    try {
        if ($Body) {
            $json = $Body | ConvertTo-Json
            $response = Invoke-RestMethod -Uri $Url -Method POST -Body $json -ContentType "application/json"
        } else {
            $response = Invoke-RestMethod -Uri $Url -Method GET
        }
        Write-Host "  [OK] SUCCESS" -ForegroundColor Green
        $TestResults.Add(@{Name=$Name; Status="PASS"; Url=$Url}) | Out-Null
        return $response
    } catch {
        Write-Host "  [FAIL] $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails) {
            Write-Host "  Details: $($_.ErrorDetails)" -ForegroundColor Gray
        }
        $TestResults.Add(@{Name=$Name; Status="FAIL"; Url=$Url; Error=$_.Exception.Message}) | Out-Null
        return $null
    }
}

Write-Host "=== Backend API Tests ===" -ForegroundColor Yellow

# Basic Health
Test-API "Root Health" "$BaseUrl/"
Test-API "System Health" "$BaseUrl/health"
Test-API "Storage Status" "$BaseUrl/api/v1/storage/status"
Test-API "Glue Health" "$BaseUrl/api/v1/glue/health"
Test-API "Cache Health" "$BaseUrl/api/v1/cache/health"
Test-API "Cache Stats" "$BaseUrl/api/v1/cache/stats"

# Rules
Test-API "Get Rules" "$BaseUrl/api/v1/rules"
Test-API "Get Rule Types" "$BaseUrl/api/v1/rules/types/list"

# Auth - Try to get current user (should fail without token)
Write-Host "`n[Auth - Me Endpoint]" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/me" -Method GET
    Write-Host "  [UNEXPECTED] Should require authentication" -ForegroundColor Yellow
} catch {
    Write-Host "  [EXPECTED] Authentication required: $($_.Exception.Message)" -ForegroundColor Gray
}

# Register a new user
$username = "testuser_$(Get-Random -Maximum 9999)"
$registerData = @{
    username = $username
    email = "test_$(Get-Random -Maximum 9999)@example.com"
    password = "TestPass123!"
    full_name = "Test User"
}
$registerResponse = Test-API "User Registration" "$BaseUrl/api/v1/auth/register" $registerData

# Observability
Test-API "Observability Metrics" "$BaseUrl/api/v1/observability/metrics"

# Summary
Write-Host "`n=== Summary ===" -ForegroundColor Yellow
$passed = ($TestResults | Where-Object Status -eq "PASS").Count
$failed = ($TestResults | Where-Object Status -eq "FAIL").Count
Write-Host "Passed: $passed / $($TestResults.Count)" -ForegroundColor Green
Write-Host "Failed: $failed / $($TestResults.Count)" -ForegroundColor Red

if ($failed -gt 0) {
    Write-Host "`nFailed Tests:" -ForegroundColor Red
    $TestResults | Where-Object Status -eq "FAIL" | ForEach-Object {
        Write-Host "  - $($_.Name)" -ForegroundColor Red
        Write-Host "    $($_.Error)" -ForegroundColor Gray
    }
}
