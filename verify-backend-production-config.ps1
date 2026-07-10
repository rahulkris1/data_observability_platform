# Backend Production Configuration Validation Script
# Validates that the backend is ready for production deployment

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Backend Production Configuration Validation" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorCount = 0
$WarningCount = 0

# Function to check file existence
function Test-FileExists {
    param($Path, $Description)
    if (Test-Path $Path) {
        Write-Host "✅ $Description exists" -ForegroundColor Green
        return $true
    } else {
        Write-Host "❌ $Description missing: $Path" -ForegroundColor Red
        $script:ErrorCount++
        return $false
    }
}

# Function to check directory existence
function Test-DirectoryExists {
    param($Path, $Description)
    if (Test-Path $Path -PathType Container) {
        Write-Host "✅ $Description exists" -ForegroundColor Green
        return $true
    } else {
        Write-Host "⚠️  $Description missing: $Path" -ForegroundColor Yellow
        $script:WarningCount++
        return $false
    }
}

# Function to check environment variable in .env.production
function Test-EnvVariable {
    param($FilePath, $VarName, $Description)
    
    if (Test-Path $FilePath) {
        $content = Get-Content $FilePath -Raw
        if ($content -match "$VarName\s*=\s*(.+)") {
            $value = $matches[1].Trim()
            
            # Check for insecure defaults
            $insecurePatterns = @("CHANGE_THIS", "changeme", "password", "secret", "admin", "default")
            $isInsecure = $false
            foreach ($pattern in $insecurePatterns) {
                if ($value -like "*$pattern*") {
                    $isInsecure = $true
                    break
                }
            }
            
            if ($isInsecure) {
                Write-Host "⚠️  $Description has insecure default value" -ForegroundColor Yellow
                $script:WarningCount++
            } else {
                Write-Host "✅ $Description is configured" -ForegroundColor Green
            }
            return $true
        } else {
            Write-Host "❌ $Description not found in $FilePath" -ForegroundColor Red
            $script:ErrorCount++
            return $false
        }
    }
    return $false
}

Write-Host "1. Checking Required Files..." -ForegroundColor Cyan
Write-Host "---------------------------------------------"

# Check production environment file
Test-FileExists "backend\.env.production" ".env.production"

# Check configuration files
Test-FileExists "backend\config\production_config.py" "production_config.py"
Test-FileExists "backend\startup.production.sh" "startup.production.sh"

# Check application files
Test-FileExists "backend\app\main.py" "main.py"
Test-FileExists "backend\requirements.txt" "requirements.txt"
Test-FileExists "backend\alembic.ini" "alembic.ini"

# Check Dockerfile
Test-FileExists "docker\backend\Dockerfile.production" "Production Dockerfile"

Write-Host ""
Write-Host "2. Checking Required Directories..." -ForegroundColor Cyan
Write-Host "---------------------------------------------"

# Check application directories
Test-DirectoryExists "backend\app" "app directory"
Test-DirectoryExists "backend\config" "config directory"
Test-DirectoryExists "backend\alembic" "alembic directory"
Test-DirectoryExists "backend\logs" "logs directory"

Write-Host ""
Write-Host "3. Validating Production Environment Variables..." -ForegroundColor Cyan
Write-Host "---------------------------------------------"

$envFile = "backend\.env.production"

# Critical security settings
Test-EnvVariable $envFile "SECRET_KEY" "SECRET_KEY"
Test-EnvVariable $envFile "JWT_SECRET_KEY" "JWT_SECRET_KEY"

# Database settings
Test-EnvVariable $envFile "POSTGRES_USER" "POSTGRES_USER"
Test-EnvVariable $envFile "POSTGRES_PASSWORD" "POSTGRES_PASSWORD"
Test-EnvVariable $envFile "POSTGRES_DB" "POSTGRES_DB"
Test-EnvVariable $envFile "DATABASE_URL" "DATABASE_URL"

# Redis settings
Test-EnvVariable $envFile "REDIS_PASSWORD" "REDIS_PASSWORD"
Test-EnvVariable $envFile "REDIS_URL" "REDIS_URL"

# Storage settings
Test-EnvVariable $envFile "STORAGE_PROVIDER" "STORAGE_PROVIDER"
Test-EnvVariable $envFile "MINIO_ACCESS_KEY" "MINIO_ACCESS_KEY"
Test-EnvVariable $envFile "MINIO_SECRET_KEY" "MINIO_SECRET_KEY"

# Celery settings
Test-EnvVariable $envFile "CELERY_BROKER_URL" "CELERY_BROKER_URL"
Test-EnvVariable $envFile "CELERY_RESULT_BACKEND" "CELERY_RESULT_BACKEND"

# Airflow settings
Test-EnvVariable $envFile "AIRFLOW_PASSWORD" "AIRFLOW_PASSWORD"

Write-Host ""
Write-Host "4. Checking Docker Configuration..." -ForegroundColor Cyan
Write-Host "---------------------------------------------"

if (Test-Path "docker-compose.production.yml") {
    Write-Host "✅ docker-compose.production.yml exists" -ForegroundColor Green
    
    # Check if docker-compose.yml contains backend service
    $dockerCompose = Get-Content "docker-compose.production.yml" -Raw
    if ($dockerCompose -match "backend:") {
        Write-Host "✅ Backend service defined in docker-compose.production.yml" -ForegroundColor Green
    } else {
        Write-Host "❌ Backend service not found in docker-compose.production.yml" -ForegroundColor Red
        $ErrorCount++
    }
} else {
    Write-Host "❌ docker-compose.production.yml not found" -ForegroundColor Red
    $ErrorCount++
}

Write-Host ""
Write-Host "5. Validating Python Dependencies..." -ForegroundColor Cyan
Write-Host "---------------------------------------------"

if (Test-Path "backend\requirements.txt") {
    $requirements = Get-Content "backend\requirements.txt"
    
    # Check critical dependencies
    $criticalDeps = @("fastapi", "uvicorn", "gunicorn", "sqlalchemy", "alembic", "redis", "celery", "pydantic")
    
    foreach ($dep in $criticalDeps) {
        if ($requirements -match $dep) {
            Write-Host "✅ $dep is in requirements.txt" -ForegroundColor Green
        } else {
            Write-Host "⚠️  $dep not found in requirements.txt" -ForegroundColor Yellow
            $WarningCount++
        }
    }
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Validation Summary" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Errors: $ErrorCount" -ForegroundColor $(if ($ErrorCount -eq 0) { "Green" } else { "Red" })
Write-Host "Warnings: $WarningCount" -ForegroundColor $(if ($WarningCount -eq 0) { "Green" } else { "Yellow" })
Write-Host ""

if ($ErrorCount -eq 0 -and $WarningCount -eq 0) {
    Write-Host "✅ Backend production configuration is VALID!" -ForegroundColor Green
    Write-Host "   Ready for production deployment" -ForegroundColor Green
    exit 0
} elseif ($ErrorCount -eq 0) {
    Write-Host "⚠️  Backend production configuration has WARNINGS" -ForegroundColor Yellow
    Write-Host "   Please review warnings before deploying to production" -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "❌ Backend production configuration has ERRORS" -ForegroundColor Red
    Write-Host "   Please fix errors before deploying to production" -ForegroundColor Red
    exit 1
}
