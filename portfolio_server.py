import os
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from twinself import DigitalTwinChatbot

# MLflow
import mlflow
from mlflow.tracking import MlflowClient

# Token counting
import tiktoken


# Global chatbot + simple session registry (no history stored)
chatbot: Optional[DigitalTwinChatbot] = None
sessions: Dict[str, Dict[str, Any]] = {}
post_dir = r"D:\HOANGVU\VPS\VuxPortfolio\src\data\blog\posts"

# MLflow setup
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment("portfolio_chatbot")

try:
    mlflow_client = MlflowClient()
    mlflow_client.search_experiments()
    print(f"MLflow connected: {MLFLOW_TRACKING_URI}")
except Exception as e:
    mlflow_client = None
    print(f"MLflow not available: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize chatbot on startup"""
    global chatbot
    try:
        chatbot = DigitalTwinChatbot(bot_name="Hoàng Vũ")
        print("Chatbot initialized successfully!")
        
        # Log server startup to MLflow
        if mlflow_client:
            try:
                with mlflow.start_run(run_name=f"server_startup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
                    mlflow.log_param("server_type", "portfolio_chatbot")
                    mlflow.log_param("bot_name", chatbot.bot_name)
                    mlflow.log_param("startup_time", datetime.now().isoformat())
            except Exception as e:
                print(f"MLflow startup log failed: {e}")
        
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


def _estimate_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Count tokens using tiktoken"""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception as e:
        # Fallback to simple estimation if tiktoken fails
        print(f"Tiktoken failed: {e}, using fallback estimation")
        return len(text) // 4


def _safe_mlflow_log(func, *args, **kwargs):
    """Safely log to MLflow"""
    if not mlflow_client:
        return
    try:
        func(*args, **kwargs)
    except Exception as e:
        print(f"MLflow log failed: {e}")


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
    session["message_count"] += 1
    
    start_time = time.time()
    accumulated_response = ""

    async def generate():
        nonlocal accumulated_response
        
        try:
            for chunk in chatbot.chat(user_message=request.message, context=context, stream=True, save_history=False):
                accumulated_response += chunk
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
            
            # Log to MLflow after stream completes
            if mlflow_client:
                try:
                    with mlflow.start_run(run_name=f"stream_{request.session_id[:8]}"):
                        mlflow.log_param("session_id", request.session_id)
                        mlflow.log_param("streaming", True)
                        mlflow.log_param("page_title", request.metadata.page_title or "unknown")
                        mlflow.log_param("context_type", request.metadata.context_type or "unknown")
                        
                        input_tokens = _estimate_tokens(request.message + context)
                        output_tokens = _estimate_tokens(accumulated_response)
                        total_time = time.time() - start_time
                        
                        mlflow.log_metric("input_tokens", input_tokens)
                        mlflow.log_metric("output_tokens", output_tokens)
                        mlflow.log_metric("total_tokens", input_tokens + output_tokens)
                        mlflow.log_metric("response_time_seconds", total_time)
                except Exception:
                    pass
        
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
