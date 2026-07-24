# Comprehensive Verification and Testing Script
# This script runs all verification tests for the Data Observability Platform

param(
    [switch]$SkipBackend = $false,
    [switch]$SkipFrontend = $false,
    [switch]$SkipE2E = $false,
    [switch]$SkipTests = $false,
    [switch]$Verbose = $false
)

# Color functions
function Write-ColorOutput($ForegroundColor, $Message) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    Write-Output $Message
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Header($Message) {
    Write-Host ""
    Write-ColorOutput "Cyan" ("="*80)
    Write-ColorOutput "Cyan" $Message.PadLeft(40 + $Message.Length/2).PadRight(80)
    Write-ColorOutput "Cyan" ("="*80)
    Write-Host ""
}

function Write-Success($Message) {
    Write-ColorOutput "Green" "✓ $Message"
}

function Write-Error($Message) {
    Write-ColorOutput "Red" "✗ $Message"
}

function Write-Warning($Message) {
    Write-ColorOutput "Yellow" "⚠ $Message"
}

function Write-Information-Msg($Message) {
    Write-ColorOutput "Cyan" "ℹ $Message"
}

# Test results tracking
$script:TotalTests = 0
$script:PassedTests = 0
$script:FailedTests = 0
$script:SkippedTests = 0

function Start-TestSection($Name) {
    Write-Header "Testing: $Name"
}

function Complete-TestSection($Name, $Success) {
    $script:TotalTests++
    if ($Success) {
        $script:PassedTests++
        Write-Success "$Name completed successfully"
    } else {
        $script:FailedTests++
        Write-Error "$Name failed"
    }
    Write-Host ""
}

function Skip-TestSection($Name, $Reason) {
    $script:TotalTests++
    $script:SkippedTests++
    Write-Warning "$Name skipped: $Reason"
    Write-Host ""
}

# Main verification script
Write-Host ""
Write-ColorOutput "Cyan" @"
================================================================================
        DATA OBSERVABILITY PLATFORM - COMPREHENSIVE VERIFICATION
================================================================================
"@
Write-Host ""
Write-Information-Msg "Start Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

# Check Python installation
Write-Header "Environment Verification"

$pythonInstalled = Get-Command python -ErrorAction SilentlyContinue
if ($pythonInstalled) {
    $pythonVersion = python --version 2>&1
    Write-Success "Python installed: $pythonVersion"
} else {
    Write-Error "Python is not installed!"
    Write-Warning "Please install Python 3.8 or higher"
    exit 1
}

# Check if services are running
Write-Information-Msg "Checking if services are running..."

$backendRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Success "Backend API is running"
        $backendRunning = $true
    }
} catch {
    Write-Warning "Backend API is not running"
    Write-Information-Msg "To start services, run: ./run-local.ps1"
}

$frontendRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -Method GET -TimeoutSec 5 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Success "Frontend is running"
        $frontendRunning = $true
    }
} catch {
    Write-Warning "Frontend is not running"
}

Write-Host ""

# ============================================================================
# 1. BACKEND COMPONENT VERIFICATION
# ============================================================================
if (-not $SkipBackend) {
    Start-TestSection "Backend Component Structure"
    
    $result = python verify_backend_components.py
    $exitCode = $LASTEXITCODE
    
    if ($Verbose) {
        Write-Output $result
    }
    
    Complete-TestSection "Backend Components" ($exitCode -eq 0)
} else {
    Skip-TestSection "Backend Components" "Skipped by user"
}

# ============================================================================
# 2. FRONTEND COMPONENT VERIFICATION
# ============================================================================
if (-not $SkipFrontend) {
    Start-TestSection "Frontend Component Structure"
    
    $result = python verify_ui_components.py
    $exitCode = $LASTEXITCODE
    
    if ($Verbose) {
        Write-Output $result
    }
    
    Complete-TestSection "Frontend Components" ($exitCode -eq 0)
} else {
    Skip-TestSection "Frontend Components" "Skipped by user"
}

# ============================================================================
# 3. BACKEND UNIT TESTS
# ============================================================================
if (-not $SkipTests) {
    Start-TestSection "Backend Unit Tests"
    
    if (Test-Path "backend/tests/unit") {
        Push-Location backend
        
        Write-Information-Msg "Running unit tests..."
        if ($Verbose) {
            python -m pytest tests/unit -v
        } else {
            python -m pytest tests/unit --tb=short -q
        }
        
        $exitCode = $LASTEXITCODE
        Pop-Location
        
        Complete-TestSection "Backend Unit Tests" ($exitCode -eq 0)
    } else {
        Skip-TestSection "Backend Unit Tests" "Test directory not found"
    }
} else {
    Skip-TestSection "Backend Unit Tests" "Skipped by user"
}

