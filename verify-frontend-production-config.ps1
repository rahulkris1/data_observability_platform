# Frontend Production Configuration Validation Script
# Validates that the frontend is ready for production deployment

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Frontend Production Configuration Validation" -ForegroundColor Cyan
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
            Write-Host "✅ $Description is configured: $value" -ForegroundColor Green
            return $true
        } else {
            Write-Host "⚠️  $Description not found in $FilePath" -ForegroundColor Yellow
            $script:WarningCount++
            return $false
        }
    }
    return $false
}

Write-Host "1. Checking Required Files..." -ForegroundColor Cyan
Write-Host "---------------------------------------------"

# Check production environment file
Test-FileExists "frontend\.env.production" ".env.production"

# Check Next.js configuration
Test-FileExists "frontend\next.config.js" "next.config.js"
Test-FileExists "frontend\package.json" "package.json"

# Check health endpoint
Test-FileExists "frontend\src\pages\api\health.ts" "API health endpoint"

# Check Dockerfile
Test-FileExists "docker\frontend\Dockerfile.production" "Production Dockerfile"

Write-Host ""
Write-Host "2. Checking Required Directories..." -ForegroundColor Cyan
Write-Host "---------------------------------------------"

# Check application directories
Test-DirectoryExists "frontend\src" "src directory"
Test-DirectoryExists "frontend\src\pages" "pages directory"
Test-DirectoryExists "frontend\src\components" "components directory"
Test-DirectoryExists "frontend\src\services" "services directory"
Test-DirectoryExists "frontend\public" "public directory"

Write-Host ""
Write-Host "3. Validating Production Environment Variables..." -ForegroundColor Cyan
Write-Host "---------------------------------------------"

$envFile = "frontend\.env.production"

# API configuration
Test-EnvVariable $envFile "NEXT_PUBLIC_API_URL" "API URL"
Test-EnvVariable $envFile "NEXT_PUBLIC_API_VERSION" "API Version"

# Application settings
Test-EnvVariable $envFile "NEXT_PUBLIC_APP_NAME" "App Name"
Test-EnvVariable $envFile "NEXT_PUBLIC_ENVIRONMENT" "Environment"
Test-EnvVariable $envFile "NODE_ENV" "Node Environment"

Write-Host ""
Write-Host "4. Checking Next.js Configuration..." -ForegroundColor Cyan
Write-Host "---------------------------------------------"

if (Test-Path "frontend\next.config.js") {
    $nextConfig = Get-Content "frontend\next.config.js" -Raw
    
    # Check for standalone output
    if ($nextConfig -match "output:\s*['\`"]standalone['\`"]") {
        Write-Host "✅ Next.js configured with standalone output" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Next.js not configured for standalone output (recommended for Docker)" -ForegroundColor Yellow
        $WarningCount++
    }
    
    # Check for React strict mode
    if ($nextConfig -match "reactStrictMode:\s*true") {
        Write-Host "✅ React Strict Mode enabled" -ForegroundColor Green
    } else {
        Write-Host "⚠️  React Strict Mode not enabled" -ForegroundColor Yellow
        $WarningCount++
    }
}

Write-Host ""
Write-Host "5. Checking Docker Configuration..." -ForegroundColor Cyan
Write-Host "---------------------------------------------"

if (Test-Path "docker-compose.production.yml") {
    Write-Host "✅ docker-compose.production.yml exists" -ForegroundColor Green
    
    # Check if docker-compose.yml contains frontend service
    $dockerCompose = Get-Content "docker-compose.production.yml" -Raw
    if ($dockerCompose -match "frontend:") {
        Write-Host "✅ Frontend service defined in docker-compose.production.yml" -ForegroundColor Green
    } else {
        Write-Host "❌ Frontend service not found in docker-compose.production.yml" -ForegroundColor Red
        $ErrorCount++
    }
} else {
    Write-Host "❌ docker-compose.production.yml not found" -ForegroundColor Red
    $ErrorCount++
}

Write-Host ""
Write-Host "6. Validating Package Dependencies..." -ForegroundColor Cyan
Write-Host "---------------------------------------------"

if (Test-Path "frontend\package.json") {
    $packageJson = Get-Content "frontend\package.json" -Raw | ConvertFrom-Json
    
    # Check critical dependencies
    $criticalDeps = @("next", "react", "react-dom", "axios")
    
    foreach ($dep in $criticalDeps) {
        if ($packageJson.dependencies.PSObject.Properties.Name -contains $dep) {
            $version = $packageJson.dependencies.$dep
            Write-Host "✅ $dep is in dependencies: $version" -ForegroundColor Green
        } else {
            Write-Host "❌ $dep not found in dependencies" -ForegroundColor Red
            $ErrorCount++
        }
    }
    
    # Check build script
    if ($packageJson.scripts.build) {
        Write-Host "✅ Build script is defined: $($packageJson.scripts.build)" -ForegroundColor Green
    } else {
        Write-Host "❌ Build script not found in package.json" -ForegroundColor Red
        $ErrorCount++
    }
}

Write-Host ""
Write-Host "7. Checking Health Check Endpoint..." -ForegroundColor Cyan
Write-Host "---------------------------------------------"

if (Test-Path "frontend\src\pages\api\health.ts") {
    $healthContent = Get-Content "frontend\src\pages\api\health.ts" -Raw
    if ($healthContent -match "status.*healthy") {
        Write-Host "✅ Health check endpoint properly configured" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Health check endpoint may not be properly configured" -ForegroundColor Yellow
        $WarningCount++
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
    Write-Host "✅ Frontend production configuration is VALID!" -ForegroundColor Green
    Write-Host "   Ready for production deployment" -ForegroundColor Green
    exit 0
} elseif ($ErrorCount -eq 0) {
    Write-Host "⚠️  Frontend production configuration has WARNINGS" -ForegroundColor Yellow
    Write-Host "   Please review warnings before deploying to production" -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "❌ Frontend production configuration has ERRORS" -ForegroundColor Red
    Write-Host "   Please fix errors before deploying to production" -ForegroundColor Red
    exit 1
}
