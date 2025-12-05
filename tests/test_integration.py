"""
Integration tests - Test with real services
Run manually before deployment: pytest tests/test_integration.py -v
Requires: MLflow server running on localhost:5000
"""
import pytest
import requests
import time

pytestmark = pytest.mark.integration


BASE_URL = "http://localhost:8001"


@pytest.fixture(scope="module")
def check_services():
    """Check if required services are running"""
    # Check MLflow
    try:
        response = requests.get("http://localhost:5000/health", timeout=2)
        assert response.status_code == 200, "MLflow not running"
    except:
        pytest.skip("MLflow server not running on localhost:5000")
    
    # Check MLOps server
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 503:
            pytest.skip("MLOps server not ready (chatbot initializing)")
    except:
        pytest.skip("MLOps server not running on localhost:8001")
    
    # Wait for chatbot to be ready
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                break
            time.sleep(1)
        except:
            time.sleep(1)
    
    yield


def test_integration_health(check_services):
    """Test health endpoint with real server"""
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "bot_name" in data
    print(f"✓ Bot name: {data['bot_name']}")


def test_integration_chat(check_services):
    """Test chat with real chatbot"""
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "session_id": "integration-test",
            "message": "Hello, who are you?"
        },
        timeout=30
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert len(data["response"]) > 0
    print(f"✓ Chat response: {data['response'][:100]}...")


def test_integration_chat_with_context(check_services):
    """Test chat with conversation history"""
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "session_id": "integration-test",
            "message": "What did I just ask?",
            "conversation": [
                {"role": "user", "content": "Hello, who are you?"},
                {"role": "assistant", "content": "I am a digital twin chatbot."}
            ]
        },
        timeout=30
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    print(f"✓ Context-aware response: {data['response'][:100]}...")


def test_integration_feedback(check_services):
    """Test feedback endpoint"""
    response = requests.post(
        f"{BASE_URL}/api/edit-message/suggestion",
        json={
            "original_question": "Integration test question",
            "original_response": "Integration test response",
            "suggested_response": "Better integration response"
        },
        timeout=10
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    print("✓ Feedback saved successfully")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("INTEGRATION TESTS - Requires running services:")
    print("1. Start MLflow: mlflow server --host 127.0.0.1 --port 5000")
    print("2. Start MLOps: python mlops_server.py")
    print("3. Run tests: pytest tests/test_integration.py -v")
    print("="*60 + "\n")
