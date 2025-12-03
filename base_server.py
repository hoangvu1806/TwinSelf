"""
Simple TwinSelf API Server
Minimal endpoints: chat and stream with session tracking
"""
import os
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from twinself import DigitalTwinChatbot


# Global chatbot instance
chatbot: Optional[DigitalTwinChatbot] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize chatbot on startup"""
    global chatbot
    try:
        chatbot = DigitalTwinChatbot(bot_name=os.getenv("USER_NAME", "Hoàng Vũ"))
        print("Chatbot initialized successfully!")
        yield
    finally:
        print("Shutting down server...")


# Create FastAPI app
app = FastAPI(
    title="TwinSelf Simple API",
    description="Simple chat API with session support",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    session_id: str
    message: str
    conversation: List[Message] = []


class ChatResponse(BaseModel):
    session_id: str
    response: str
    bot_name: str


# Health check
@app.get("/health")
async def health_check():
    """Check if server is healthy"""
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    return {
        "status": "healthy",
        "bot_name": chatbot.bot_name
    }


# Chat endpoint (non-streaming)
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the bot (non-streaming response)
    
    Example:
    ```json
    {
        "session_id": "user123",
        "message": "Hello, who are you?",
        "conversation": [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello! How can I help?"}
        ]
    }
    ```
    """
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Build context from conversation history
    context = _build_context(request.conversation)
    
    try:
        response = chatbot.chat(
            user_message=request.message,
            context=context,
            stream=False,
            save_history=False
        )
        
        return ChatResponse(
            session_id=request.session_id,
            response=response,
            bot_name=chatbot.bot_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


# Stream endpoint
@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Chat with the bot (streaming response)
    
    Returns Server-Sent Events (SSE) stream
    
    Example:
    ```json
    {
        "session_id": "user123",
        "message": "Tell me about yourself",
        "conversation": []
    }
    ```
    """
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Build context from conversation history
    context = _build_context(request.conversation)
    
    async def generate():
        try:
            for chunk in chatbot.chat(
                user_message=request.message,
                context=context,
                stream=True,
                save_history=False
            ):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# Helper function
def _build_context(conversation: List[Message]) -> str:
    """Build context string from conversation history"""
    if not conversation:
        return ""
    
    context_lines = ["=== Recent Conversation ==="]
    for msg in conversation[-5:]:  # Last 5 messages
        role = "User" if msg.role == "user" else chatbot.bot_name
        context_lines.append(f"{role}: {msg.content}")
    
    return "\n".join(context_lines)


# Root endpoint
@app.get("/")
async def root():
    """API information"""
    return {
        "name": "TwinSelf Simple API",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /health",
            "chat": "POST /chat",
            "stream": "POST /chat/stream"
        },
        "docs": "/docs"
    }


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print(f"Starting TwinSelf Simple API on {host}:{port}")
    print(f"API docs: http://{host}:{port}/docs")
    
    uvicorn.run(
        "base_server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
