"""
Tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def client():
    """Test client with mocked chatbot and MLflow"""
    with patch('mlops_server.DigitalTwinChatbot') as mock_chatbot_class, \
         patch('mlops_server.MlflowClient') as mock_mlflow_client, \
         patch('mlops_server.GeminiEvalModel') as mock_gemini:
        
        # Mock chatbot instance
        chatbot_instance = Mock()
        chatbot_instance.bot_name = "Test Bot"
        chatbot_instance.chat.return_value = "Test response"
        mock_chatbot_class.return_value = chatbot_instance
        
        # Mock MLflow client
        mock_mlflow_client.return_value = Mock()
        
        # Mock Gemini model
        mock_gemini.return_value = Mock()
        
        # Import app after patching
        from mlops_server import app
        
        with TestClient(app) as test_client:
            yield test_client


def test_health(client):
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "bot_name" in data


def test_root(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "name" in data


def test_chat(client):
    """Test chat endpoint"""
    response = client.post(
        "/chat",
        json={
            "session_id": "test",
            "message": "Hello"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "session_id" in data


def test_chat_empty_message(client):
    """Test chat with empty message"""
    response = client.post(
        "/chat",
        json={
            "session_id": "test",
            "message": ""
        }
    )
    
    assert response.status_code == 400


def test_chat_with_history(client):
    """Test chat with conversation history"""
    response = client.post(
        "/chat",
        json={
            "session_id": "test",
            "message": "Tell me more",
            "conversation": [
                {"role": "user", "content": "What are your skills?"},
                {"role": "assistant", "content": "I am proficient in Python."}
            ]
        }
    )
    
    assert response.status_code == 200


def test_feedback(client):
    """Test feedback endpoint"""
    response = client.post(
        "/api/edit-message/suggestion",
        json={
            "original_question": "Test question",
            "original_response": "Test response",
            "suggested_response": "Better response"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


@pytest.mark.skip(reason="MLops server doesn't have sessions endpoint")
def test_sessions_list(client):
    """Test sessions list endpoint"""
    response = client.get("/api/sessions")
    assert response.status_code == 200
    
    data = response.json()
    assert "sessions" in data
