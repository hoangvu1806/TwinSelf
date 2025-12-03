import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    _instance: Optional['Config'] = None
    
    def __new__(cls) -> 'Config':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self._validate_environment()
    
    # API Keys
    @property
    def google_api_key(self) -> str:
        return self._get_required_env("GOOGLE_API_KEY")
    
    @property
    def qdrant_local_path(self) -> str:
        return os.getenv("QDRANT_LOCAL_PATH", "./data/qdrant/twinself")
    
    # Model Configuration
    @property
    def chat_llm_model(self) -> str:
        return os.getenv("CHAT_LLM_MODEL", "gemini-2.5-flash-lite")
    
    @property
    def embedding_model_name(self) -> str:
        return os.getenv("EMBEDDING_MODEL_NAME", "dangvantuan/vietnamese-document-embedding")
    
    @property
    def model_cache_folder(self) -> str:
        return os.getenv("MODEL_CACHE_FOLDER", "./models")
    
    # Collection Names - configurable with user prefix
    @property
    def user_prefix(self) -> str:
        return os.getenv("USER_PREFIX", "user")
    
    @property
    def semantic_memory_collection(self) -> str:
        return f"{self.user_prefix}_semantic_memory_hg"
    
    @property
    def episodic_memory_collection(self) -> str:
        return f"{self.user_prefix}_episodic_memory_hg"
    
    @property
    def procedural_memory_collection(self) -> str:
        return f"{self.user_prefix}_procedural_memory_hg"
    
    # Retrieval Settings
    @property
    def top_k_semantic(self) -> int:
        return 7
    
    @property
    def top_k_episodic(self) -> int:
        return 5

    @property
    def top_k_procedural(self) -> int:
        return 10
    
    # Directory Paths
    @property
    def semantic_data_dir(self) -> str:
        return "semantic_data"
    
    @property
    def episodic_data_dir(self) -> str:
        return "episodic_data"
    
    @property
    def procedural_data_dir(self) -> str:
        return "procedural_data"
    
    @property
    def system_prompts_dir(self) -> str:
        return "system_prompts"
    
    # Text Processing
    @property
    def chunk_size(self) -> int:
        return 1000
    
    @property
    def chunk_overlap(self) -> int:
        return 200
    
    @property
    def batch_size(self) -> int:
        return 5
    
    @property
    def qdrant_timeout(self) -> int:
        return 60
    
    def _get_required_env(self, key: str) -> str:
        """Get required environment variable or raise error."""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"{key} environment variable not set")
        return value
    
    def _validate_environment(self) -> None:
        """Validate all required environment variables are set."""
        required_vars = [
            "GOOGLE_API_KEY"
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")


# Global config instance
config = Config()