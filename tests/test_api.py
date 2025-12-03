"""
Tests for API endpoints
"""
import requests


BASE_URL = "http://localhost:8001"


def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "bot_name" in data


def test_chat():
    """Test chat endpoint"""
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "session_id": "test",
            "message": "Hello"
        },
        timeout=30
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert "response" in data
    assert "session_id" in data
    assert len(data["response"]) > 0


def test_chat_with_history():
    """Test chat with conversation history"""
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "session_id": "test",
            "message": "Tell me more",
            "conversation": [
                {"role": "user", "content": "What are your skills?"},
                {"role": "assistant", "content": "I am proficient in Python."}
            ]
        },
        timeout=30
    )
    
    assert response.status_code == 200


def test_feedback():
    """Test feedback endpoint"""
    response = requests.post(
        f"{BASE_URL}/api/edit-message/suggestion",
        json={
            "original_question": "Test question",
            "original_response": "Test response",
            "suggested_response": "Better response"
        },
        timeout=10
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"


def test_root():
    """Test root endpoint"""
    response = requests.get(f"{BASE_URL}/", timeout=5)
    assert response.status_code == 200
    
    data = response.json()
    assert "name" in data
    assert "endpoints" in data


if __name__ == "__main__":
    print("Testing API endpoints...")
    print("Make sure server is running: python mlops_server.py")
    print()
    
    try:
        test_health()
        print("test_health passed")
        
        test_root()
        print("test_root passed")
        
        test_chat()
        print("test_chat passed")
        
        test_chat_with_history()
        print("test_chat_with_history passed")
        
        test_feedback()
        print("test_feedback passed")
        
        print("\nAll tests passed!")
    except requests.exceptions.ConnectionError:
        print("Error: Server not running. Start with: python mlops_server.py")
    except AssertionError as e:
        print(f"Test failed: {e}")
