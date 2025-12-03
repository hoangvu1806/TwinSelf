"""
Tests for TwinSelf chatbot
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_chatbot_initialization():
    """Test chatbot can be initialized"""
    from twinself import DigitalTwinChatbot
    
    chatbot = DigitalTwinChatbot()
    assert chatbot is not None
    assert chatbot.bot_name is not None


def test_chatbot_chat():
    """Test chatbot can respond"""
    from twinself import DigitalTwinChatbot
    
    chatbot = DigitalTwinChatbot()
    response = chatbot.chat("Hello", stream=False)
    
    assert response is not None
    assert len(response) > 0


def test_chatbot_with_context():
    """Test chatbot with conversation context"""
    from twinself import DigitalTwinChatbot
    
    chatbot = DigitalTwinChatbot()
    
    context = "User: What are your skills?\nAssistant: I am proficient in Python."
    response = chatbot.chat("Tell me more", context=context, stream=False)
    
    assert response is not None


if __name__ == "__main__":
    test_chatbot_initialization()
    print("test_chatbot_initialization passed")
    
    test_chatbot_chat()
    print("test_chatbot_chat passed")
    
    test_chatbot_with_context()
    print("test_chatbot_with_context passed")
    
    print("\nAll tests passed!")
