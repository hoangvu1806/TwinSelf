# TwinSelf Deployment Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TwinSelf Deployment Starting..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Stop Portfolio Server (port 8080)
Write-Host "[1/8] Stopping Portfolio Server..." -ForegroundColor Yellow
Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 3
Write-Host "Done" -ForegroundColor Green

# Stop MLflow Server (port 5000)
Write-Host "[2/8] Stopping MLflow Server..." -ForegroundColor Yellow
Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 3
Write-Host "Done" -ForegroundColor Green

# Pull latest code
Write-Host "[3/8] Pulling latest code..." -ForegroundColor Yellow
Set-Location D:\HOANGVU\VPS\TwinSelf
git fetch origin
git reset --hard origin/main
git clean -fd
Write-Host "Done" -ForegroundColor Green

# Rebuild data
Write-Host "[4/8] Rebuilding data..." -ForegroundColor Yellow
python scripts\smart_rebuild.py --create-version
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed" -ForegroundColor Red
    exit 1
}
Write-Host "Done" -ForegroundColor Green

# Start MLflow Server
Write-Host "[5/8] Starting MLflow Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd D:\HOANGVU\VPS\TwinSelf; mlflow server --host 0.0.0.0 --port 5000" -WindowStyle Minimized
Start-Sleep -Seconds 15
Write-Host "Done" -ForegroundColor Green

# Start Portfolio Server
Write-Host "[6/8] Starting Portfolio Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd D:\HOANGVU\VPS\TwinSelf; uvicorn portfolio_server:app --host 0.0.0.0 --port 8080 --workers 1" -WindowStyle Minimized
Start-Sleep -Seconds 30
Write-Host "Done" -ForegroundColor Green

# Health check
Write-Host "[7/8] Health check..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

$maxRetries = 7
$retryDelay = 10
$success = $false

for ($i = 1; $i -le $maxRetries; $i++) {
    Write-Host "Attempt $i/$maxRetries..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/chatbot/api/health" -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "Server is healthy!" -ForegroundColor Green
            $success = $true
            break
        }
    } catch {
        Write-Host "Health check failed, retrying in ${retryDelay}s..." -ForegroundColor Yellow
        if ($i -lt $maxRetries) {
            Start-Sleep -Seconds $retryDelay
        }
    }
}

if ($success) {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "DEPLOYMENT SUCCESS" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    exit 0
} else {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "DEPLOYMENT FAILED - Health check timeout" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    exit 1
}
