"""
Core module for TwinSelf.
Contains configuration, exceptions, version management, and incremental building.
"""

from .config import config, Config
from .exceptions import (
    TwinSelfError,
    ConfigurationError,
    EmbeddingError,
    VectorStoreError,
    MemoryError,
    ChatbotError,
    DataLoadingError
)
from .version_manager import VersionManager, MemoryVersion
from .incremental_builder import IncrementalBuilder

__all__ = [
    "config",
    "Config",
    "TwinSelfError",
    "ConfigurationError",
    "EmbeddingError",
    "VectorStoreError",
    "MemoryError",
    "ChatbotError",
    "DataLoadingError",
    "VersionManager",
    "MemoryVersion",
    "IncrementalBuilder"
]
