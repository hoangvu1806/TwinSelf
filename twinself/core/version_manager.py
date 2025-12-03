import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from qdrant_client import QdrantClient, models

from .config import config


@dataclass
class MemoryVersion:
    """Represents a version of memory collections."""
    version_id: str
    timestamp: str
    collections: Dict[str, int]  
    data_hash: Dict[str, str] 
    metadata: Dict[str, Any]
    is_active: bool = False
    system_prompt_file: Optional[str] = None  


class VersionManager:
    """Manages versioning for TwinSelf memory collections."""
    
    def __init__(
        self, 
        registry_path: str = "./data/version_registry.json",
        snapshots_dir: str = "./data/snapshots"
    ):
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.snapshots_dir = Path(snapshots_dir)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.versions: List[MemoryVersion] = []
        self._load_registry()
    
    def _load_registry(self):
        """Load version registry from disk."""
        if self.registry_path.exists():
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.versions = [MemoryVersion(**v) for v in data.get('versions', [])]
    
    def _save_registry(self):
        """Save version registry to disk."""
        data = {'versions': [asdict(v) for v in self.versions]}
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def create_version(
        self,
        collections: Dict[str, int],
        data_hash: Dict[str, str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new version snapshot."""
        version_id = f"v{len(self.versions) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        version = MemoryVersion(
            version_id=version_id,
            timestamp=datetime.now().isoformat(),
            collections=collections,
            data_hash=data_hash,
            metadata=metadata or {},
            is_active=True
        )
        
        for v in self.versions:
            v.is_active = False
        
        self.versions.append(version)
        self._save_registry()
        
        print(f"Created version: {version_id}")
        return version_id
    
    def get_active_version(self) -> Optional[MemoryVersion]:
        for v in reversed(self.versions):
            if v.is_active:
                return v
        return None
    
    def list_versions(self) -> List[MemoryVersion]:
        return self.versions
    
    def rollback_to_version(self, version_id: str) -> bool:
        target_version = None
        for v in self.versions:
            if v.version_id == version_id:
                target_version = v
                break
        
        if not target_version:
            print(f"Version {version_id} not found")
            return False
        
        for v in self.versions:
            v.is_active = False
        
        target_version.is_active = True
        self._save_registry()
        
        print(f"Rolled back to version: {version_id}")
        return True
    
    def get_version_diff(self, version_id1: str, version_id2: str) -> Dict[str, Any]:
        v1 = next((v for v in self.versions if v.version_id == version_id1), None)
        v2 = next((v for v in self.versions if v.version_id == version_id2), None)
        
        if not v1 or not v2:
            return {}
        
        diff = {
            'collection_changes': {},
            'data_hash_changes': {}
        }

        for coll_name in set(list(v1.collections.keys()) + list(v2.collections.keys())):
            count1 = v1.collections.get(coll_name, 0)
            count2 = v2.collections.get(coll_name, 0)
            if count1 != count2:
                diff['collection_changes'][coll_name] = {
                    'before': count1,
                    'after': count2,
                    'delta': count2 - count1
                }
        
        for data_type in set(list(v1.data_hash.keys()) + list(v2.data_hash.keys())):
            hash1 = v1.data_hash.get(data_type, '')
            hash2 = v2.data_hash.get(data_type, '')
            if hash1 != hash2:
                diff['data_hash_changes'][data_type] = {
                    'changed': True,
                    'before': hash1[:8],
                    'after': hash2[:8]
                }
        
        return diff

    
    def create_snapshot(self, version_id: str, system_prompt_file: Optional[str] = None) -> bool:
        try:
            snapshot_path = self.snapshots_dir / version_id
            qdrant_path = Path(config.qdrant_local_path)
            
            if not qdrant_path.exists():
                print(f"Qdrant path does not exist: {qdrant_path}")
                return False
            
            if snapshot_path.exists():
                shutil.rmtree(snapshot_path)
            
            def ignore_lock_files(directory, files):
                """Ignore lock files and temporary files during copy."""
                return [f for f in files if f.endswith(('.lock', '.tmp', '.temp'))]
            
            shutil.copytree(qdrant_path, snapshot_path, ignore=ignore_lock_files)
            
            # Copy system prompt if provided
            if system_prompt_file:
                prompt_source = Path(system_prompt_file)
                if prompt_source.exists():
                    prompt_dest = snapshot_path / "system_prompt.md"
                    shutil.copy2(prompt_source, prompt_dest)
                    print(f"System prompt backed up: {system_prompt_file}")
            
            print(f"Snapshot created: {snapshot_path}")
            return True
            
        except Exception as e:
            print(f"Failed to create snapshot: {e}")
            return False
    
    def restore_snapshot(self, version_id: str, restore_system_prompt: bool = True) -> bool:
        try:
            snapshot_path = self.snapshots_dir / version_id
            qdrant_path = Path(config.qdrant_local_path)
            
            if not snapshot_path.exists():
                print(f"Snapshot not found: {snapshot_path}")
                return False

            backup_path = qdrant_path.parent / f"qdrant_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if qdrant_path.exists():
                shutil.copytree(qdrant_path, backup_path)
                print(f"Current state backed up to: {backup_path}")
            
            if qdrant_path.exists():
                shutil.rmtree(qdrant_path)

            shutil.copytree(snapshot_path, qdrant_path, 
                          ignore=shutil.ignore_patterns('system_prompt.md'))

            if restore_system_prompt:
                prompt_source = snapshot_path / "system_prompt.md"
                if prompt_source.exists():
                    version = next((v for v in self.versions if v.version_id == version_id), None)
                    if version and version.system_prompt_file:
                        prompt_dest = Path(version.system_prompt_file)
                        prompt_dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(prompt_source, prompt_dest)
                        print(f"System prompt restored to: {prompt_dest}")
            
            print(f"Restored from snapshot: {version_id}")
            return True
            
        except Exception as e:
            print(f"Failed to restore snapshot: {e}")
            return False
    
    def rollback_to_version(self, version_id: str, restore_data: bool = True) -> bool:
        """
        Rollback to a specific version.
        
        Args:
            version_id: Version to rollback to
            restore_data: If True, restores actual Qdrant data from snapshot
        """
        target_version = None
        for v in self.versions:
            if v.version_id == version_id:
                target_version = v
                break
        
        if not target_version:
            print(f"Version {version_id} not found")
            return False
        
        # Restore data if requested
        if restore_data:
            if not self.restore_snapshot(version_id):
                print(f"Failed to restore data, but updating active version pointer")
        
        # Deactivate all versions
        for v in self.versions:
            v.is_active = False
        
        # Activate target version
        target_version.is_active = True
        self._save_registry()
        
        print(f"Rolled back to version: {version_id}")
        return True
    
    def list_snapshots(self) -> List[str]:
        """List all available snapshots."""
        if not self.snapshots_dir.exists():
            return []
        return [d.name for d in self.snapshots_dir.iterdir() if d.is_dir()]
    
    def delete_snapshot(self, version_id: str) -> bool:
        """Delete a snapshot to free up space."""
        try:
            snapshot_path = self.snapshots_dir / version_id
            if snapshot_path.exists():
                shutil.rmtree(snapshot_path)
                print(f"Deleted snapshot: {version_id}")
                return True
            else:
                print(f"Snapshot not found: {version_id}")
                return False
        except Exception as e:
            print(f"Failed to delete snapshot: {e}")
            return False
    
    def get_snapshot_size(self, version_id: str) -> int:
        """Get size of a snapshot in bytes."""
        snapshot_path = self.snapshots_dir / version_id
        if not snapshot_path.exists():
            return 0
        
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(snapshot_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        return total_size
    
    def cleanup_old_snapshots(self, keep_last: int = 5) -> int:
        """
        Delete old snapshots, keeping only the most recent ones.
        
        Args:
            keep_last: Number of recent snapshots to keep
            
        Returns:
            Number of snapshots deleted
        """
        snapshots = self.list_snapshots()
        if len(snapshots) <= keep_last:
            return 0
        
        # Sort by creation time (version_id contains timestamp)
        snapshots.sort(reverse=True)
        
        deleted = 0
        for snapshot in snapshots[keep_last:]:
            if self.delete_snapshot(snapshot):
                deleted += 1
        
        print(f"Cleaned up {deleted} old snapshots")
        return deleted
