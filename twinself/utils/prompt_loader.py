"""
System Prompt Loader Utility
Load system prompts from versioned data
"""
from pathlib import Path
from typing import Optional
from ..core.config import config
from ..core.version_manager import VersionManager


class PromptLoader:
    """Load and manage system prompts from versioning system."""
    
    def __init__(self):
        self.version_manager = VersionManager()
        self.prompts_dir = Path(config.system_prompts_dir)
        self._cache = {}
    
    def get_active_prompt(self) -> str:
        """
        Get the system prompt from active version.
        Falls back to default_prompt.md if not found.
        """
        # Try to get from active version
        active_version = self.version_manager.get_active_version()
        
        if active_version and active_version.system_prompt_file:
            prompt_path = Path(active_version.system_prompt_file)
            if prompt_path.exists():
                return self._load_prompt(prompt_path)
        
        # Fallback to default
        return self.get_prompt("default_prompt.md")
    
    def get_prompt(self, filename: str) -> str:
        """
        Load a specific prompt by filename.
        
        Args:
            filename: Name of the prompt file (e.g., 'default_prompt.md')
            
        Returns:
            Content of the prompt file
        """
        # Check cache
        if filename in self._cache:
            return self._cache[filename]
        
        prompt_path = self.prompts_dir / filename
        
        if not prompt_path.exists():
            raise FileNotFoundError(f"System prompt not found: {filename}")
        
        content = self._load_prompt(prompt_path)
        self._cache[filename] = content
        return content
    
    def _load_prompt(self, path: Path) -> str:
        """Load prompt content from file."""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def list_available_prompts(self) -> list[str]:
        """List all available prompt files."""
        if not self.prompts_dir.exists():
            return []
        
        return [f.name for f in self.prompts_dir.glob('*.md')]
    
    def clear_cache(self):
        """Clear the prompt cache."""
        self._cache.clear()
    
    def reload_prompt(self, filename: str) -> str:
        """
        Reload a prompt, bypassing cache.
        
        Args:
            filename: Name of the prompt file
            
        Returns:
            Fresh content of the prompt file
        """
        if filename in self._cache:
            del self._cache[filename]
        return self.get_prompt(filename)


# Global instance
_prompt_loader = None


def get_prompt_loader() -> PromptLoader:
    """Get or create global PromptLoader instance."""
    global _prompt_loader
    if _prompt_loader is None:
        _prompt_loader = PromptLoader()
    return _prompt_loader


def load_system_prompt(filename: Optional[str] = None) -> str:
    """
    Convenience function to load system prompt.
    
    Args:
        filename: Optional specific prompt file. If None, loads active prompt.
        
    Returns:
        System prompt content
    """
    loader = get_prompt_loader()
    
    if filename:
        return loader.get_prompt(filename)
    else:
        return loader.get_active_prompt()
