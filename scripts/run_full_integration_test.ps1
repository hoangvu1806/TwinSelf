# Full Integration Test Pipeline
# 1. Rebuild data
# 2. Start MLflow server
# 3. Start MLOps server
# 4. Run integration tests
# 5. Cleanup

param(
    [switch]$SkipRebuild = $false
)

$ErrorActionPreference = "Stop"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "TwinSelf Full Integration Test Pipeline" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Step 1: Rebuild data
if (-not $SkipRebuild) {
    Write-Host "[1/5] Rebuilding data..." -ForegroundColor Yellow
    python scripts/smart_rebuild.py --create-version
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Data rebuild failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Data rebuilt successfully`n" -ForegroundColor Green
} else {
    Write-Host "[1/5] Skipping data rebuild`n" -ForegroundColor Yellow
}

# Step 2: Start MLflow server
Write-Host "[2/5] Starting MLflow server..." -ForegroundColor Yellow
$mlflowProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "mlflow server --host 127.0.0.1 --port 5000" -PassThru
Write-Host "✓ MLflow server started (PID: $($mlflowProcess.Id))" -ForegroundColor Green

# Wait for MLflow to be ready
Write-Host "Waiting for MLflow to be ready..." -ForegroundColor Yellow
$maxRetries = 30
$mlflowReady = $false
for ($i = 0; $i -lt $maxRetries; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/health" -TimeoutSec 1 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $mlflowReady = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}

if (-not $mlflowReady) {
    Write-Host "✗ MLflow failed to start" -ForegroundColor Red
    Stop-Process -Id $mlflowProcess.Id -Force
    exit 1
}
Write-Host "✓ MLflow is ready`n" -ForegroundColor Green

# Step 3: Start MLOps server
Write-Host "[3/5] Starting MLOps server..." -ForegroundColor Yellow
$mlopsProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "python mlops_server.py" -PassThru
Write-Host "✓ MLOps server started (PID: $($mlopsProcess.Id))" -ForegroundColor Green

# Wait for MLOps server to be ready
Write-Host "Waiting for MLOps server to initialize (this may take 30-60s)..." -ForegroundColor Yellow
$maxRetries = 60
$mlopsReady = $false
for ($i = 0; $i -lt $maxRetries; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8001/health" -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $mlopsReady = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}

if (-not $mlopsReady) {
    Write-Host "✗ MLOps server failed to start" -ForegroundColor Red
    Stop-Process -Id $mlflowProcess.Id -Force
    Stop-Process -Id $mlopsProcess.Id -Force
    exit 1
}
Write-Host "✓ MLOps server is ready`n" -ForegroundColor Green

# Step 4: Run integration tests
Write-Host "[4/5] Running integration tests..." -ForegroundColor Yellow
pytest tests/test_integration.py -v -m integration

$testResult = $LASTEXITCODE

if ($testResult -eq 0) {
    Write-Host "`n✓ All integration tests passed!" -ForegroundColor Green
} else {
    Write-Host "`n✗ Some integration tests failed" -ForegroundColor Red
}

# Step 5: Cleanup
Write-Host "`n[5/5] Cleaning up..." -ForegroundColor Yellow
Write-Host "Stopping MLOps server..." -ForegroundColor Yellow
Stop-Process -Id $mlopsProcess.Id -Force -ErrorAction SilentlyContinue
Write-Host "Stopping MLflow server..." -ForegroundColor Yellow
Stop-Process -Id $mlflowProcess.Id -Force -ErrorAction SilentlyContinue
Write-Host "✓ Cleanup completed`n" -ForegroundColor Green

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Integration Test Pipeline Completed!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

exit $testResult
