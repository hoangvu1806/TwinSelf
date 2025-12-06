"""
Tests for TwinSelf chatbot core functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="module")
def mock_all():
    """Mock all heavy dependencies"""
    with patch('twinself.chatbot.ChatGoogleGenerativeAI') as mock_llm, \
         patch('twinself.chatbot.QdrantClient') as mock_client, \
         patch('twinself.chatbot.Qdrant') as mock_store, \
         patch('twinself.chatbot.EmbeddingService') as mock_embedding:
        
        # Mock LLM
        llm = Mock()
        response = Mock()
        response.content = "Test response"
        llm.invoke.return_value = response
        llm.stream.return_value = iter(["Test ", "response"])
        mock_llm.return_value = llm
        
        # Mock Qdrant
        client = Mock()
        mock_client.return_value = client
        
        store = Mock()
        store.similarity_search.return_value = [
            Mock(page_content="Test context", metadata={})
        ]
        mock_store.return_value = store
        
        # Mock embedding service
        service = Mock()
        service._embeddings = Mock()
        mock_embedding.return_value = service
        
        yield


def test_chatbot_initialization(mock_all):
    """Test chatbot can be initialized"""
    from twinself import DigitalTwinChatbot
    
    chatbot = DigitalTwinChatbot(bot_name="Test Bot")
    assert chatbot is not None
    assert chatbot.bot_name == "Test Bot"


def test_chatbot_chat_non_stream(mock_all):
    """Test chatbot non-streaming response"""
    from twinself import DigitalTwinChatbot
    
    chatbot = DigitalTwinChatbot()
    response = chatbot.chat("Hello", stream=False)
    
    assert response is not None
    assert isinstance(response, str)


def test_chatbot_with_context(mock_all):
    """Test chatbot with conversation context"""
    from twinself import DigitalTwinChatbot
    
    chatbot = DigitalTwinChatbot()
    context = "Previous conversation context"
    response = chatbot.chat("Tell me more", context=context, stream=False)
    
    assert response is not None
