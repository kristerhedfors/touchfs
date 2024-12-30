"""Tests for .touchfs directory filtering."""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from openai import OpenAI
from touchfs.content.generator import generate_filesystem, generate_file_content
from touchfs.core.memory import MemoryBase

def test_touchfs_directory_filtering():
    """Test that .touchfs directory and its contents are filtered correctly."""
    # Set up environment
    client = OpenAI()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = """{
        "data": {
            "/": {
                "type": "directory",
                "attrs": {"st_mode": "16877"},
                "children": {
                    "calculator": "/calculator",
                    ".touchfs": "/.touchfs"
                },
            },
            "/calculator": {
                "type": "directory",
                "attrs": {"st_mode": "16877"},
                "children": {
                    "operations.py": "/calculator/operations.py"
                }
            },
            "/calculator/operations.py": {
                "type": "file",
                "attrs": {"st_mode": "33188"},
                "content": "def add(a, b): return a + b"
            },
            "/.touchfs": {
                "type": "directory",
                "attrs": {"st_mode": "16877"},
                "children": {
                    "cache": "/.touchfs/cache",
                    "prompt.default": "/.touchfs/prompt.default"
                },
            },
            "/.touchfs/cache": {
                "type": "file",
                "attrs": {"st_mode": "33188"},
                "content": "cache data"
            },
            "/.touchfs/prompt.default": {
                "type": "file",
                "attrs": {"st_mode": "33188"},
                "content": "default prompt"
            }
        }
    }"""

    with patch.object(client.chat.completions, 'create', return_value=mock_response):
        with patch('touchfs.content.generator.get_openai_client', return_value=client):
            from touchfs.content.generator import generate_filesystem

            # User prompt - should filter .touchfs
            fs_data = generate_filesystem("Create a calculator")
            fs = MemoryBase(fs_data)

            # Verify .touchfs entries are filtered out
            assert "/" in fs.data
            assert "/calculator/operations.py" in fs.data
            assert "/.touchfs" not in fs.data
            assert "/.touchfs/cache" not in fs.data
            assert "/.touchfs/prompt.default" not in fs.data
            assert ".touchfs" not in fs.data["/"].children

            # Internal prompt - should keep .touchfs
            fs_data = generate_filesystem("internal:setup")
            fs = MemoryBase(fs_data)

            # Verify .touchfs entries are preserved
            assert "/" in fs.data
            assert "/.touchfs" in fs.data
            assert "/.touchfs/cache" in fs.data
            assert "/.touchfs/prompt.default" in fs.data
            assert ".touchfs" in fs.data["/"].children

def test_touchfs_content_generation():
    """Test content generation for .touchfs files."""
    # Mock content for cache_stats
    mock_stats = "Cache hits: 10\nCache misses: 5"

    # Setup test structure with both user and .touchfs files
    fs_structure = {
        "/": {
            "type": "directory",
            "attrs": {"st_mode": "16877"},
            "children": {
                "calculator": "/calculator",
                ".touchfs": "/.touchfs"
            },
        },
        "/calculator": {
            "type": "directory",
            "attrs": {"st_mode": "16877"},
            "children": {
                "operations.py": "/calculator/operations.py"
            }
        },
        "/calculator/operations.py": {
            "type": "file",
            "attrs": {"st_mode": "33188"},
            "content": "def add(a, b): return a + b"
        },
        "/.touchfs": {
            "type": "directory",
            "attrs": {"st_mode": "16877"},
            "children": {
                "cache_stats": "/.touchfs/cache_stats"
            },
        },
        "/.touchfs/cache_stats": {
            "type": "file",
            "attrs": {"st_mode": "33188"},
            "xattrs": {"generator": "cache_control"}
        }
    }

    # Create a clean copy without .touchfs for comparison
    fs_structure_clean = {k: v for k, v in fs_structure.items() if not k.startswith("/.touchfs")}
    fs_structure_clean["/"]["children"] = {k: v for k, v in fs_structure_clean["/"]["children"].items() if k != ".touchfs"}

    with patch('touchfs.content.plugins.cache_control.CacheControlPlugin.generate', return_value=mock_stats):
        # First verify content is generated during size calculation
        base = MemoryBase(fs_structure_clean)
        assert len(base._data) == 3  # /, /calculator, /calculator/operations.py

        base = MemoryBase(fs_structure)
        assert len(base._data) == 5  # Should include .touchfs entries
        node = base[("/.touchfs/cache_stats")]
        assert node is not None

        from touchfs.content.generator import generate_file_content
        content = generate_file_content("/.touchfs/cache_stats", fs_structure)
        assert content == mock_stats

if __name__ == '__main__':
    pytest.main([__file__])
