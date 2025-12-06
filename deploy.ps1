# TwinSelf Deployment Script
# Run this manually or via CD pipeline

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "TwinSelf Deployment Starting..." -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Stop Portfolio Server (port 8080)
Write-Host "[1/8] Stopping Portfolio Server..." -ForegroundColor Yellow
$process = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
if ($process) {
    Stop-Process -Id $process -Force
    Write-Host "✓ Portfolio Server stopped" -ForegroundColor Green
} else {
    Write-Host "No process on port 8080" -ForegroundColor Gray
}
Start-Sleep -Seconds 3

# Stop MLflow Server (port 5000)
Write-Host "`n[2/8] Stopping MLflow Server..." -ForegroundColor Yellow
$process = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
if ($process) {
    Stop-Process -Id $process -Force
    Write-Host "✓ MLflow Server stopped" -ForegroundColor Green
} else {
    Write-Host "No process on port 5000" -ForegroundColor Gray
}
Start-Sleep -Seconds 3

# Pull latest code
Write-Host "`n[3/8] Pulling latest code..." -ForegroundColor Yellow
Set-Location D:\HOANGVU\VPS\TwinSelf
git fetch origin
git reset --hard origin/main
git clean -fd
Write-Host "✓ Code updated" -ForegroundColor Green

# Rebuild data
Write-Host "`n[4/8] Rebuilding data..." -ForegroundColor Yellow
python scripts\smart_rebuild.py --create-version
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Data rebuild failed" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Data rebuilt" -ForegroundColor Green

# Start MLflow Server
Write-Host "`n[5/8] Starting MLflow Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd D:\HOANGVU\VPS\TwinSelf; mlflow server --host 0.0.0.0 --port 5000" -WindowStyle Minimized
Start-Sleep -Seconds 10
Write-Host "✓ MLflow Server started" -ForegroundColor Green

# Wait for MLflow
Write-Host "`n[6/8] Waiting for MLflow..." -ForegroundColor Yellow
$maxRetries = 15
for ($i = 0; $i -lt $maxRetries; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/health" -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ MLflow is ready" -ForegroundColor Green
            break
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}

# Start Portfolio Server
Write-Host "`n[7/8] Starting Portfolio Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd D:\HOANGVU\VPS\TwinSelf; uvicorn portfolio_server:app --host 0.0.0.0 --port 8080 --workers 1" -WindowStyle Minimized
Start-Sleep -Seconds 30
Write-Host "✓ Portfolio Server started" -ForegroundColor Green

# Health check
Write-Host "`n[8/8] Health check..." -ForegroundColor Yellow
$maxRetries = 30
$healthy = $false
for ($i = 0; $i -lt $maxRetries; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/chatbot/api/health" -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $data = $response.Content | ConvertFrom-Json
            Write-Host "✓ Server is healthy!" -ForegroundColor Green
            Write-Host "  Bot: $($data.bot_name)" -ForegroundColor Cyan
            Write-Host "  MLflow: $($data.mlflow_connected)" -ForegroundColor Cyan
            $healthy = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
if ($healthy) {
    Write-Host "✓ DEPLOYMENT SUCCESS" -ForegroundColor Green
    Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
    Write-Host "Portfolio: http://localhost:8080/chatbot/api/" -ForegroundColor Cyan
    Write-Host "MLflow:    http://localhost:5000" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    exit 0
} else {
    Write-Host "✗ DEPLOYMENT FAILED" -ForegroundColor Red
    Write-Host "Health check timeout" -ForegroundColor Red
    Write-Host "========================================`n" -ForegroundColor Cyan
    exit 1
}
