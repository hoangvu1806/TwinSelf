"""
TwinSelf MLOps Server
Integrated with MLflow tracking and DeepEval quality monitoring
"""
import os
import sys
import time
import uuid
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import asyncio
from concurrent.futures import ThreadPoolExecutor
import subprocess
import json

# MLflow
import mlflow
from mlflow.tracking import MlflowClient

# DeepEval (optional)
try:
    from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
    from deepeval.test_case import LLMTestCase
    from deepeval.models import DeepEvalBaseLLM
    DEEPEVAL_AVAILABLE = True
except ImportError:
    DEEPEVAL_AVAILABLE = False
    print("DeepEval not installed. Install: pip install deepeval")

from twinself import DigitalTwinChatbot


# Gemini Model for DeepEval
class GeminiEvalModel(DeepEvalBaseLLM):
    """Custom DeepEval model using Google Gemini"""
    def __init__(self):
        from langchain_google_genai import ChatGoogleGenerativeAI
        self.model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY_4DEEPEVAL")
        )
    
    def load_model(self):
        return self.model
    
    def generate(self, prompt: str) -> str:
        response = self.model.invoke(prompt)
        return response.content
    
    async def a_generate(self, prompt: str) -> str:
        response = await self.model.ainvoke(prompt)
        return response.content
    
    def get_model_name(self):
        return "gemini-2.0-flash"


# Global instances
chatbot: Optional[DigitalTwinChatbot] = None
mlflow_client: Optional[MlflowClient] = None
gemini_eval_model: Optional[GeminiEvalModel] = None
metrics_buffer: List[Dict[str, Any]] = []

