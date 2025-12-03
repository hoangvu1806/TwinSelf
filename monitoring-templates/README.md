# 📁 Monitoring Templates

## Quick Setup

### 1. Copy files này vào thư mục `monitoring/`

```powershell
# Tạo thư mục
mkdir monitoring
cd monitoring

# Copy docker-compose.yml vào đây
# Copy thư mục prometheus/ vào đây
```

### 2. Cấu trúc cuối cùng

```
monitoring/
├── docker-compose.yml          ← Copy từ monitoring-templates/
├── prometheus/
│   └── prometheus.yml          ← Copy từ monitoring-templates/prometheus/
```

### 3. Start

```powershell
docker-compose up -d
```

### 4. Access

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

---

## Xem hướng dẫn đầy đủ

→ `MONITORING_SIMPLE_SETUP.md`
