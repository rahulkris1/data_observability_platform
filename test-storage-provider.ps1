# Test Storage Provider Configuration
# This script helps verify storage provider setup

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('minio', 's3')]
    [string]$Provider = 'minio'
)

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Storage Provider Configuration Test" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists
$envFile = "backend\.env"
if (-not (Test-Path $envFile)) {
    Write-Host "❌ .env file not found at: $envFile" -ForegroundColor Red
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    
    if (Test-Path "backend\.env.example") {
        Copy-Item "backend\.env.example" $envFile
        Write-Host "✓ Created .env file" -ForegroundColor Green
        Write-Host ""
        Write-Host "⚠️  Please edit backend\.env and configure your storage provider" -ForegroundColor Yellow
        Write-Host "   Then run this script again." -ForegroundColor Yellow
        exit 1
    } else {
        Write-Host "❌ .env.example not found" -ForegroundColor Red
        exit 1
    }
}

# Read current STORAGE_PROVIDER setting
$currentProvider = Select-String -Path $envFile -Pattern "^STORAGE_PROVIDER=(.+)$" | ForEach-Object { $_.Matches.Groups[1].Value }

Write-Host "Current Configuration:" -ForegroundColor Cyan
Write-Host "  Storage Provider: $currentProvider" -ForegroundColor White
Write-Host ""

# Check if provider needs to be changed
if ($Provider -ne $currentProvider) {
    Write-Host "Updating STORAGE_PROVIDER to: $Provider" -ForegroundColor Yellow
    
    # Update .env file
    $content = Get-Content $envFile
    $content = $content -replace "^STORAGE_PROVIDER=.*$", "STORAGE_PROVIDER=$Provider"
    $content | Set-Content $envFile
    
    Write-Host "✓ Updated STORAGE_PROVIDER in .env" -ForegroundColor Green
    Write-Host ""
}

# Validate configuration based on provider
if ($Provider -eq 's3') {
    Write-Host "Validating AWS S3 Configuration..." -ForegroundColor Cyan
    
    $awsKeyId = Select-String -Path $envFile -Pattern "^AWS_ACCESS_KEY_ID=(.+)$" | ForEach-Object { $_.Matches.Groups[1].Value }
    $awsSecret = Select-String -Path $envFile -Pattern "^AWS_SECRET_ACCESS_KEY=(.+)$" | ForEach-Object { $_.Matches.Groups[1].Value }
    $awsRegion = Select-String -Path $envFile -Pattern "^AWS_REGION=(.+)$" | ForEach-Object { $_.Matches.Groups[1].Value }
    
    $valid = $true
    
    if ([string]::IsNullOrWhiteSpace($awsKeyId) -or $awsKeyId -like '*your_*' -or $awsKeyId -like '*example*') {
        Write-Host "  ❌ AWS_ACCESS_KEY_ID not configured" -ForegroundColor Red
        $valid = $false
    } else {
        Write-Host "  ✓ AWS_ACCESS_KEY_ID: $($awsKeyId.Substring(0, [Math]::Min(8, $awsKeyId.Length)))..." -ForegroundColor Green
    }
    
    if ([string]::IsNullOrWhiteSpace($awsSecret) -or $awsSecret -like '*your_*' -or $awsSecret -like '*example*') {
        Write-Host "  ❌ AWS_SECRET_ACCESS_KEY not configured" -ForegroundColor Red
        $valid = $false
    } else {
        Write-Host "  ✓ AWS_SECRET_ACCESS_KEY: [configured]" -ForegroundColor Green
    }
    
    if ([string]::IsNullOrWhiteSpace($awsRegion)) {
        Write-Host "  ❌ AWS_REGION not configured" -ForegroundColor Red
        $valid = $false
    } else {
        Write-Host "  ✓ AWS_REGION: $awsRegion" -ForegroundColor Green
    }
    
    if (-not $valid) {
        Write-Host ""
        Write-Host "⚠️  Please configure AWS credentials in backend\.env" -ForegroundColor Yellow
        Write-Host "   Required variables:" -ForegroundColor Yellow
        Write-Host "   - AWS_ACCESS_KEY_ID" -ForegroundColor Yellow
        Write-Host "   - AWS_SECRET_ACCESS_KEY" -ForegroundColor Yellow
        Write-Host "   - AWS_REGION" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "Validating MinIO Configuration..." -ForegroundColor Cyan
    Write-Host "  ✓ MinIO configuration found" -ForegroundColor Green
    
    # Check if MinIO is running
    Write-Host ""
    Write-Host "Checking MinIO Docker container..." -ForegroundColor Cyan
    
    $minioRunning = docker ps --filter "name=dop-minio" --format "{{.Names}}" 2>$null
    
    if ($minioRunning -eq "dop-minio") {
        Write-Host "  ✓ MinIO container is running" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  MinIO container is not running" -ForegroundColor Yellow
        Write-Host ""
        $start = Read-Host "Start MinIO with Docker Compose? (y/n)"
        
        if ($start -eq 'y') {
            Write-Host "Starting MinIO..." -ForegroundColor Cyan
            docker-compose --profile minio up -d minio minio-setup
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✓ MinIO started successfully" -ForegroundColor Green
                Start-Sleep -Seconds 5
            } else {
                Write-Host "  ❌ Failed to start MinIO" -ForegroundColor Red
                exit 1
            }
        }
    }
}

