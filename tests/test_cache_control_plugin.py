"""Tests for the cache control plugin."""
import json
import os
import pytest
from pathlib import Path
from llmfs.content.plugins.cache_control import CacheControlPlugin
from llmfs.core import cache_stats
from llmfs.models.filesystem import FileNode, FileAttrs
from llmfs.config.settings import get_cache_enabled, set_cache_enabled
from llmfs.core.cache import get_cache_dir, get_cached_response, cache_response

@pytest.fixture
def plugin():
    return CacheControlPlugin()

@pytest.fixture
def fs_structure():
    return {}

@pytest.fixture
def test_cache_dir(tmp_path, monkeypatch):
    """Setup test cache directory."""
    test_cache = tmp_path / ".llmfs.cache"
    test_cache.mkdir()
    monkeypatch.setenv("LLMFS_CACHE_FOLDER", str(test_cache))
    return test_cache

def test_cache_enabled(plugin, fs_structure, test_cache_dir):
    """Test cache_enabled control file has global effect."""
    # Test reading initial state
    node = FileNode(
        type="file",
        attrs=FileAttrs(st_mode="0644")
    )
    result = plugin.generate("/.llmfs/cache_enabled", node, fs_structure)
    assert result in ["0\n", "1\n"]
    initial_state = result == "1\n"

    # Create test request/response
    request = {"test": "data"}
    response = {"result": "test"}
    
    # Test disabling cache globally
    node.content = "0"
    plugin.generate("/.llmfs/cache_enabled", node, fs_structure)
    assert not get_cache_enabled()
    
    # Verify cache is not used when disabled
    cache_response(request, response)
    assert get_cached_response(request) is None
    
    # Test enabling cache globally
    node.content = "1"
    plugin.generate("/.llmfs/cache_enabled", node, fs_structure)
    assert get_cache_enabled()
    
    # Verify cache is used when enabled
    cache_response(request, response)
    assert get_cached_response(request) == response

    # Reset to initial state
    set_cache_enabled(initial_state)

def test_cache_stats(plugin, fs_structure, test_cache_dir):
    """Test cache_stats control file."""
    # Reset stats at start of test
    cache_stats.reset_stats()
    
    # Create test request/response
    request = {"prompt": "test"}
    response = {"result": "test response"}
    
    # Test cache miss
    result1 = get_cached_response(request)
    assert result1 is None
    
    # Cache the response
    cache_response(request, response)
    
    # Test cache hit
    result2 = get_cached_response(request)
    assert result2 == response
    
    # Check stats
    node = FileNode(
        type="file",
        attrs=FileAttrs(st_mode="0644")
    )
    stats = plugin.generate("/.llmfs/cache_stats", node, fs_structure)
    
    assert "Hits: 1" in stats
    assert "Misses: 1" in stats
    assert "Size:" in stats
    assert "Enabled:" in stats

def test_cache_clear(plugin, fs_structure, test_cache_dir):
    """Test cache_clear control file."""
    # Create test cache file with explicit flush
    test_file = test_cache_dir / "test.json"
    with test_file.open('w') as f:
        f.write("{}")
        f.flush()
        os.fsync(f.fileno())
    
    # Verify cache file exists
    assert test_file.exists()

    # Clear cache
    node = FileNode(
        type="file",
        content="1",
        attrs=FileAttrs(st_mode="0644")
    )
    plugin.generate("/.llmfs/cache_clear", node, fs_structure)

    # Verify cache was cleared
    assert not test_file.exists()

def test_cache_list(plugin, fs_structure, test_cache_dir):
    """Test cache_list control file."""
    import time
    
    # Create filesystem requests
    for i in range(70):  # Create more than 64 entries to test limit
        request = {
            "type": "filesystem",
            "prompt": f"test prompt {i}",
            "model": "gpt-4",
            "system_prompt": "test system prompt"
        }
        response = {
            "data": {
                "test": "content" * 100  # Make response large enough for comma formatting
            }
        }
        cache_response(request, response)
        time.sleep(0.01)  # Ensure different timestamps
    
    # Create a file content request
    file_request = {
        "type": "file_content",
        "path": "/some/test/path"
    }
    file_response = {"data": "test content"}
    cache_response(file_request, file_response)
    
    # List cache
    node = FileNode(
        type="file",
        attrs=FileAttrs(st_mode="0644")
    )
    result = plugin.generate("/.llmfs/cache_list", node, fs_structure)
    lines = result.splitlines()
    
    # Verify format and limits
    assert len(lines) == 64  # Maximum 64 entries
    
    # Check format of entries
    for line in lines:
        parts = line.split()
        assert len(parts[0]) == 8  # Hash length
        
        # Check timestamp format
        import re
        timestamp_pattern = r"[A-Z][a-z]{2} \d{2} \d{2}:\d{2}"
        assert re.search(timestamp_pattern, line)
        
        # Check size format
        assert line.strip().endswith("bytes")
        size_str = line.strip().split()[-2]  # Get size number before "bytes"
        if size_str.replace(",", "").isdigit():  # Make sure it's a valid number
            size = int(size_str.replace(",", ""))
            if size > 999:
                assert "," in size_str, f"Large size {size} should have comma formatting"
    
    # Verify both types of entries are present
    assert any("test prompt" in line for line in lines), "No filesystem entries found"
    assert any("/some/test/path" in line for line in lines), "No file content entry found"
    
    # Test multiple reads return consistent results
    result2 = plugin.generate("/.llmfs/cache_list", node, fs_structure)
    assert result == result2  # Second read should match first read exactly

def test_cache_hits_and_misses(test_cache_dir):
    """Test cache hit/miss counting and proc file handling."""
    cache_stats.reset_stats()
    
    # Test LLM-generated file request
    llm_request = {
        "type": "filesystem",
        "prompt": "test prompt",
        "model": "gpt-4",
        "system_prompt": "test system prompt"
    }
    llm_response = {"data": {"test": "content"}}
    
    # Test proc file request
    proc_request = {
        "type": "file_content",
        "path": "/.llmfs/cache_stats",
        "node": {"type": "file", "attrs": {"st_mode": "0644"}},
        "fs_structure": {}
    }
    proc_response = "proc content"
    
    # Test initial miss for LLM request
    assert get_cached_response(llm_request) is None
    stats = cache_stats.get_stats()
    assert stats['misses'] == 1
    assert stats['hits'] == 0
    
    # Cache and test hit for LLM request
    cache_response(llm_request, llm_response)
    assert get_cached_response(llm_request) == llm_response
    stats = cache_stats.get_stats()
    assert stats['misses'] == 1
    assert stats['hits'] == 1
    
    # Test proc file is not cached
    cache_response(proc_request, proc_response)
    assert get_cached_response(proc_request) is None
    stats = cache_stats.get_stats()
    assert stats['misses'] == 2
    assert stats['hits'] == 1
