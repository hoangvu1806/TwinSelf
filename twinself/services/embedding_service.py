from typing import List, Optional

from langchain_huggingface import HuggingFaceEmbeddings

from ..core.config import config
from ..core.exceptions import EmbeddingError


class EmbeddingService:
    """Service for managing text embeddings using HuggingFace models."""
    
    def __init__(self, model_name: Optional[str] = None, cache_folder: Optional[str] = None):
        """
        Initialize embedding service.
        
        Args:
            model_name: Name of the embedding model to use. If None, uses config default.
            cache_folder: Folder to cache models. If None, uses config default.
        """
        self._model_name = model_name or config.embedding_model_name
        self._cache_folder = cache_folder or config.model_cache_folder
        
        self._embeddings = HuggingFaceEmbeddings(
            model_name=self._model_name,
            model_kwargs={"trust_remote_code": True},
            cache_folder=self._cache_folder
        )
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query text."""
        if not text or not text.strip():
            raise EmbeddingError("Text cannot be empty")
        try:
            return self._embeddings.embed_query(text.strip())
        except Exception as e:
            raise EmbeddingError(f"Failed to embed query: {e}") from e
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents."""
        if not texts:
            return []
            
        # Filter out empty texts
        valid_texts = [text.strip() for text in texts if text and text.strip()]
        if not valid_texts:
            raise EmbeddingError("No valid texts to embed")
            
        try:
            return self._embeddings.embed_documents(valid_texts)
        except Exception as e:
            raise EmbeddingError(f"Failed to embed documents: {e}") from e
    
    def get_embedding_size(self) -> int:
        """Get the size of embeddings."""
        try:
            dummy_embedding = self.embed_query("sample text")
            return len(dummy_embedding)
        except EmbeddingError:
            return 768  # Default size for most models
    
    @property
    def model_name(self) -> str:
        """Get the current model name."""
        return self._model_name