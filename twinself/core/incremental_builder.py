import os
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime

from langchain_core.documents import Document
from qdrant_client import QdrantClient, models

from .config import config
from .exceptions import DataLoadingError, VectorStoreError
from ..services.embedding_service import EmbeddingService


class IncrementalBuilder:
    """Smart builder that only processes changed files."""
    
    def __init__(self, cache_path: str = "./data/build_cache.json"):
        self.cache_path = Path(cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache: Dict[str, Dict[str, str]] = self._load_cache()
        self.embedding_service = EmbeddingService()
    
    def _load_cache(self) -> Dict[str, Dict[str, str]]:
        """Load file hash cache."""
        if self.cache_path.exists():
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_cache(self):
        """Save file hash cache."""
        with open(self.cache_path, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2)
    
    def _compute_file_hash(self, filepath: str) -> str:
        """Compute SHA256 hash of file content."""
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            hasher.update(f.read())
        return hasher.hexdigest()
    
    def _compute_directory_hash(self, directory: str) -> str:
        """Compute combined hash of all files in directory."""
        hasher = hashlib.sha256()
        for root, _, files in os.walk(directory):
            for file in sorted(files):
                if file.endswith(('.txt', '.md', '.json')):
                    filepath = os.path.join(root, file)
                    hasher.update(self._compute_file_hash(filepath).encode())
        return hasher.hexdigest()
    
    def detect_changes(self, directory: str, data_type: str) -> Tuple[Set[str], Set[str], Set[str]]:
        """
        Detect changed, added, and deleted files.
        
        Returns:
            (added_files, modified_files, deleted_files)
        """
        if not os.path.exists(directory):
            return set(), set(), set()
        
        current_files = {}
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.txt', '.md', '.json')):
                    filepath = os.path.join(root, file)
                    current_files[filepath] = self._compute_file_hash(filepath)
        
        cached_files = self.cache.get(data_type, {})
        
        added = set(current_files.keys()) - set(cached_files.keys())
        deleted = set(cached_files.keys()) - set(current_files.keys())
        modified = {
            f for f in current_files.keys() & cached_files.keys()
            if current_files[f] != cached_files[f]
        }
        
        return added, modified, deleted
    
    def update_cache(self, directory: str, data_type: str):
        """Update cache with current file hashes."""
        current_files = {}
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.txt', '.md', '.json')):
                    filepath = os.path.join(root, file)
                    current_files[filepath] = self._compute_file_hash(filepath)
        
        self.cache[data_type] = current_files
        self._save_cache()
    
    def needs_rebuild(self, directory: str, data_type: str) -> bool:
        """Check if directory needs rebuild."""
        added, modified, deleted = self.detect_changes(directory, data_type)
        return bool(added or modified or deleted)
    
    def get_change_summary(self, directory: str, data_type: str) -> Dict[str, int]:
        """Get summary of changes."""
        added, modified, deleted = self.detect_changes(directory, data_type)
        return {
            'added': len(added),
            'modified': len(modified),
            'deleted': len(deleted),
            'total_changes': len(added) + len(modified) + len(deleted)
        }
    
    def incremental_build_semantic(
        self,
        source_directory: str = None,
        collection_name: str = None,
        force_rebuild: bool = False
    ) -> Dict[str, any]:
        """
        Incrementally build semantic memory.
        Only processes changed files.
        """
        source_dir = source_directory or config.semantic_data_dir
        collection = collection_name or config.semantic_memory_collection
        
        # Check if rebuild needed
        if not force_rebuild and not self.needs_rebuild(source_dir, 'semantic'):
            print("No changes detected in semantic data. Skipping rebuild.")
            return {'status': 'skipped', 'reason': 'no_changes'}
        
        # Get changes
        added, modified, deleted = self.detect_changes(source_dir, 'semantic')
        
        print(f"\nChange Summary:")
        print(f"  Added: {len(added)} files")
        print(f"  Modified: {len(modified)} files")
        print(f"  Deleted: {len(deleted)} files")
        
        from ..build_semantic_memory import build_semantic_memory
        build_semantic_memory(source_dir, collection)
        
        # Update cache
        self.update_cache(source_dir, 'semantic')
        
        return {
            'status': 'rebuilt',
            'changes': {
                'added': len(added),
                'modified': len(modified),
                'deleted': len(deleted)
            }
        }
