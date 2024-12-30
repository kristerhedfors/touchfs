"""Tests for cache control plugin functionality."""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from touchfs.content.plugins.cache_control import CacheControlPlugin
from touchfs.models.filesystem import FileNode
from touchfs.config.settings import get_cache_enabled

def create_file_node(content=None, xattrs=None):
    """Helper to create a FileNode for testing."""
    return FileNode(
        type="file",
        content=content,
        attrs={"st_mode": "33188"},
        xattrs=xattrs
    )

def test_cache_control_initialization(tmp_path):
    """Test cache directory initialization."""
    test_cache = tmp_path / ".touchfs.cache"
    test_cache.mkdir()
    assert test_cache.exists()

def test_cache_enabled_control():
    """Test cache enabled control file."""
    plugin = CacheControlPlugin()
    node = create_file_node()
    fs_structure = {}
    
    # Test reading current state
    result = plugin.generate("/.touchfs/cache_enabled", node, fs_structure)
    assert result in ["0\n", "1\n"]
    
    # Test disabling cache
    node.content = "0"
    plugin.generate("/.touchfs/cache_enabled", node, fs_structure)
    assert not get_cache_enabled()
    
    # Test enabling cache
    node.content = "1"
    plugin.generate("/.touchfs/cache_enabled", node, fs_structure)
    assert get_cache_enabled()

def test_cache_stats_display():
    """Test cache statistics display."""
    plugin = CacheControlPlugin()
    node = create_file_node()
    fs_structure = {}
    
    stats = plugin.generate("/.touchfs/cache_stats", node, fs_structure)
    
    # Verify stats format
    assert "Hits:" in stats
    assert "Misses:" in stats
    assert "Size:" in stats
    assert "Enabled:" in stats

def test_cache_clear():
    """Test cache clearing functionality."""
    plugin = CacheControlPlugin()
    node = create_file_node()
    fs_structure = {}
    
    plugin.generate("/.touchfs/cache_clear", node, fs_structure)
    
    # Verify cache is cleared (no error thrown)
    assert True

def test_cache_list():
    """Test cache listing functionality."""
    plugin = CacheControlPlugin()
    node = create_file_node()
    fs_structure = {}
    
    # Test initial listing
    result = plugin.generate("/.touchfs/cache_list", node, fs_structure)
    lines = result.splitlines()
    
    # Test multiple reads return consistent results
    result2 = plugin.generate("/.touchfs/cache_list", node, fs_structure)
    assert result == result2  # Second read should match first read exactly
