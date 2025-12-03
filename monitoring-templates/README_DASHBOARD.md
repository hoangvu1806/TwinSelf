# 📊 TwinSelf Dashboard Import Guide

## Dashboard: `twinself_dashboard.json`

Dashboard này hiển thị Prometheus self-monitoring metrics.

---

## 📈 Panels Included

1. **Prometheus Status** - Service UP/DOWN status
2. **Prometheus Memory Usage** - Memory consumption over time
3. **Current Memory** - Current memory usage (stat)
4. **Prometheus CPU Usage** - CPU usage over time
5. **Current CPU** - Current CPU usage (stat)
6. **Scrape Duration** - Time taken to scrape metrics
7. **Scrape Duration Over Time** - Scrape duration graph

---

## 🚀 How to Import

### Step 1: Access Grafana
```
http://localhost:3456
```
Login: `admin` / `admin`

### Step 2: Import Dashboard

1. Click **Menu** (☰) → **Dashboards**
2. Click **New** → **Import**
3. Click **Upload JSON file**
4. Select: `monitoring-templates/twinself_dashboard.json`
5. Click **Load**
6. Select data source: **prometheus-main**
7. Click **Import**

### Step 3: View Dashboard

Dashboard sẽ tự động mở với:
- Auto-refresh: 5 seconds
- Time range: Last 15 minutes
- All panels showing live data

---

## 🎨 Customization

### Change Refresh Rate

Top right → Click refresh dropdown → Select:
- 5s (default)
- 10s
- 30s
- 1m
- Off

### Change Time Range

Top right → Click time picker → Select:
- Last 5 minutes
- Last 15 minutes (default)
- Last 30 minutes
- Last 1 hour
- Custom range

### Edit Panels

1. Hover over panel title
2. Click **...** (three dots)
3. Click **Edit**
4. Modify query, visualization, or settings
5. Click **Apply**
6. Click **Save dashboard** (top right)

---

## 📊 Metrics Explained

### `up`
- Value: 1 = UP, 0 = DOWN
- Shows if Prometheus is scraping successfully

### `process_resident_memory_bytes`
- Memory used by Prometheus process
- Unit: Bytes
- Typical: 50-200 MB

### `rate(process_cpu_seconds_total[1m])`
- CPU usage rate over last 1 minute
- Unit: Percentage (0-1)
- Typical: 0.01-0.05 (1-5%)

### `scrape_duration_seconds`
- Time to scrape metrics from target
- Unit: Seconds
- Typical: 0.001-0.01 (1-10ms)

---

## 🔧 Troubleshooting

### No Data Showing

**Check:**
1. Data source connected: Connections → Data sources → Prometheus → Test
2. Time range: Set to "Last 15 minutes"
3. Prometheus running: `docker ps | findstr prometheus`
4. Query syntax: Try simple query `up` first

**Fix:**
```powershell
# Restart Prometheus
cd monitoring
docker-compose restart prometheus

# Check logs
docker logs prometheus
```

### "N/A" or "No data"

**Possible causes:**
1. Time range too old (Prometheus just started)
2. Data source URL wrong (should be `http://prometheus:9090`)
3. Prometheus not scraping (check targets in Prometheus UI)

**Fix:**
1. Change time range to "Last 5 minutes"
2. Verify data source URL
3. Check Prometheus targets: http://localhost:9090/targets

### Panels showing errors

**Check browser console:**
1. Press F12
2. Go to Console tab
3. Look for errors
4. Common: CORS, connection refused, timeout

---

## 💡 Tips

1. **Pin dashboard**: Click ⭐ to add to favorites
2. **Share dashboard**: Click Share → Export → Save JSON
3. **Duplicate panel**: Panel menu → More → Duplicate
4. **Add variables**: Dashboard settings → Variables
5. **Set alerts**: Panel edit → Alert tab

---

## 🎯 Next Steps

After importing this dashboard:

1. ✅ Verify all panels show data
2. ✅ Customize refresh rate and time range
3. ✅ Add more panels for your needs
4. ✅ Export and backup dashboard JSON
5. ✅ Create dashboards for TwinSelf API metrics

---

## 📝 Dashboard JSON Structure

```json
{
  "title": "TwinSelf - Prometheus Monitoring",
  "uid": "twinself-prometheus",
  "refresh": "5s",
  "time": {
    "from": "now-15m",
    "to": "now"
  },
  "panels": [...]
}
```

- **uid**: Unique identifier
- **refresh**: Auto-refresh interval
- **time**: Default time range
- **panels**: Array of visualization panels

---

Happy Monitoring! 📊✨
