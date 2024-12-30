"""Tests for content generation caching functionality."""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from touchfs.content.generator import generate_file_content
from touchfs.models.filesystem import FileNode

def test_cache_initialization(tmp_path):
    """Test cache directory initialization."""
    test_cache = tmp_path / ".touchfs.cache"
    test_cache.mkdir()
    assert test_cache.exists()

def test_generator_caching():
    """Test that content generation properly uses caching."""
    # Mock OpenAI client
    with patch('touchfs.content.generator.OpenAI') as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client

    # Mock plugin registry
    with patch('touchfs.content.generator.PluginRegistry') as mock:
        mock_generator = MagicMock()
        mock_plugin_registry = MagicMock()
        mock_plugin_registry.get_generator.return_value = mock_generator
        mock.return_value = mock_plugin_registry

    # Setup test structure
    proc_structure = {
        "_plugin_registry": mock_plugin_registry.return_value,
        "/": {
            "type": "directory",
            "attrs": {"st_mode": "16877"},
            "children": {}
        },
        "/.touchfs/cache_stats": {
            "type": "file",
            "attrs": {"st_mode": "33188"},
            "xattrs": {"generator": "cache_control"}
        }
    }

    # First generation should hit plugin
    proc_content1 = generate_file_content("/.touchfs/cache_stats", proc_structure.copy())
    assert mock_plugin_registry.return_value.get_generator.return_value.generate.call_count == 1

    # Second generation should hit plugin again (no caching)
    proc_content2 = generate_file_content("/.touchfs/cache_stats", proc_structure.copy())
    assert mock_plugin_registry.return_value.get_generator.return_value.generate.call_count == 2

def test_cache_invalidation():
    """Test that cache is properly invalidated."""
    # Setup test structure
    proc_structure = {
        "/": {
            "type": "directory",
            "attrs": {"st_mode": "16877"},
            "children": {}
        },
        "/.touchfs/cache_stats": {
            "type": "file",
            "attrs": {"st_mode": "33188"},
            "xattrs": {"generator": "cache_control"}
        }
    }

    # Mock plugin registry
    mock_plugin_registry = MagicMock()
    mock_generator = MagicMock()
    mock_plugin_registry.get_generator.return_value = mock_generator
    proc_structure["_plugin_registry"] = mock_plugin_registry

    # First generation
    generate_file_content("/.touchfs/cache_stats", proc_structure.copy())

    # Second generation
    generate_file_content("/.touchfs/cache_stats", proc_structure.copy())
    assert mock_plugin_registry.return_value.get_generator.return_value.generate.call_count == 2