# Check if virtual environment exists
Write-Host ""
Write-Host "Checking Python environment..." -ForegroundColor Cyan

if (Test-Path "backend\.venv\Scripts\python.exe") {
    Write-Host "  ✓ Virtual environment found" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Virtual environment not found" -ForegroundColor Yellow
    $create = Read-Host "Create virtual environment? (y/n)"
    
    if ($create -eq 'y') {
        Write-Host "Creating virtual environment..." -ForegroundColor Cyan
        Push-Location backend
        python -m venv .venv
        Pop-Location
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Virtual environment created" -ForegroundColor Green
        } else {
            Write-Host "  ❌ Failed to create virtual environment" -ForegroundColor Red
            exit 1
        }
    }
}

# Install boto3 if testing S3
if ($Provider -eq 's3') {
    Write-Host ""
    Write-Host "Checking boto3 installation..." -ForegroundColor Cyan
    
    $boto3Installed = & backend\.venv\Scripts\python.exe -c "import boto3; print('installed')" 2>$null
    
    if ($boto3Installed -eq 'installed') {
        Write-Host "  ✓ boto3 is installed" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  boto3 not found" -ForegroundColor Yellow
        $install = Read-Host "Install boto3? (y/n)"
        
        if ($install -eq 'y') {
            Write-Host "Installing boto3..." -ForegroundColor Cyan
            & backend\.venv\Scripts\pip.exe install boto3
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✓ boto3 installed successfully" -ForegroundColor Green
            } else {
                Write-Host "  ❌ Failed to install boto3" -ForegroundColor Red
            }
        }
    }
}

# Run connection test
Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Running Connection Test" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

$testScript = if ($Provider -eq 's3') { "test_s3_connection.py" } else { "test_minio_connection.py" }

if (Test-Path "backend\$testScript") {
    Push-Location backend
    & .\.venv\Scripts\python.exe $testScript
    $testResult = $LASTEXITCODE
    Pop-Location
    
    Write-Host ""
    if ($testResult -eq 0) {
        Write-Host "✓ Storage provider test completed successfully!" -ForegroundColor Green
    } else {
        Write-Host "❌ Storage provider test failed" -ForegroundColor Red
    }
} else {
    Write-Host "⚠️  Test script not found: backend\$testScript" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Start the backend: cd backend && uvicorn app.main:app --reload" -ForegroundColor White
Write-Host "  2. Check API: http://localhost:8000/api/v1/storage/status" -ForegroundColor White
Write-Host "  3. View dashboard: http://localhost:3000/dashboard" -ForegroundColor White
Write-Host "==================================================" -ForegroundColor Cyan
