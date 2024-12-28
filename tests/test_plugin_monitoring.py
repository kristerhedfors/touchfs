import os
import time
import pytest
from fuse import FUSE
from llmfs.core.memory import Memory
from llmfs.content.plugins.base import BaseContentGenerator
from llmfs.content.plugins.registry import PluginRegistry
from llmfs.models.filesystem import FileNode

class TestPlugin(BaseContentGenerator):
    """Test plugin that generates predictable content."""
    
    invocation_count = 0  # Class variable instead of instance variable
    
    def generator_name(self) -> str:
        return "test_plugin"
    
    def generate(self, path: str, node: FileNode, fs_structure: dict) -> str:
        self.invocation_count += 1
        return f"Generated content #{self.invocation_count} for {path}"

def test_plugin_invocation_on_file_access():
    """Test that a registered plugin is invoked when its tagged files are accessed."""
    
    # Create initial filesystem structure with a file tagged for our test plugin
    fs_data = {
        "data": {
            "/": {
                "type": "directory",
                "children": {
                    "test.txt": "/test.txt"
                },
                "attrs": {
                    "st_mode": "16877"
                }
            },
            "/test.txt": {
                "type": "file",
                "content": None,
                    "attrs": {
                        "st_mode": "33188",
                        "st_size": "0"
                    },
                    "xattrs": {
                        "generator": "test_plugin",
                        "generate_content": b"true"
                    }
            }
        }
    }
    
    # Initialize Memory filesystem with the structure
    fs = Memory(fs_data["data"])
    test_plugin = TestPlugin()
    fs._plugin_registry.register_generator(test_plugin)
    
    # Get initial state
    node = fs["/test.txt"]
    assert node["content"] == ""
    assert node["attrs"]["st_size"] == "0"
    
    # Get attributes - this should trigger content generation
    attrs = fs.getattr("/test.txt")
    
    # Verify content was generated
    node = fs["/test.txt"]
    assert node["content"] == f"Generated content #1 for /test.txt"
    assert test_plugin.invocation_count == 1
    
    # Second check should use cached content
    attrs = fs.getattr("/test.txt")
    node = fs["/test.txt"]
    assert node["content"] == f"Generated content #1 for /test.txt"
    assert test_plugin.invocation_count == 1  # Should not increment
    
    # Clear content and mark for regeneration
    fs.truncate("/test.txt", 0)  # Clear content
    node = fs["/test.txt"]
    node["xattrs"]["generate_content"] = b"true"  # Mark for regeneration
    
    # Next check should trigger generation again
    attrs = fs.getattr("/test.txt")
    node = fs["/test.txt"]
    assert node["content"] == f"Generated content #2 for /test.txt"
    assert test_plugin.invocation_count == 2
        

def test_plugin_registration():
    """Test that plugins can be registered and retrieved correctly."""
    
    # Create and register test plugin
    test_plugin = TestPlugin()
    registry = PluginRegistry()
    registry.register_generator(test_plugin)
    
    # Create a test file node with plugin's generator tag
    node = FileNode(
        type="file",
        content=None,
        attrs={"st_mode": "33188"},
        xattrs={"generator": "test_plugin"}
    )
    
    # Verify plugin can be retrieved
    generator = registry.get_generator("/test.txt", node)
    assert generator is not None
    assert isinstance(generator, TestPlugin)
    assert generator.generator_name() == "test_plugin"
    
    # Verify plugin handles the tagged file
    assert generator.can_handle("/test.txt", node) is True
    
    # Verify plugin doesn't handle untagged file
    untagged_node = FileNode(
        type="file",
        content=None,
        attrs={"st_mode": "33188"}
    )
    assert generator.can_handle("/test.txt", untagged_node) is False
