import sys
import os
import json
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import mlflow
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.test_case import LLMTestCase
from deepeval.models import DeepEvalBaseLLM
from langchain_google_genai import ChatGoogleGenerativeAI


class GeminiEvalModel(DeepEvalBaseLLM):
    """Custom DeepEval model using Google Gemini"""
    def __init__(self):
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
        """Async generate - required by DeepEvalBaseLLM"""
        response = await self.model.ainvoke(prompt)
        return response.content
    
    def get_model_name(self) -> str:
        """Get model name - required by DeepEvalBaseLLM"""
        return "gemini-2.0-flash"


def evaluate_quality(query: str, response: str, context: str, run_id: str):
    """Evaluate response quality with DeepEval"""
    print(f"Starting evaluation for run {run_id[:8]}")
    
    try:
        # Initialize model
        eval_model = GeminiEvalModel()
        
        # Create test case
        test_case = LLMTestCase(
            input=query,
            actual_output=response,
            retrieval_context=[context] if context else ["No context available"]
        )
        
        metrics = {}
        
        # Answer Relevancy
        try:
            print("Evaluating answer relevancy...")
            relevancy = AnswerRelevancyMetric(threshold=0.7, model=eval_model)
            relevancy.measure(test_case)
            metrics["answer_relevancy"] = relevancy.score
            print(f"Answer Relevancy: {relevancy.score:.2f}")
        except Exception as e:
            print(f"Relevancy failed: {e}")
        
        # Faithfulness
        try:
            print("Evaluating faithfulness...")
            faithfulness = FaithfulnessMetric(threshold=0.7, model=eval_model)
            faithfulness.measure(test_case)
            metrics["faithfulness"] = faithfulness.score
            print(f"Faithfulness: {faithfulness.score:.2f}")
        except Exception as e:
            print(f"Faithfulness failed: {e}")
        
        # Log to MLflow
        if metrics:
            print(f"Logging to MLflow run {run_id[:8]}...")
            mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
            mlflow.set_tracking_uri(mlflow_uri)
            
            with mlflow.start_run(run_id=run_id):
                for key, value in metrics.items():
                    mlflow.log_metric(f"deepeval_{key}", value)
                    print(f"  Logged: deepeval_{key} = {value}")
            
            print(f"Evaluation complete: {len(metrics)} metrics logged")
            return metrics
        else:
            print("No metrics to log")
            return None
    
    except Exception as e:
        print(f"Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python run_deepeval_evaluation.py <query> <response> <context> <run_id>")
        sys.exit(1)
    
    query = sys.argv[1]
    response = sys.argv[2]
    context = sys.argv[3]
    run_id = sys.argv[4]
    
    result = evaluate_quality(query, response, context, run_id)
    
    if result:
        print(json.dumps(result, indent=2))
        sys.exit(0)
    else:
        sys.exit(1)
