"""Tests for the ProcPlugin base class."""
import pytest
from llmfs.content.plugins.proc import ProcPlugin
from llmfs.models.filesystem import FileNode

class TestProcPlugin(ProcPlugin):
    """Test implementation of ProcPlugin"""
    def generator_name(self) -> str:
        return "test"
        
    def get_proc_path(self) -> str:
        return "test"
        
    def generate(self, path: str, node: FileNode, fs_structure: dict) -> str:
        return "test content"

def create_file_node(content=None):
    """Helper to create a FileNode instance"""
    return FileNode(
        type="file",
        content=content,
        attrs={"st_mode": "33188"},  # 644 permissions
        xattrs={}
    )

def test_overlay_file_creation():
    """Test that overlay files are created correctly"""
    plugin = TestProcPlugin()
    overlays = plugin.get_overlay_files()
    
    assert len(overlays) == 1
    assert overlays[0].path == "/.llmfs/test"
    assert overlays[0].xattrs == {"generator": "test"}

def test_path_handling():
    """Test path handling and matching"""
    plugin = TestProcPlugin()
    
    # Should handle root .llmfs path
    assert plugin.can_handle("/.llmfs/test", create_file_node())
    
    # Should not handle other paths
    assert not plugin.can_handle("/project/.llmfs/test", create_file_node())
    assert not plugin.can_handle("/.llmfs/other", create_file_node())
    assert not plugin.can_handle("/test", create_file_node())

def test_content_generation():
    """Test basic content generation"""
    plugin = TestProcPlugin()
    node = create_file_node()
    content = plugin.generate("/.llmfs/test", node, {})
    assert content == "test content"

def test_input_parsing():
    """Test input parsing for proc files"""
    class InputTestPlugin(ProcPlugin):
        def generator_name(self) -> str:
            return "input_test"
            
        def get_proc_path(self) -> str:
            return "input_test"
            
        def generate(self, path: str, node: FileNode, fs_structure: dict) -> str:
            if node.content:
                # Return content with prefix to verify parsing
                return f"parsed:{node.content.strip()}"
            return "default"
    
    plugin = InputTestPlugin()
    
    # Test raw text input
    node = create_file_node(content="hello world")
    content = plugin.generate("/.llmfs/input_test", node, {})
    assert content == "parsed:hello world"
    
    # Test no input (default)
    node = create_file_node()
    content = plugin.generate("/.llmfs/input_test", node, {})
    assert content == "default"
    
    # Test JSON input
    node = create_file_node(content='{"test": "json value"}')
    content = plugin.generate("/.llmfs/input_test", node, {})
    assert content == 'parsed:{"test": "json value"}'
