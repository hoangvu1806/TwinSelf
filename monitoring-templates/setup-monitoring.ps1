# Setup Prometheus + Grafana tự động
# Chạy: .\setup-monitoring.ps1

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Prometheus + Grafana Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker
Write-Host "Checking Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker not found!" -ForegroundColor Red
    Write-Host "Please install Docker Desktop first:" -ForegroundColor Red
    Write-Host "https://www.docker.com/products/docker-desktop/" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Create directories
Write-Host "Creating directories..." -ForegroundColor Yellow
$monitoringDir = "monitoring"
$prometheusDir = "$monitoringDir\prometheus"

if (Test-Path $monitoringDir) {
    Write-Host "⚠ monitoring/ already exists" -ForegroundColor Yellow
    $response = Read-Host "Overwrite? (y/n)"
    if ($response -ne "y") {
        Write-Host "Cancelled." -ForegroundColor Red
        exit 0
    }
    Remove-Item -Recurse -Force $monitoringDir
}

New-Item -ItemType Directory -Path $monitoringDir | Out-Null
New-Item -ItemType Directory -Path $prometheusDir | Out-Null
Write-Host "✓ Created directories" -ForegroundColor Green

Write-Host ""

# Create prometheus.yml
Write-Host "Creating prometheus.yml..." -ForegroundColor Yellow
$prometheusConfig = @"
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
"@

Set-Content -Path "$prometheusDir\prometheus.yml" -Value $prometheusConfig
Write-Host "✓ Created prometheus.yml" -ForegroundColor Green

Write-Host ""

# Create docker-compose.yml
Write-Host "Creating docker-compose.yml..." -ForegroundColor Yellow
$dockerCompose = @"
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3456:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
    restart: unless-stopped

volumes:
  prometheus-data:
  grafana-data:
"@

Set-Content -Path "$monitoringDir\docker-compose.yml" -Value $dockerCompose
Write-Host "✓ Created docker-compose.yml" -ForegroundColor Green

Write-Host ""

# Start containers
Write-Host "Starting containers..." -ForegroundColor Yellow
Set-Location $monitoringDir

try {
    docker-compose up -d
    Write-Host "✓ Containers started" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to start containers" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Set-Location ..
    exit 1
}

Write-Host ""

# Wait for services
Write-Host "Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check status
Write-Host ""
Write-Host "Checking status..." -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access services:" -ForegroundColor Yellow
Write-Host "  Prometheus: http://localhost:9090" -ForegroundColor Cyan
Write-Host "  Grafana:    http://localhost:3456" -ForegroundColor Cyan
Write-Host ""
Write-Host "Grafana Login:" -ForegroundColor Yellow
Write-Host "  Username: admin" -ForegroundColor Cyan
Write-Host "  Password: admin" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Open Grafana: http://localhost:3456" -ForegroundColor White
Write-Host "  2. Add Prometheus data source" -ForegroundColor White
Write-Host "  3. Create your first dashboard" -ForegroundColor White
Write-Host ""
Write-Host "See MONITORING_SIMPLE_SETUP.md for detailed guide" -ForegroundColor Yellow

Set-Location ..
