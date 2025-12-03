"""
TwinSelf - Personal Memory Framework

A configurable framework for building personalized AI memory systems.
Create digital twins with semantic, episodic, and procedural memories 
using AI embeddings and vector databases.
"""

from .chatbot import DigitalTwinChatbot
from .build_semantic_memory import build_semantic_memory
from .build_episodic_memory import build_episodic_memory
from .build_procedural_memory import build_procedural_memory
from .core.config import config
from .services.embedding_service import EmbeddingService

__version__ = "1.0.0"
__author__ = "TwinSelf Contributors"

__all__ = [
    "DigitalTwinChatbot",
    "build_semantic_memory",
    "build_episodic_memory", 
    "build_procedural_memory",
    "config",
    "EmbeddingService"
]