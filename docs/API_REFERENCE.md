# API Reference

## Base URL

- Production: `http://localhost:8001`
- Simple: `http://localhost:8000`

## Endpoints

### Health Check

```
GET /health
```

Response:
```json
{
  "status": "healthy",
  "bot_name": "HoangVu",
  "mlflow_connected": true,
  "deepeval_enabled": true
}
```

### Chat

```
POST /chat
```

Request:
```json
{
  "session_id": "string",
  "message": "string",
  "conversation": [
    {"role": "user", "content": "previous message"},
    {"role": "assistant", "content": "previous response"}
  ],
  "track_quality": true
}
```

Response:
```json
{
  "session_id": "string",
  "response": "string",
  "bot_name": "string",
  "metrics": {
    "response_time": 1.2,
    "total_tokens": 450,
    "cost_usd": 0.00015,
    "quality_evaluation": "evaluating_in_background"
  }
}
```

Parameters:
- `session_id` (required): Unique session identifier
- `message` (required): User message
- `conversation` (optional): Previous conversation history
- `track_quality` (optional, default: true): Enable DeepEval quality tracking

### Chat Stream

```
POST /chat/stream
```

Request: Same as `/chat`

Response: Server-Sent Events (SSE)
```
data: Hello
data: , how
data:  can
data:  I help?
data: [DONE]
```

### Submit Feedback

```
POST /api/edit-message/suggestion
```

Request:
```json
{
  "original_question": "string",
  "original_response": "string",
  "suggested_response": "string"
}
```

Response:
```json
{
  "status": "success",
  "message": "Suggestion saved successfully. Total suggestions: 5",
  "saved_to": "episodic_data/user_suggestions.json"
}
```

### Root Info

```
GET /
```

Response:
```json
{
  "name": "TwinSelf MLOps API",
  "version": "1.0.0",
  "features": [
    "MLflow experiment tracking",
    "DeepEval quality evaluation",
    "Token and cost tracking",
    "Streaming support",
    "User feedback collection"
  ],
  "endpoints": {
    "health": "GET /health",
    "chat": "POST /chat",
    "stream": "POST /chat/stream",
    "edit_suggestion": "POST /api/edit-message/suggestion"
  },
  "docs": "/docs"
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Message cannot be empty"
}
```

### 503 Service Unavailable
```json
{
  "detail": "Chatbot not initialized"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Chat error: <error message>"
}
```

## Examples

### Python

```python
import requests

response = requests.post(
    "http://localhost:8001/chat",
    json={
        "session_id": "user123",
        "message": "What are your skills?"
    }
)

print(response.json()["response"])
```

### JavaScript

```javascript
const response = await fetch("http://localhost:8001/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    session_id: "user123",
    message: "What are your skills?"
  })
});

const data = await response.json();
console.log(data.response);
```

### cURL

```bash
curl -X POST "http://localhost:8001/chat" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test","message":"Hello"}'
```

### Streaming (Python)

```python
import requests

response = requests.post(
    "http://localhost:8001/chat/stream",
    json={"session_id": "test", "message": "Hello"},
    stream=True
)

for line in response.iter_lines():
    if line:
        data = line.decode("utf-8")
        if data.startswith("data: "):
            content = data[6:]
            if content != "[DONE]":
                print(content, end="", flush=True)
```

## Rate Limits

No built-in rate limits. Implement at reverse proxy level if needed.

## Authentication

No built-in authentication. Add middleware or reverse proxy for production.

## CORS

All origins allowed by default. Configure in `mlops_server.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
