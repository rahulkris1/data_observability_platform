# Docker Setup Prerequisites Check
# Run this script before starting Docker services

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Docker Prerequisites Check" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$allGood = $true

# Check 1: Docker Desktop installed
Write-Host "1. Checking Docker Desktop installation..." -ForegroundColor Yellow
$dockerPath = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerPath) {
    Write-Host "  ✓ Docker is installed at: $($dockerPath.Source)" -ForegroundColor Green
    
    # Check Docker version
    try {
        $version = docker --version
        Write-Host "  ✓ Version: $version" -ForegroundColor Green
    }
    catch {
        Write-Host "  ⚠ Could not determine Docker version" -ForegroundColor Yellow
    }
}
else {
    Write-Host "  ✗ Docker is not installed" -ForegroundColor Red
    $allGood = $false
}
Write-Host ""

# Check 2: Docker is running
if ($dockerPath) {
    Write-Host "2. Checking if Docker daemon is running..." -ForegroundColor Yellow
    try {
        docker info | Out-Null
        Write-Host "  ✓ Docker daemon is running" -ForegroundColor Green
    }
    catch {
        Write-Host "  ✗ Docker daemon is not running" -ForegroundColor Red
        Write-Host "  → Please start Docker Desktop" -ForegroundColor Yellow
        $allGood = $false
    }
    Write-Host ""
}

# Check 3: Docker Compose
if ($dockerPath) {
    Write-Host "3. Checking Docker Compose..." -ForegroundColor Yellow
    
    # Try Docker Compose V2 (built into Docker)
    try {
        $composeVersion = docker compose version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Docker Compose V2: $composeVersion" -ForegroundColor Green
        }
    }
    catch {
        # Try Docker Compose V1 (standalone)
        try {
            $composeVersion = docker-compose --version
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✓ Docker Compose V1: $composeVersion" -ForegroundColor Green
            }
        }
        catch {
            Write-Host "  ✗ Docker Compose is not available" -ForegroundColor Red
            $allGood = $false
        }
    }
    Write-Host ""
}

# Check 4: Available RAM
Write-Host "4. Checking system resources..." -ForegroundColor Yellow
$totalRAM = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)
Write-Host "  Total RAM: $totalRAM GB" -ForegroundColor White

if ($totalRAM -ge 8) {
    Write-Host "  ✓ Sufficient RAM available" -ForegroundColor Green
}
else {
    Write-Host "  ⚠ Recommended: 8GB+ RAM (you have $totalRAM GB)" -ForegroundColor Yellow
}
Write-Host ""

# Check 5: Available disk space
Write-Host "5. Checking disk space..." -ForegroundColor Yellow
$drive = (Get-Location).Drive
$freeSpace = [math]::Round((Get-PSDrive $drive.Name).Free / 1GB, 2)
Write-Host "  Free space on $($drive.Name): $freeSpace GB" -ForegroundColor White

if ($freeSpace -ge 20) {
    Write-Host "  ✓ Sufficient disk space available" -ForegroundColor Green
}
else {
    Write-Host "  ⚠ Recommended: 20GB+ free space (you have $freeSpace GB)" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($allGood) {
    Write-Host "✓ All prerequisites met! You can proceed with:" -ForegroundColor Green
    Write-Host "  .\start-docker.ps1" -ForegroundColor Yellow
}
else {
    Write-Host "✗ Some prerequisites are missing" -ForegroundColor Red
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    
    if (-not $dockerPath) {
        Write-Host ""
        Write-Host "1. Install Docker Desktop:" -ForegroundColor Yellow
        Write-Host "   → Download from: https://www.docker.com/products/docker-desktop/" -ForegroundColor White
        Write-Host "   → Install for Windows" -ForegroundColor White
        Write-Host "   → Restart your computer after installation" -ForegroundColor White
        Write-Host ""
        Write-Host "2. Configure Docker Desktop:" -ForegroundColor Yellow
        Write-Host "   → Open Docker Desktop settings" -ForegroundColor White
        Write-Host "   → Resources → Advanced" -ForegroundColor White
        Write-Host "   → Allocate at least 8GB RAM" -ForegroundColor White
        Write-Host "   → Allocate at least 4 CPUs" -ForegroundColor White
        Write-Host "   → Apply & Restart" -ForegroundColor White
    }
    elseif (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Host ""
        Write-Host "1. Start Docker Desktop:" -ForegroundColor Yellow
        Write-Host "   → Look for Docker Desktop in Start Menu" -ForegroundColor White
        Write-Host "   → Wait for Docker to fully start (icon in system tray)" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "3. Run this check again:" -ForegroundColor Yellow
    Write-Host "   .\check-docker-prerequisites.ps1" -ForegroundColor White
}

Write-Host ""
