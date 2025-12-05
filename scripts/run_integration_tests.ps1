# Integration Test Runner
# Starts services and runs integration tests

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "TwinSelf Integration Test Runner" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if MLflow is running
Write-Host "Checking MLflow server..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✓ MLflow is running" -ForegroundColor Green
} catch {
    Write-Host "✗ MLflow not running. Starting MLflow..." -ForegroundColor Red
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "mlflow server --host 127.0.0.1 --port 5000"
    Write-Host "Waiting for MLflow to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}

# Check if MLOps server is running
Write-Host "Checking MLOps server..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8001/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✓ MLOps server is running" -ForegroundColor Green
} catch {
    Write-Host "✗ MLOps server not running. Starting..." -ForegroundColor Red
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "python mlops_server.py"
    Write-Host "Waiting for server to start (30s)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
}

# Run integration tests
Write-Host "`nRunning integration tests..." -ForegroundColor Cyan
pytest tests/test_integration.py -v -m integration

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Integration tests completed!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
