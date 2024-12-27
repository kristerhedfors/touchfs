"""Tests for caching in content generator."""
import pytest
from unittest.mock import patch, MagicMock
from llmfs.content.generator import generate_filesystem, generate_file_content
from llmfs.models.filesystem import FileNode, FileAttrs
from llmfs.config.settings import set_cache_enabled
from llmfs.core.cache import get_cache_dir

@pytest.fixture
def test_cache_dir(tmp_path, monkeypatch):
    """Setup test cache directory."""
    test_cache = tmp_path / ".llmfs.cache"
    test_cache.mkdir()
    monkeypatch.setenv("LLMFS_CACHE_FOLDER", str(test_cache))
    return test_cache

@pytest.fixture
def mock_openai():
    """Mock OpenAI client."""
    with patch('llmfs.content.generator.OpenAI') as mock:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value.choices[0].message.content = """
        {
            "data": {
                "/": {
                    "type": "directory",
                    "children": {},
                    "attrs": {
                        "st_mode": "16877"
                    }
                }
            }
        }
        """
        mock.return_value = mock_client
        yield mock

@pytest.fixture
def mock_plugin_registry():
    """Mock plugin registry."""
    with patch('llmfs.content.generator.PluginRegistry') as mock:
        mock_generator = MagicMock()
        mock_generator.generate.return_value = "test content"
        mock_registry = MagicMock()
        mock_registry.get_generator.return_value = mock_generator
        mock.return_value = mock_registry
        yield mock

def test_filesystem_generation_caching(test_cache_dir, mock_openai, monkeypatch):
    """Test caching of filesystem generation."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    set_cache_enabled(True)
    
    # First generation should hit OpenAI
    fs1 = generate_filesystem("test prompt")
    assert mock_openai.return_value.chat.completions.create.call_count == 1
    
    # Second generation with same prompt should use cache
    fs2 = generate_filesystem("test prompt")
    assert mock_openai.return_value.chat.completions.create.call_count == 1
    assert fs1 == fs2
    
    # Different prompt should hit OpenAI again
    generate_filesystem("different prompt")
    assert mock_openai.return_value.chat.completions.create.call_count == 2

def test_file_content_generation_caching(test_cache_dir, mock_plugin_registry):
    """Test caching of file content generation."""
    set_cache_enabled(True)
    
    fs_structure = {
        "_plugin_registry": mock_plugin_registry.return_value,
        "/test.txt": {
            "type": "file",
            "attrs": {"st_mode": "33188"}
        }
    }
    
    # First generation should hit plugin
    content1 = generate_file_content("/test.txt", fs_structure.copy())
    assert mock_plugin_registry.return_value.get_generator.return_value.generate.call_count == 1
    
    # Second generation should use cache
    content2 = generate_file_content("/test.txt", fs_structure.copy())
    assert mock_plugin_registry.return_value.get_generator.return_value.generate.call_count == 1
    assert content1 == content2

def test_caching_disabled(test_cache_dir, mock_openai, mock_plugin_registry, monkeypatch):
    """Test behavior when caching is disabled."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    set_cache_enabled(False)
    
    # Filesystem generation should always hit OpenAI
    generate_filesystem("test prompt")
    generate_filesystem("test prompt")
    assert mock_openai.return_value.chat.completions.create.call_count == 2
    
    # File content generation should always hit plugin
    fs_structure = {
        "_plugin_registry": mock_plugin_registry.return_value,
        "/test.txt": {
            "type": "file",
            "attrs": {"st_mode": "33188"}
        }
    }
    generate_file_content("/test.txt", fs_structure.copy())
    generate_file_content("/test.txt", fs_structure.copy())
    assert mock_plugin_registry.return_value.get_generator.return_value.generate.call_count == 2