# Configuration
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
MLFLOW_EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "twinself-production")



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize chatbot and MLflow on startup"""
    global chatbot, mlflow_client, gemini_eval_model
    
    try:
        print("Initializing TwinSelf MLOps Server...")
        
        # Initialize MLflow (non-blocking)
        print(f"Connecting to MLflow: {MLFLOW_TRACKING_URI}")
        try:
            mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
            mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
            mlflow_client = MlflowClient()
            
            # Test connection with timeout
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', 5000))
            sock.close()
            
            if result == 0:
                print("✓ MLflow connected")
                # Log server startup
                with mlflow.start_run(run_name=f"server_startup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
                    mlflow.log_param("server_version", "1.0.0")
                    mlflow.log_param("deepeval_enabled", DEEPEVAL_AVAILABLE)
            else:
                print("MLflow server not available - tracking disabled")
                mlflow_client = None
        except Exception as e:
            print(f"MLflow connection failed: {e} - tracking disabled")
            mlflow_client = None
        
        # Initialize chatbot
        print("Initializing chatbot...")
        chatbot = DigitalTwinChatbot(bot_name=os.getenv("USER_NAME", "Hoàng Vũ"))
        print("✓ Chatbot initialized")
        
        # Initialize Gemini model for DeepEval
        if DEEPEVAL_AVAILABLE:
            try:
                gemini_eval_model = GeminiEvalModel()
                print("✓ Gemini evaluation model initialized")
            except Exception as e:
                print(f"Failed to initialize Gemini eval model: {e}")
                gemini_eval_model = None
        
        print("Server ready!")
        yield
        
    finally:
        print("Shutting down...")
        if metrics_buffer and mlflow_client:
            _flush_metrics_buffer()


# Create FastAPI app
app = FastAPI(
    title="TwinSelf MLOps API",
    description="Production API with MLflow and DeepEval",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models
class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    session_id: str
    message: str
    conversation: List[Message] = []
    track_quality: bool = True  # Default: enable quality tracking


class ChatResponse(BaseModel):
    session_id: str
    response: str
    bot_name: str
    metrics: Optional[Dict[str, Any]] = None


class EditSuggestion(BaseModel):
    original_question: str
    original_response: str
    suggested_response: str


class EditSuggestionResponse(BaseModel):
    status: str
    message: str
    saved_to: str



# Helper functions
def _estimate_tokens(text: str) -> int:
    """Estimate token count (chars / 4 for Vietnamese)"""
    return len(text) // 4


def _safe_mlflow_log(func, *args, **kwargs):
    """Safely log to MLflow if available"""
    if not mlflow_client:
        return
    try:
        func(*args, **kwargs)
    except Exception as e:
        print(f"MLflow log failed: {e}")


def _ensure_mlflow_run_ended():
    """Ensure any active MLflow run is ended before starting a new one"""
    if not mlflow_client:
        return
    try:
        active_run = mlflow.active_run()
        if active_run:
            mlflow.end_run()
    except Exception as e:
        print(f"Failed to end active run: {e}")


def _flush_metrics_buffer():
    """Flush metrics buffer to MLflow"""
    if not metrics_buffer or not mlflow_client:
        return
    
    try:
        with mlflow.start_run(run_name=f"batch_{datetime.now().strftime('%H%M%S')}"):
            total = len(metrics_buffer)
            avg_duration = sum(m["duration"] for m in metrics_buffer) / total
            errors = sum(1 for m in metrics_buffer if m["status_code"] >= 400)
            
            mlflow.log_metric("total_requests", total)
            mlflow.log_metric("avg_duration_seconds", avg_duration)
            mlflow.log_metric("error_count", errors)
            mlflow.log_metric("error_rate", errors / total if total > 0 else 0)
        
        metrics_buffer.clear()
    except Exception as e:
        print(f"Failed to flush metrics: {e}")


def _evaluate_quality(query: str, response: str, context: str) -> Optional[Dict]:
    """Evaluate response quality with DeepEval using Gemini (synchronous)"""
    if not DEEPEVAL_AVAILABLE or not gemini_eval_model:
        return None
    
    try:
        test_case = LLMTestCase(
            input=query,
            actual_output=response,
            retrieval_context=[context] if context else ["No context available"]
        )
        
        metrics = {}
        
        # Answer Relevancy
        try:
            relevancy = AnswerRelevancyMetric(threshold=0.7, model=gemini_eval_model)
            relevancy.measure(test_case)
            metrics["answer_relevancy"] = relevancy.score
            metrics["answer_relevancy_reason"] = getattr(relevancy, 'reason', '')
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                print(f"Relevancy failed: API quota exceeded")
            else:
                print(f"Relevancy failed: {e}")
        
        # Faithfulness
        try:
            faithfulness = FaithfulnessMetric(threshold=0.7, model=gemini_eval_model)
            faithfulness.measure(test_case)
            metrics["faithfulness"] = faithfulness.score
            metrics["faithfulness_reason"] = getattr(faithfulness, 'reason', '')
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                print(f"Faithfulness failed: API quota exceeded")
            else:
                print(f"Faithfulness failed: {e}")
        
        return metrics if metrics else None
        
    except Exception as e:
        print(f"Quality evaluation failed: {e}")
        return None


def _run_evaluation_in_process(query: str, response: str, context: str, run_id: str):
    """
    Run DeepEval evaluation in separate process.
    This completely avoids async/threading conflicts.
    """
    print(f"Starting evaluation in separate process for run {run_id[:8]}")
    
    try:
        # Run evaluation script in separate process with UTF-8 encoding
        result = subprocess.run(
            [
                sys.executable,
                "scripts/run_deepeval_evaluation.py",
                query,
                response,
                context,
                run_id
            ],
            capture_output=True,
            text=True,
            encoding='utf-8',  # Force UTF-8 encoding
            errors='replace',  # Replace invalid characters
            timeout=60  # 60 second timeout
        )
        
        if result.returncode == 0:
            print(f"Evaluation process completed successfully")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"Evaluation process failed with code {result.returncode}")
            if result.stderr:
                print(result.stderr)
    
    except subprocess.TimeoutExpired:
        print(f"Evaluation process timed out after 60 seconds")
    except Exception as e:
        print(f"Failed to run evaluation process: {e}")
        import traceback
        traceback.print_exc()


async def _evaluate_quality_async(query: str, response: str, context: str, run_id: str = None):
    """
    Evaluate quality asynchronously in background using separate process.
    Does not block the main response flow.
    """
    if not run_id:
        print("No run_id provided for evaluation")
        return
    
    try:
        # Run evaluation in thread pool (which spawns separate process)
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            await loop.run_in_executor(
                executor,
                _run_evaluation_in_process,
                query,
                response,
                context,
                run_id
            )
    except Exception as e:
        print(f"Async quality evaluation failed: {e}")
        import traceback
        traceback.print_exc()


def _build_context(conversation: List[Message]) -> str:
    """Build context from conversation history"""
    if not conversation:
        return ""
    
    lines = ["=== Recent Conversation ==="]
    for msg in conversation[-5:]:
        role = "User" if msg.role == "user" else chatbot.bot_name
        lines.append(f"{role}: {msg.content}")
    
    return "\n".join(lines)



# Middleware for request tracking
@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Track all requests"""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    response = await call_next(request)
    duration = time.time() - start_time
    
    metrics_buffer.append({
        "request_id": request_id,
        "path": request.url.path,
        "method": request.method,
        "duration": duration,
        "status_code": response.status_code,
        "timestamp": datetime.now().isoformat()
    })
    
    if len(metrics_buffer) >= 100:
        _flush_metrics_buffer()
    
    return response