# ============================================================================
# 4. FRONTEND TESTS
# ============================================================================
if (-not $SkipTests -and -not $SkipFrontend) {
    Start-TestSection "Frontend Tests"
    
    if (Test-Path "frontend/__tests__") {
        Push-Location frontend
        
        Write-Information-Msg "Running frontend tests..."
        if ($Verbose) {
            npm test -- --verbose --passWithNoTests
        } else {
            npm test -- --passWithNoTests 2>&1 | Out-Null
        }
        
        $exitCode = $LASTEXITCODE
        Pop-Location
        
        Complete-TestSection "Frontend Tests" ($exitCode -eq 0)
    } else {
        Skip-TestSection "Frontend Tests" "Test directory not found"
    }
} else {
    if ($SkipTests) {
        Skip-TestSection "Frontend Tests" "Skipped by user"
    } else {
        Skip-TestSection "Frontend Tests" "Frontend skipped"
    }
}

# ============================================================================
# 5. END-TO-END API VERIFICATION
# ============================================================================
if (-not $SkipE2E) {
    Start-TestSection "End-to-End API Verification"
    
    if ($backendRunning) {
        $result = python comprehensive_verification.py
        $exitCode = $LASTEXITCODE
        
        if ($Verbose) {
            Write-Output $result
        }
        
        Complete-TestSection "E2E API Tests" ($exitCode -eq 0)
    } else {
        Skip-TestSection "E2E API Tests" "Backend is not running"
        Write-Warning "Start the backend with: ./run-local.ps1"
    }
} else {
    Skip-TestSection "E2E API Tests" "Skipped by user"
}

# ============================================================================
# 6. BACKEND INTEGRATION TESTS
# ============================================================================
if (-not $SkipTests) {
    Start-TestSection "Backend Integration Tests"
    
    if ((Test-Path "backend/tests/integration") -and $backendRunning) {
        Push-Location backend
        
        Write-Information-Msg "Running integration tests..."
        if ($Verbose) {
            python -m pytest tests/integration -v
        } else {
            python -m pytest tests/integration --tb=short -q
        }
        
        $exitCode = $LASTEXITCODE
        Pop-Location
        
        Complete-TestSection "Backend Integration Tests" ($exitCode -eq 0)
    } elseif (-not $backendRunning) {
        Skip-TestSection "Backend Integration Tests" "Backend is not running"
    } else {
        Skip-TestSection "Backend Integration Tests" "Test directory not found"
    }
} else {
    Skip-TestSection "Backend Integration Tests" "Skipped by user"
}

# ============================================================================
# 7. AIRFLOW DAG VALIDATION
# ============================================================================
if (-not $SkipTests) {
    Start-TestSection "Airflow DAG Validation"
    
    if (Test-Path "airflow/dags") {
        Write-Information-Msg "Validating Airflow DAGs..."
        
        # Check if DAGs can be imported without errors
        $dagFiles = Get-ChildItem -Path "airflow/dags" -Filter "*.py" | Where-Object { $_.Name -notmatch "__" }
        
        $allValid = $true
        foreach ($dagFile in $dagFiles) {
            try {
                python -c "import sys; sys.path.insert(0, 'airflow/dags'); import $($dagFile.BaseName)" 2>&1 | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    Write-Success "DAG valid: $($dagFile.Name)"
                } else {
                    Write-Error "DAG invalid: $($dagFile.Name)"
                    $allValid = $false
                }
            } catch {
                Write-Error "DAG import failed: $($dagFile.Name)"
                $allValid = $false
            }
        }
        
        Complete-TestSection "Airflow DAG Validation" $allValid
    } else {
        Skip-TestSection "Airflow DAG Validation" "DAGs directory not found"
    }
} else {
    Skip-TestSection "Airflow DAG Validation" "Skipped by user"
}

# ============================================================================
# 8. DOCKER CONFIGURATION VALIDATION
# ============================================================================
Start-TestSection "Docker Configuration"

$dockerFiles = @(
    "docker-compose.yml",
    "docker-compose.dev.yml",
    "docker-compose.production.yml",
    "docker/backend/Dockerfile",
    "docker/frontend/Dockerfile",
    "docker/airflow/Dockerfile"
)

$allDockerFilesExist = $true
foreach ($file in $dockerFiles) {
    if (Test-Path $file) {
        Write-Success "Found: $file"
    } else {
        Write-Error "Missing: $file"
        $allDockerFilesExist = $false
    }
}

