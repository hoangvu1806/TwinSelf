# Portfolio Chatbot Server

A stateless chatbot server designed for portfolio websites with context-aware conversations.

## Features

- **Stateless Design**: Frontend provides conversation history
- **Context Awareness**: Understands current page, URL, and user context
- **Blog Post Integration**: Can read and discuss blog post content
- **Session Tracking**: Tracks user activity without storing history
- **Streaming Support**: Real-time response streaming
- **CORS Enabled**: Ready for frontend integration

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### Build Memory

```bash
python scripts/smart_rebuild.py --create-version
```

### Start Server

```bash
python portfolio_server.py
```

Server runs at: http://localhost:8080

## API Endpoints

### Health Check

```
GET /chatbot/api/health
```

Response:
```json
{
  "status": "healthy",
  "bot_name": "Hoàng Vũ",
  "active_sessions": 5
}
```

### Chat (Streaming)

```
POST /chatbot/api/chat/stream
```

Request:
```json
{
  "session_id": "user123",
  "message": "Tell me about your experience",
  "conversation": [
    {
      "id": 1,
      "role": "user",
      "content": "Hello",
      "timestamp": "2025-12-01T10:00:00"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "Hi! How can I help?",
      "timestamp": "2025-12-01T10:00:01"
    }
  ],
  "metadata": {
    "url": "https://yoursite.com/about",
    "timestamp": "2025-12-01T10:00:00",
    "page_title": "About Me",
    "context_type": "about_page"
  }
}
```

Response: Server-Sent Events (SSE)
```
data: I have
data:  5 years
data:  of experience...
data: [DONE]
```

### Chat (Non-Streaming)

```
POST /chatbot/api/chat
```

Request: Same as streaming

Response:
```json
{
  "response": "I have 5 years of experience...",
  "session_id": "user123",
  "bot_name": "Hoàng Vũ"
}
```

### List Sessions

```
GET /chatbot/api/sessions
```

Response:
```json
{
  "sessions": [
    {
      "session_id": "user123",
      "created_at": "2025-12-01T10:00:00",
      "last_activity": "2025-12-01T10:05:00",
      "message_count": 5
    }
  ],
  "total_sessions": 1
}
```

## Frontend Integration

### JavaScript Example

```javascript
// Streaming chat
const response = await fetch('http://localhost:8080/chatbot/api/chat/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: 'user123',
    message: 'What are your skills?',
    conversation: conversationHistory,
    metadata: {
      url: window.location.href,
      timestamp: new Date().toISOString(),
      page_title: document.title,
      context_type: 'skills_page'
    }
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const content = line.slice(6);
      if (content === '[DONE]') break;
      console.log(content);
    }
  }
}
```

### React Example

```jsx
import { useState } from 'react';

function ChatBot() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  const sendMessage = async () => {
    const response = await fetch('http://localhost:8080/chatbot/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: 'user123',
        message: input,
        conversation: messages,
        metadata: {
          url: window.location.href,
          timestamp: new Date().toISOString(),
          page_title: document.title
        }
      })
    });

    const data = await response.json();
    setMessages([...messages, 
      { role: 'user', content: input },
      { role: 'assistant', content: data.response }
    ]);
    setInput('');
  };

  return (
    <div>
      {messages.map((msg, i) => (
        <div key={i}>{msg.role}: {msg.content}</div>
      ))}
      <input value={input} onChange={e => setInput(e.target.value)} />
      <button onClick={sendMessage}>Send</button>
    </div>
  );
}
```

## Blog Post Integration

The server can read blog post content when user asks about specific posts:

```json
{
  "message": "What is this post about?",
  "ask": "summarize",
  "metadata": {
    "url": "https://yoursite.com/blog/my-post",
    "context_type": "blog_post"
  }
}
```

Configure blog post directory in `portfolio_server.py`:
```python
post_dir = r"path/to/your/blog/posts"
```

## Configuration

### Environment Variables

```bash
# .env
GOOGLE_API_KEY=your_api_key
HOST=0.0.0.0
PORT=8080
RELOAD=true
```

### Server Settings

Edit `portfolio_server.py`:
```python
# Bot name
chatbot = DigitalTwinChatbot(bot_name="Your Name")

# Blog post directory
post_dir = r"path/to/posts"

# Port
port = int(os.getenv("PORT", "8080"))
```

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python scripts/smart_rebuild.py

EXPOSE 8080
CMD ["python", "portfolio_server.py"]
```

### Nginx Reverse Proxy

```nginx
location /chatbot/api/ {
    proxy_pass http://localhost:8080/chatbot/api/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
}
```

## Tech Stack

- **Framework**: FastAPI
- **LLM**: Google Gemini
- **Vector DB**: Qdrant (local)
- **Embeddings**: Vietnamese Document Embedding

## License

MIT License

## Author

Hoang Vu - [GitHub](https://github.com/hoangvu1806)