# Endpoints
@app.get("/health")
async def health_check():
    """Health check"""
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    return {
        "status": "healthy",
        "bot_name": chatbot.bot_name,
        "mlflow_uri": MLFLOW_TRACKING_URI,
        "mlflow_connected": mlflow_client is not None,
        "deepeval_enabled": DEEPEVAL_AVAILABLE
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """Chat with MLflow tracking and optional DeepEval evaluation"""
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    start_time = time.time()
    
    # Start MLflow run if available
    # End any active run first to avoid conflicts
    _ensure_mlflow_run_ended()
    mlflow_run = mlflow.start_run(run_name=f"chat_{request.session_id[:8]}") if mlflow_client else None
    run_id = mlflow_run.info.run_id if mlflow_run else None
    
    try:
        # Log parameters
        _safe_mlflow_log(mlflow.log_param, "session_id", request.session_id)
        _safe_mlflow_log(mlflow.log_param, "message_length", len(request.message))
        _safe_mlflow_log(mlflow.log_param, "conversation_length", len(request.conversation))
        
        # Estimate tokens
        input_tokens = _estimate_tokens(request.message)
        context_tokens = sum(_estimate_tokens(m.content) for m in request.conversation)
        total_input = input_tokens + context_tokens
        
        _safe_mlflow_log(mlflow.log_metric, "input_tokens", input_tokens)
        _safe_mlflow_log(mlflow.log_metric, "context_tokens", context_tokens)
        _safe_mlflow_log(mlflow.log_metric, "total_input_tokens", total_input)
        
        # Build context and get response
        context = _build_context(request.conversation)
        
        response_start = time.time()
        result = chatbot.chat(
            user_message=request.message,
            context=context,
            stream=False,
            save_history=False,
            return_retrieved_context=request.track_quality  # Only retrieve if quality tracking enabled
        )
        response_time = time.time() - response_start
        
        # Extract response and retrieved docs
        if request.track_quality and isinstance(result, dict):
            response = result["response"]
            retrieved_docs = result["retrieved_docs"]
        else:
            response = result
            retrieved_docs = None
        
        # Log response metrics
        output_tokens = _estimate_tokens(response)
        total_tokens = total_input + output_tokens
        
        _safe_mlflow_log(mlflow.log_metric, "output_tokens", output_tokens)
        _safe_mlflow_log(mlflow.log_metric, "total_tokens", total_tokens)
        _safe_mlflow_log(mlflow.log_metric, "response_time_seconds", response_time)
        
        # Estimate cost (Gemini 2.5 Flash)
        input_cost = total_input * 0.075 / 1_000_000
        output_cost = output_tokens * 0.30 / 1_000_000
        total_cost = input_cost + output_cost
        
        _safe_mlflow_log(mlflow.log_metric, "input_cost_usd", input_cost)
        _safe_mlflow_log(mlflow.log_metric, "output_cost_usd", output_cost)
        _safe_mlflow_log(mlflow.log_metric, "total_cost_usd", total_cost)
        
        # Quality evaluation - Run in background to not block response
        quality_status = "not_requested"
        if request.track_quality and retrieved_docs and DEEPEVAL_AVAILABLE:
            # Combine all retrieved docs into context string for DeepEval
            rag_context = "\n\n".join([
                "=== Semantic Knowledge ===\n" + "\n".join(retrieved_docs.get("semantic", [])),
                "=== Episodic Examples ===\n" + "\n".join(retrieved_docs.get("episodic", [])),
                "=== Procedural Rules ===\n" + "\n".join(retrieved_docs.get("procedural", []))
            ])
            
            # Schedule async evaluation in background
            if run_id:
                background_tasks.add_task(
                    _evaluate_quality_async,
                    request.message,
                    response,
                    rag_context,
                    run_id
                )
                quality_status = "evaluating_in_background"
                print(f"DeepEval evaluation scheduled for run {run_id[:8]}")
        
        # Log total time (without evaluation time)
        total_time = time.time() - start_time
        _safe_mlflow_log(mlflow.log_metric, "total_time_seconds", total_time)
        _safe_mlflow_log(mlflow.log_param, "status", "success")
        _safe_mlflow_log(mlflow.log_param, "quality_evaluation", quality_status)
        
        return ChatResponse(
            session_id=request.session_id,
            response=response,
            bot_name=chatbot.bot_name,
            metrics={
                "response_time": response_time,
                "total_tokens": total_tokens,
                "cost_usd": total_cost,
                "quality_evaluation": quality_status
            }
        )
        
    except Exception as e:
        _safe_mlflow_log(mlflow.log_param, "status", "error")
        _safe_mlflow_log(mlflow.log_param, "error_message", str(e))
        _safe_mlflow_log(mlflow.log_metric, "total_time_seconds", time.time() - start_time)
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")
    
    finally:
        if mlflow_run:
            mlflow.end_run()



@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat with MLflow tracking"""
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    context = _build_context(request.conversation)
    
    # Track metrics (will be logged after stream completes)
    start_time = time.time()
    accumulated_response = ""
    
    async def generate():
        nonlocal accumulated_response
        
        try:
            for chunk in chatbot.chat(
                user_message=request.message,
                context=context,
                stream=True,
                save_history=False
            ):
                accumulated_response += chunk
                yield f"data: {chunk}\n\n"
            
            yield "data: [DONE]\n\n"
            
            # Log to MLflow after stream completes
            if mlflow_client:
                try:
                    # End any active run first
                    _ensure_mlflow_run_ended()
                    
                    with mlflow.start_run(run_name=f"stream_{request.session_id[:8]}"):
                        mlflow.log_param("session_id", request.session_id)
                        mlflow.log_param("streaming", True)
                        
                        input_tokens = _estimate_tokens(request.message)
                        output_tokens = _estimate_tokens(accumulated_response)
                        total_tokens = input_tokens + output_tokens
                        
                        mlflow.log_metric("input_tokens", input_tokens)
                        mlflow.log_metric("output_tokens", output_tokens)
                        mlflow.log_metric("total_tokens", total_tokens)
                        
                        duration = time.time() - start_time
                        mlflow.log_metric("stream_duration_seconds", duration)
                        
                        cost = (input_tokens * 0.075 + output_tokens * 0.30) / 1_000_000
                        mlflow.log_metric("total_cost_usd", cost)
                        
                        mlflow.log_param("status", "success")
                except Exception as e:
                    print(f"Failed to log stream metrics: {e}")
                
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"
            
            # Log error
            if mlflow_client:
                try:
                    with mlflow.start_run(run_name=f"stream_error_{request.session_id[:8]}"):
                        mlflow.log_param("status", "error")
                        mlflow.log_param("error_message", str(e))
                except:
                    pass
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.post("/api/edit-message/suggestion", response_model=EditSuggestionResponse)
async def save_edit_suggestion(suggestion: EditSuggestion):
    """
    Save user's suggested response edit to episodic data.
    This helps improve the chatbot by learning from user corrections.
    """
    import json
    from pathlib import Path
    
    try:
        # Define file path
        episodic_dir = Path("episodic_data")
        episodic_dir.mkdir(exist_ok=True)
        suggestions_file = episodic_dir / "user_suggestions.json"
        
        # Create new entry - only user_query and your_response
        new_entry = {
            "user_query": suggestion.original_question,
            "your_response": suggestion.suggested_response
        }
        
        # Load existing data or create new list
        if suggestions_file.exists():
            with open(suggestions_file, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if not isinstance(data, list):
                        data = []
                except json.JSONDecodeError:
                    data = []
        else:
            data = []
        
        # Append new entry
        data.append(new_entry)
        
        # Save back to file
        with open(suggestions_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Log to MLflow if available
        _safe_mlflow_log(
            mlflow.log_metric,
            "user_suggestions_count",
            len(data)
        )
        
        return EditSuggestionResponse(
            status="success",
            message=f"Suggestion saved successfully. Total suggestions: {len(data)}",
            saved_to=str(suggestions_file)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save suggestion: {str(e)}"
        )


@app.get("/")
async def root():
    """API information"""
    return {
        "name": "TwinSelf MLOps API",
        "version": "1.0.0",
        "features": [
            "MLflow experiment tracking",
            "DeepEval quality evaluation" if DEEPEVAL_AVAILABLE else "DeepEval not available",
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


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print(f"Starting TwinSelf MLOps API on {host}:{port}")
    print(f"MLflow UI: {MLFLOW_TRACKING_URI}")
    print(f"API docs: http://{host}:{port}/docs")
    
    uvicorn.run(
        "mlops_server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