Complete-TestSection "Docker Configuration" $allDockerFilesExist

# ============================================================================
# 9. CONFIGURATION FILES VALIDATION
# ============================================================================
Start-TestSection "Configuration Files"

$configFiles = @{
    "backend/requirements.txt" = @("fastapi", "sqlalchemy", "pydantic")
    "backend/alembic.ini" = @("alembic")
    "frontend/package.json" = @("next", "react", "typescript")
    "frontend/tsconfig.json" = @("compilerOptions")
    "README.md" = @("Data Observability")
}

$allConfigValid = $true
foreach ($file in $configFiles.Keys) {
    if (Test-Path $file) {
        $content = Get-Content $file -Raw
        $missing = @()
        
        foreach ($expected in $configFiles[$file]) {
            if ($content -notmatch [regex]::Escape($expected)) {
                $missing += $expected
            }
        }
        
        if ($missing.Count -eq 0) {
            Write-Success "Valid: $file"
        } else {
            Write-Warning "Missing elements in $file : $($missing -join ', ')"
            $allConfigValid = $false
        }
    } else {
        Write-Error "Missing: $file"
        $allConfigValid = $false
    }
}

Complete-TestSection "Configuration Files" $allConfigValid

# ============================================================================
# 10. DATABASE MIGRATIONS CHECK
# ============================================================================
Start-TestSection "Database Migrations"

if (Test-Path "backend/alembic/versions") {
    $migrations = Get-ChildItem -Path "backend/alembic/versions" -Filter "*.py" | Where-Object { $_.Name -notmatch "__" }
    
    if ($migrations.Count -gt 0) {
        Write-Success "Found $($migrations.Count) database migrations"
        
        if ($Verbose) {
            foreach ($migration in $migrations) {
                Write-Information-Msg "  - $($migration.Name)"
            }
        }
        
        Complete-TestSection "Database Migrations" $true
    } else {
        Write-Warning "No migration files found"
        Complete-TestSection "Database Migrations" $false
    }
} else {
    Write-Error "Migrations directory not found"
    Complete-TestSection "Database Migrations" $false
}

# ============================================================================
# FINAL SUMMARY
# ============================================================================
Write-Host ""
Write-Header "VERIFICATION SUMMARY"

Write-Host ""
Write-ColorOutput "Cyan" "Total Test Sections: $script:TotalTests"
Write-ColorOutput "Green" "Passed: $script:PassedTests"
Write-ColorOutput "Red" "Failed: $script:FailedTests"
Write-ColorOutput "Yellow" "Skipped: $script:SkippedTests"
Write-Host ""

$passRate = if ($script:TotalTests -gt 0) { 
    [math]::Round(($script:PassedTests / $script:TotalTests) * 100, 1) 
} else { 
    0 
}

Write-ColorOutput "Cyan" "Pass Rate: $passRate%"
Write-Host ""

if ($script:FailedTests -eq 0 -and $script:PassedTests -gt 0) {
    Write-ColorOutput "Green" "🎉 ALL VERIFICATIONS PASSED!"
    Write-Host ""
    Write-Success "The Data Observability Platform is functioning correctly"
    $exitCode = 0
} elseif ($script:FailedTests -eq 0 -and $script:SkippedTests -gt 0) {
    Write-ColorOutput "Yellow" "⚠ All tests passed, but some were skipped"
    Write-Host ""
    Write-Warning "Run without skip flags for complete verification"
    $exitCode = 0
} elseif ($passRate -ge 80) {
    Write-ColorOutput "Yellow" "⚠ Most tests passed, but some issues found"
    Write-Host ""
    Write-Warning "Review failed tests above for details"
    $exitCode = 1
} else {
    Write-ColorOutput "Red" "✗ VERIFICATION FAILED"
    Write-Host ""
    Write-Error "Multiple test failures detected. Please review the output above."
    $exitCode = 1
}

Write-Information-Msg "End Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

# Provide recommendations
if (-not $backendRunning) {
    Write-Header "RECOMMENDATIONS"
    Write-Warning "Backend is not running. To start all services:"
    Write-Host "  .\run-local.ps1"
    Write-Host ""
}

if ($script:FailedTests -gt 0) {
    Write-Header "NEXT STEPS"
    Write-Information-Msg "1. Review the failed test sections above"
    Write-Information-Msg "2. Check the error messages and logs"
    Write-Information-Msg "3. Fix the issues and re-run: .\run_comprehensive_verification.ps1"
    Write-Host ""
}

exit $exitCode
