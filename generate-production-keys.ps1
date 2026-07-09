# Generate Secure Keys for Production
# This script generates secure random keys for production environment variables

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Production Security Key Generator" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

function New-SecureKey {
    param(
        [int]$Length = 64
    )
    
    $bytes = New-Object byte[] $Length
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    return [Convert]::ToBase64String($bytes)
}

function New-SecurePassword {
    param(
        [int]$Length = 32
    )
    
    $chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?"
    $password = ""
    $rng = New-Object System.Random
    
    for ($i = 0; $i -lt $Length; $i++) {
        $password += $chars[$rng.Next(0, $chars.Length)]
    }
    
    return $password
}

Write-Host "Generated Secure Keys:" -ForegroundColor Green
Write-Host ""

Write-Host "# Application Security" -ForegroundColor Cyan
Write-Host "SECRET_KEY=$(New-SecureKey)" -ForegroundColor White
Write-Host "JWT_SECRET_KEY=$(New-SecureKey)" -ForegroundColor White
Write-Host ""

Write-Host "# Database Credentials" -ForegroundColor Cyan
Write-Host "POSTGRES_PASSWORD=$(New-SecurePassword)" -ForegroundColor White
Write-Host ""

Write-Host "# Redis Credentials" -ForegroundColor Cyan
Write-Host "REDIS_PASSWORD=$(New-SecurePassword)" -ForegroundColor White
Write-Host ""

Write-Host "# MinIO Credentials" -ForegroundColor Cyan
Write-Host "MINIO_ACCESS_KEY=dop-minio-$(New-SecurePassword -Length 16)" -ForegroundColor White
Write-Host "MINIO_SECRET_KEY=$(New-SecurePassword)" -ForegroundColor White
Write-Host ""

Write-Host "# Airflow Credentials" -ForegroundColor Cyan
Write-Host "AIRFLOW_PASSWORD=$(New-SecurePassword)" -ForegroundColor White
Write-Host "AIRFLOW_FERNET_KEY=$(New-SecureKey)" -ForegroundColor White
Write-Host "AIRFLOW_SECRET_KEY=$(New-SecureKey)" -ForegroundColor White
Write-Host ""

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Copy these values to your .env.production files" -ForegroundColor Yellow
Write-Host "IMPORTANT: Store these securely!" -ForegroundColor Red
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Optionally save to a secure file
$save = Read-Host "Save to secure-keys.txt? (y/N)"
if ($save -eq "y" -or $save -eq "Y") {
    $keys = @"
# Generated on $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
# IMPORTANT: Keep this file secure and DO NOT commit to version control!

# Application Security
SECRET_KEY=$(New-SecureKey)
JWT_SECRET_KEY=$(New-SecureKey)

# Database Credentials
POSTGRES_PASSWORD=$(New-SecurePassword)

# Redis Credentials
REDIS_PASSWORD=$(New-SecurePassword)

# MinIO Credentials
MINIO_ACCESS_KEY=dop-minio-$(New-SecurePassword -Length 16)
MINIO_SECRET_KEY=$(New-SecurePassword)

# Airflow Credentials
AIRFLOW_PASSWORD=$(New-SecurePassword)
AIRFLOW_FERNET_KEY=$(New-SecureKey)
AIRFLOW_SECRET_KEY=$(New-SecureKey)
"@
    
    $keys | Out-File -FilePath "secure-keys.txt" -Encoding UTF8
    Write-Host "✅ Keys saved to secure-keys.txt" -ForegroundColor Green
    Write-Host "⚠️  Remember to delete this file after updating .env.production!" -ForegroundColor Yellow
}
