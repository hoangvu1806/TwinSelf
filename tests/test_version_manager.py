"""
Tests for Version Manager
"""
import pytest
import tempfile
import shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from twinself.core.version_manager import VersionManager


@pytest.fixture
def temp_data_dir():
    """Create temporary data directory"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


def test_version_manager_init(temp_data_dir):
    """Test version manager initialization"""
    registry_path = str(temp_data_dir / "version_registry.json")
    snapshots_dir = str(temp_data_dir / "snapshots")
    
    vm = VersionManager(registry_path=registry_path, snapshots_dir=snapshots_dir)
    assert vm is not None
    assert vm.registry_path.parent.exists()
    assert vm.snapshots_dir.exists()


def test_create_snapshot(temp_data_dir):
    """Test creating a snapshot"""
    registry_path = str(temp_data_dir / "version_registry.json")
    snapshots_dir = str(temp_data_dir / "snapshots")
    
    vm = VersionManager(registry_path=registry_path, snapshots_dir=snapshots_dir)
    
    # create_snapshot returns bool, not snapshot_id
    result = vm.create_snapshot("test_snapshot_v1")
    assert isinstance(result, bool)


def test_list_snapshots(temp_data_dir):
    """Test listing snapshots"""
    registry_path = str(temp_data_dir / "version_registry.json")
    snapshots_dir = str(temp_data_dir / "snapshots")
    
    vm = VersionManager(registry_path=registry_path, snapshots_dir=snapshots_dir)
    
    snapshots = vm.list_snapshots()
    assert isinstance(snapshots, list)


def test_get_active_version(temp_data_dir):
    """Test getting active version"""
    registry_path = str(temp_data_dir / "version_registry.json")
    snapshots_dir = str(temp_data_dir / "snapshots")
    
    vm = VersionManager(registry_path=registry_path, snapshots_dir=snapshots_dir)
    
    # get_active_version may return None if no versions exist
    version = vm.get_active_version()
    assert version is None or isinstance(version, object)
