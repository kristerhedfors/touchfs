"""Tests for proc-like file plugin functionality."""
import pytest
from unittest.mock import patch, MagicMock
from touchfs.content.plugins.proc import ProcPlugin
from touchfs.models.filesystem import FileNode

def create_file_node(content=None, xattrs=None):
    """Helper to create a FileNode for testing."""
    return FileNode(
        type="file",
        content=content,
        attrs={"st_mode": "33188"},
        xattrs=xattrs
    )

class TestPlugin(ProcPlugin):
    """Test implementation of ProcPlugin."""
    def generator_name(self) -> str:
        return "test"
        
    def get_proc_path(self) -> str:
        return "test"
        
    def generate(self, path: str, node: FileNode, fs_structure: dict) -> str:
        if "input_test" in path:
            if node.content:
                return f"parsed:{node.content}"
            return "default"
        return "test content"

def test_overlay_file_creation():
    """Test overlay file creation."""
    plugin = TestPlugin()
    overlays = plugin.get_overlay_files()
    assert len(overlays) == 1
    assert overlays[0].path == "/.touchfs/test"
    assert overlays[0].xattrs == {"generator": "test"}

def test_path_handling():
    """Test that plugin correctly handles different paths."""
    plugin = TestPlugin()
    
    # Should handle root .touchfs path
    assert plugin.can_handle("/.touchfs/test", create_file_node())
    
    # Should not handle other paths
    assert not plugin.can_handle("/project/.touchfs/test", create_file_node())
    assert not plugin.can_handle("/.touchfs/other", create_file_node())
    assert not plugin.can_handle("/test", create_file_node())

def test_content_generation():
    """Test content generation."""
    plugin = TestPlugin()
    
    # Test basic generation
    node = create_file_node()
    content = plugin.generate("/.touchfs/test", node, {})
    assert content == "test content"
    
    # Test with input content
    node = create_file_node(content="hello world")
    content = plugin.generate("/.touchfs/input_test", node, {})
    assert content == "parsed:hello world"
    
    # Test with no input content
    node = create_file_node()
    content = plugin.generate("/.touchfs/input_test", node, {})
    assert content == "default"
    
    # Test with JSON input
    node = create_file_node(content='{"test": "json value"}')
    content = plugin.generate("/.touchfs/input_test", node, {})
    assert content == 'parsed:{"test": "json value"}'
