<#
.SYNOPSIS
    Deploy AWS Glue jobs to AWS

.DESCRIPTION
    This script automates the deployment of Glue job scripts to S3 and creates/updates Glue job definitions.

.PARAMETER JobName
    Name of the Glue job (default: dop-dataset-ingestion-job)

.PARAMETER ScriptBucket
    S3 bucket for Glue scripts

.PARAMETER IamRole
    IAM role ARN for Glue job execution

.PARAMETER Region
    AWS region (default: us-east-1)

.PARAMETER WorkerType
    Glue worker type (default: G.1X)

.PARAMETER Workers
    Number of workers (default: 2)

.EXAMPLE
    .\deploy-glue-jobs.ps1 -ScriptBucket my-glue-scripts -IamRole arn:aws:iam::123456789:role/GlueRole
#>

param(
    [string]$JobName = "dop-dataset-ingestion-job",
    [Parameter(Mandatory=$true)]
    [string]$ScriptBucket,
    [Parameter(Mandatory=$true)]
    [string]$IamRole,
    [string]$Region = "us-east-1",
    [string]$WorkerType = "G.1X",
    [int]$Workers = 2
)

$ErrorActionPreference = "Stop"

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "AWS Glue Job Deployment" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# Check if AWS CLI is installed
try {
    $awsVersion = aws --version
    Write-Host "✓ AWS CLI found: $awsVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ AWS CLI not found. Please install AWS CLI first." -ForegroundColor Red
    exit 1
}

# Check AWS credentials
Write-Host "`nChecking AWS credentials..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity --query "Account" --output text 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ AWS credentials configured (Account: $identity)" -ForegroundColor Green
    } else {
        throw "Credentials check failed"
    }
} catch {
    Write-Host "✗ AWS credentials not configured or invalid" -ForegroundColor Red
    Write-Host "  Run: aws configure" -ForegroundColor Yellow
    exit 1
}

# Validate script file exists
$scriptPath = "backend\glue_jobs\dataset_ingestion_job.py"
if (-not (Test-Path $scriptPath)) {
    Write-Host "✗ Script not found: $scriptPath" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Script found: $scriptPath" -ForegroundColor Green

# Upload script to S3
Write-Host "`nUploading script to S3..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$s3Key = "scripts/dataset_ingestion_job_${timestamp}.py"
$s3Uri = "s3://${ScriptBucket}/${s3Key}"

try {
    aws s3 cp $scriptPath $s3Uri --region $Region
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Script uploaded to: $s3Uri" -ForegroundColor Green
    } else {
        throw "Upload failed"
    }
} catch {
    Write-Host "✗ Failed to upload script to S3" -ForegroundColor Red
    Write-Host "  Check bucket exists and you have write permissions" -ForegroundColor Yellow
    exit 1
}

# Check if job exists
Write-Host "`nChecking if Glue job exists..." -ForegroundColor Yellow
$jobExists = $false
try {
    aws glue get-job --job-name $JobName --region $Region 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $jobExists = $true
        Write-Host "✓ Job exists: $JobName" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✓ Job does not exist, will create new" -ForegroundColor Green
}

# Create or update Glue job
if ($jobExists) {
    Write-Host "`nUpdating existing Glue job..." -ForegroundColor Yellow
    
    $updateCommand = @"
aws glue update-job ``
  --job-name $JobName ``
  --job-update '{
    \"Role\": \"$IamRole\",
    \"Command\": {
      \"Name\": \"glueetl\",
      \"ScriptLocation\": \"$s3Uri\",
      \"PythonVersion\": \"3\"
    },
    \"DefaultArguments\": {
      \"--enable-metrics\": \"true\",
      \"--enable-spark-ui\": \"true\",
      \"--enable-job-insights\": \"true\",
      \"--job-language\": \"python\"
    },
    \"GlueVersion\": \"4.0\",
    \"WorkerType\": \"$WorkerType\",
    \"NumberOfWorkers\": $Workers,
    \"Timeout\": 2880,
    \"MaxRetries\": 1
  }' ``
  --region $Region
"@
    
    try {
        Invoke-Expression $updateCommand
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Glue job updated successfully" -ForegroundColor Green
        } else {
            throw "Update failed"
        }
    } catch {
        Write-Host "✗ Failed to update Glue job" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "`nCreating new Glue job..." -ForegroundColor Yellow
    
    $createCommand = @"
aws glue create-job ``
  --name $JobName ``
  --role $IamRole ``
  --command Name=glueetl,ScriptLocation=$s3Uri,PythonVersion=3 ``
  --default-arguments '{
    \"--enable-metrics\":\"true\",
    \"--enable-spark-ui\":\"true\",
    \"--enable-job-insights\":\"true\",
    \"--job-language\":\"python\"
  }' ``
  --glue-version 4.0 ``
  --worker-type $WorkerType ``
  --number-of-workers $Workers ``
  --timeout 2880 ``
  --max-retries 1 ``
  --region $Region
"@
    
    try {
        Invoke-Expression $createCommand
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Glue job created successfully" -ForegroundColor Green
        } else {
            throw "Creation failed"
        }
    } catch {
        Write-Host "✗ Failed to create Glue job" -ForegroundColor Red
        exit 1
    }
}

# Summary
Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan
Write-Host "Deployment Summary" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Job Name:        $JobName" -ForegroundColor White
Write-Host "Script Location: $s3Uri" -ForegroundColor White
Write-Host "IAM Role:        $IamRole" -ForegroundColor White
Write-Host "Region:          $Region" -ForegroundColor White
Write-Host "Worker Type:     $WorkerType" -ForegroundColor White
Write-Host "Workers:         $Workers" -ForegroundColor White
Write-Host ""
Write-Host "✓ Deployment completed successfully!" -ForegroundColor Green
Write-Host ""

# Next steps
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Update .env with GLUE_JOB_NAME=$JobName" -ForegroundColor White
Write-Host "2. Set EXECUTION_MODE=glue in .env" -ForegroundColor White
Write-Host "3. Restart backend: docker-compose restart backend" -ForegroundColor White
Write-Host "4. Test: curl http://localhost:8000/api/v1/glue/environment" -ForegroundColor White
Write-Host ""
