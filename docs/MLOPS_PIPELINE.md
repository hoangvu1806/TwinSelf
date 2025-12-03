# MLOps Pipeline

## Overview

The MLOps pipeline integrates:
- MLflow for experiment tracking
- DeepEval for quality evaluation
- Prometheus/Grafana for monitoring (optional)

## MLflow Integration

### Setup

```bash
# Start MLflow server
mlflow ui --host 0.0.0.0 --port 5000

# Set environment variable
export MLFLOW_TRACKING_URI=http://localhost:5000
```

### Tracked Metrics

Per request:
- `input_tokens`: Estimated input tokens
- `output_tokens`: Estimated output tokens
- `total_tokens`: Total tokens used
- `response_time_seconds`: Response generation time
- `total_time_seconds`: Total request time
- `input_cost_usd`: Estimated input cost
- `output_cost_usd`: Estimated output cost
- `total_cost_usd`: Total estimated cost

Quality metrics (async):
- `deepeval_answer_relevancy`: Answer relevance score (0-1)
- `deepeval_faithfulness`: Faithfulness to context score (0-1)

### View Metrics

Open MLflow UI: http://localhost:5000

Navigate to experiment "twinself_production" to see all runs.

## DeepEval Integration

### How It Works

1. User sends chat request with `track_quality: true`
2. Server generates response immediately
3. Background process runs DeepEval evaluation
4. Metrics logged to MLflow asynchronously

### Evaluation Metrics

**Answer Relevancy**
- Measures if response answers the question
- Score: 0.0 to 1.0
- Threshold: 0.7

**Faithfulness**
- Measures if response is faithful to retrieved context
- Score: 0.0 to 1.0
- Threshold: 0.7

### Configuration

DeepEval uses a separate API key to avoid quota conflicts:

```bash
# .env
GOOGLE_API_KEY=your_main_key
GOOGLE_API_KEY_4DEEPEVAL=your_deepeval_key
```

### Evaluation Script

Runs in separate process to avoid async conflicts:

```bash
# Manual test
python scripts/run_deepeval_evaluation.py \
  "What are your skills?" \
  "I am proficient in Python..." \
  "Context from retrieval" \
  "mlflow_run_id"
```

## Monitoring Setup (Optional)

### Docker Compose

```bash
cd monitoring-templates
docker-compose up -d
```

Services:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

### Grafana Dashboard

Import `monitoring-templates/twinself_dashboard.json` for pre-built dashboard.

## Pipeline Flow

```
1. User Request
   |
   v
2. MLflow Run Start
   - Log parameters (session_id, message_length)
   |
   v
3. Generate Response
   - Retrieve context from Qdrant
   - Generate with Gemini
   |
   v
4. Log Metrics
   - Tokens, cost, response time
   |
   v
5. Return Response
   |
   v
6. Background Evaluation (async)
   - Run DeepEval in separate process
   - Log quality metrics to MLflow
```

## Cost Tracking

Estimated costs based on Gemini pricing:
- Input: $0.075 per 1M tokens
- Output: $0.30 per 1M tokens

Example for 1000 requests:
- Average 500 tokens per request
- Total: 500K tokens
- Cost: ~$0.04 input + ~$0.15 output = ~$0.19

## Best Practices

### 1. Sample Evaluation

For high traffic, sample evaluation to reduce costs:

```python
import random

# Evaluate 10% of requests
track_quality = random.random() < 0.1
```

### 2. Monitor Quota

Check Gemini API quota:
- https://ai.dev/usage?tab=rate-limit

### 3. Regular Review

Weekly review of MLflow metrics:
- Average response time
- Quality scores trend
- Cost per request

### 4. Version Tracking

Always create version when updating data:

```bash
python scripts/smart_rebuild.py --create-version
```

## Troubleshooting

### MLflow not connecting

```bash
# Check MLflow server
curl http://localhost:5000/api/2.0/mlflow/experiments/list

# Check environment
echo $MLFLOW_TRACKING_URI
```

### DeepEval not running

```bash
# Check logs for errors
tail -f server.log | grep "evaluation"

# Test script directly
python scripts/run_deepeval_evaluation.py test test test test
```

### Metrics not appearing

1. Wait 30-60 seconds for async evaluation
2. Refresh MLflow UI
3. Check server logs for errors
