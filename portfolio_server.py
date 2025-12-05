import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from twinself import DigitalTwinChatbot


# Global chatbot + simple session registry (no history stored)
chatbot: Optional[DigitalTwinChatbot] = None
sessions: Dict[str, Dict[str, Any]] = {}
post_dir = r"D:\HOANGVU\VPS\VuxPortfolio\src\data\blog\posts"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize chatbot on startup"""
    global chatbot
    try:
        chatbot = DigitalTwinChatbot(bot_name="Hoàng Vũ")
        print("Chatbot initialized successfully!")
        yield
    finally:
        print("Shutting down server...")


# Create FastAPI app
app = FastAPI(
    title="TwinSelf Digital Twin API",
    description="Stateless API with session tracking and context awareness",
    version="2.1.0",
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
class ConversationMessage(BaseModel):
    id: int
    role: str
    content: str
    timestamp: str


class RequestMetadata(BaseModel):
    url: Optional[str] = None
    timestamp: str
    user_agent: Optional[str] = None
    page_title: Optional[str] = None
    user_id: Optional[str] = None
    context_type: Optional[str] = None


class ChatRequest(BaseModel):
    session_id: str
    message: str
    ask: Optional[str] = None
    conversation: List[ConversationMessage] = []
    metadata: RequestMetadata


class HealthResponse(BaseModel):
    status: str
    bot_name: str
    active_sessions: int

def get_post_detail(url:str) -> str:
    for f in os.listdir(post_dir):
        if url.split("/")[-1] in f:
            file_path = post_dir+"/"+f
            with open(file_path, "r", encoding="utf-8") as p:
                return p.read()
            
# Session management (just track activity, not history)
def get_or_create_session(session_id: str, metadata: RequestMetadata) -> Dict[str, Any]:
    if session_id not in sessions:
        sessions[session_id] = {
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "message_count": 0
        }
    else:
        sessions[session_id]["last_activity"] = datetime.now().isoformat()
    return sessions[session_id]


def build_context(request: ChatRequest) -> str:
    """Build enhanced context from metadata + FE conversation"""
    ctx = []
    
    ctx.append("=== Current Context ===")
    if request.metadata.page_title:
        ctx.append(f"Page: {request.metadata.page_title}")
    if request.metadata.url:
        ctx.append(f"URL: {request.metadata.url}")
    if request.metadata.context_type:
        ctx.append(f"Context Type: {request.metadata.context_type}")

    if request.conversation:
        ctx.append("\n=== Recent Conversation ===")
        for msg in request.conversation[-5:]:
            role = "User" if msg.role == "user" else chatbot.bot_name
            ctx.append(f"{role}: {msg.content}")

    if request.ask:
        post_content = get_post_detail(request.metadata.url)
        ctx.append("\n=== Specific Context ===")
        ctx.append(f"Additional: ***{request.ask}*** at {request.metadata.url}")
        ctx.append(f"The post content is: \n{post_content}\n")

    return "\n".join(ctx)


# Health check
@app.get("/chatbot/api/health", response_model=HealthResponse)
async def health_check():
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    return HealthResponse(
        status="healthy",
        bot_name=chatbot.bot_name,
        active_sessions=len(sessions)
    )


# Streaming chat
@app.post("/chatbot/api/chat/stream")
async def chat_stream(request: ChatRequest):
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session = get_or_create_session(request.session_id, request.metadata)
    context = build_context(request)
    # full_message = f"{context}\n\n=== User Message ===\n{request.message}" if context else request.message
    session["message_count"] += 1

    async def generate():
        try:
            for chunk in chatbot.chat(user_message=request.message, context=context, stream=True, save_history=False):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: Error: {str(e)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# Full chat (non-stream)
@app.post("/chatbot/api/chat")
async def chat(request: ChatRequest):
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session = get_or_create_session(request.session_id, request.metadata)
    context = build_context(request)
    full_message = f"{context}\n\n=== User Message ===\n{request.message}" if context else request.message
    session["message_count"] += 1

    try:
        response = chatbot.chat(full_message, stream=False)
        return {
            "response": response,
            "session_id": request.session_id,
            "bot_name": chatbot.bot_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


# Session list (just info, no history)
@app.get("/chatbot/api/sessions")
async def list_sessions():
    return {
        "sessions": [
            {"session_id": sid, **session} for sid, session in sessions.items()
        ],
        "total_sessions": len(sessions)
    }


# Root
@app.get("/chatbot/api/")
async def root():
    return {
        "message": "TwinSelf Digital Twin API (stateless)",
        "version": "2.1.0",
        "features": [
            "Stateless (FE provides history)",
            "Session activity tracking",
            "Metadata support",
            "Streaming & non-streaming chat"
        ]
    }


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    reload = os.getenv("RELOAD", "true").lower() == "true"

    print(f"Starting TwinSelf API server on {host}:{port}")
    uvicorn.run("advanced_server:app", host=host, port=port, reload=reload, log_level="info")
