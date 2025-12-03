# Deployment

## Local Development

### Requirements

```bash
pip install -r requirements.txt
```

### Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required variables:
- `GOOGLE_API_KEY`: Gemini API key for chat
- `GOOGLE_API_KEY_4DEEPEVAL`: Gemini API key for evaluation (optional)

### Start Server

```bash
# Development with auto-reload
python mlops_server.py

# Or with uvicorn directly
uvicorn mlops_server:app --host 0.0.0.0 --port 8001 --reload
```

## Production Deployment

### 1. Prepare Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Build Memory

```bash
python scripts/smart_rebuild.py --create-version
```

### 3. Configure Environment

```bash
# .env
GOOGLE_API_KEY=your_production_key
MLFLOW_TRACKING_URI=http://mlflow-server:5000
HOST=0.0.0.0
PORT=8001
RELOAD=false
```

### 4. Start with Gunicorn (Linux)

```bash
gunicorn mlops_server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8001
```

### 5. Start with Uvicorn (Windows)

```bash
uvicorn mlops_server:app --host 0.0.0.0 --port 8001 --workers 4
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Build memory
RUN python scripts/smart_rebuild.py

EXPOSE 8001

CMD ["uvicorn", "mlops_server:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Build and Run

```bash
docker build -t twinself .
docker run -p 8001:8001 --env-file .env twinself
```

### Docker Compose

```yaml
version: '3.8'

services:
  twinself:
    build: .
    ports:
      - "8001:8001"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./mlruns:/app/mlruns

  mlflow:
    image: ghcr.io/mlflow/mlflow:latest
    ports:
      - "5000:5000"
    command: mlflow ui --host 0.0.0.0
    volumes:
      - ./mlruns:/mlruns
```

## Cloud Deployment

### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/twinself

# Deploy
gcloud run deploy twinself \
  --image gcr.io/PROJECT_ID/twinself \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=your_key
```

### AWS ECS

1. Create ECR repository
2. Push Docker image
3. Create ECS task definition
4. Create ECS service

### Heroku

```bash
# Create Procfile
echo "web: uvicorn mlops_server:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
heroku create twinself
heroku config:set GOOGLE_API_KEY=your_key
git push heroku main
```

## Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## SSL/TLS

### Let's Encrypt with Certbot

```bash
sudo certbot --nginx -d api.yourdomain.com
```

## Health Checks

### Kubernetes Liveness Probe

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8001
  initialDelaySeconds: 30
  periodSeconds: 10
```

### Docker Healthcheck

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1
```

## Scaling

### Horizontal Scaling

- Use load balancer (nginx, HAProxy, cloud LB)
- Each instance has its own Qdrant data
- Share MLflow server across instances

### Considerations

- Qdrant data is local, not shared
- For shared data, use Qdrant Cloud or hosted instance
- MLflow can be shared across instances

## Monitoring

### Prometheus Metrics

Add to server for custom metrics:

```python
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter('requests_total', 'Total requests')
RESPONSE_TIME = Histogram('response_time_seconds', 'Response time')
```

### Logging

Configure structured logging:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Backup

### Data Backup

```bash
# Backup Qdrant data
tar -czf backup_qdrant.tar.gz data/qdrant/

# Backup version registry
cp data/version_registry.json backup_version_registry.json

# Backup MLflow
tar -czf backup_mlruns.tar.gz mlruns/
```

### Restore

```bash
# Restore Qdrant
tar -xzf backup_qdrant.tar.gz

# Restore version registry
cp backup_version_registry.json data/version_registry.json
```

## Security

### API Key Protection

- Never commit `.env` to git
- Use secrets manager in production
- Rotate keys regularly

### Rate Limiting

Add rate limiting middleware:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/chat")
@limiter.limit("10/minute")
async def chat(request: Request):
    ...
```

### Input Validation

- Message length limits
- Session ID validation
- Content filtering
