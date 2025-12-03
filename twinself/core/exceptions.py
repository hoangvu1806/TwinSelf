
class TwinSelfError(Exception):
    """Base exception for TwinSelf application."""
    pass


class ConfigurationError(TwinSelfError):
    """Raised when configuration is invalid or missing."""
    pass


class EmbeddingError(TwinSelfError):
    """Raised when embedding operations fail."""
    pass


class VectorStoreError(TwinSelfError):
    """Raised when vector store operations fail."""
    pass


class MemoryError(TwinSelfError):
    """Raised when memory operations fail."""
    pass


class ChatbotError(TwinSelfError):
    """Raised when chatbot operations fail."""
    pass


class DataLoadingError(TwinSelfError):
    """Raised when data loading operations fail."""
    pass