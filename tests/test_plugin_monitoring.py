import os
import time
import pytest
from fuse import FUSE
from llmfs.core.operations import Memory
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

def test_plugin_invocation_on_file_access(mounted_fs_foreground):
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
                    "st_mode": "33188"
                },
                "xattrs": {
                    "generator": "test_plugin"
                }
            }
        }
    }
    
    # Initialize Memory filesystem with the structure
    mounted_fs = Memory(fs_data["data"])
    
    # Register our test plugin
    test_plugin = TestPlugin()
    registry = PluginRegistry()
    registry.register_generator(test_plugin)
    
    # Ensure mountpoint exists and has correct permissions
    os.makedirs(mounted_fs_foreground, exist_ok=True)
    os.chmod(mounted_fs_foreground, 0o777)
    
    # Mount the filesystem with proper permissions
    os.chmod(mounted_fs_foreground, 0o755)  # More restrictive permissions
    fuse = FUSE(
        mounted_fs,
        mounted_fs_foreground,
        foreground=True,
        allow_other=True,  # Allow other users to access
        nonempty=True
    )
    
    # Wait for filesystem to be mounted
    time.sleep(1)
    
    test_file = os.path.join(mounted_fs_foreground, "test.txt")
    
    try:
        # First read should trigger content generation
        with open(test_file, "r") as f:
            content1 = f.read()
        assert content1 == f"Generated content #1 for /test.txt"
        assert test_plugin.invocation_count == 1
        
        # Second read should return cached content
        with open(test_file, "r") as f:
            content2 = f.read()
        assert content2 == content1
        assert test_plugin.invocation_count == 1  # Should not increment
        
        # Write to file should clear cache
        with open(test_file, "w") as f:
            f.write("New content")
        
        # Next read should trigger generation again
        with open(test_file, "r") as f:
            content3 = f.read()
        assert content3 == f"Generated content #2 for /test.txt"
        assert test_plugin.invocation_count == 2
        
    finally:
        # Clean up
        import subprocess
        subprocess.run(["fusermount", "-u", mounted_fs_foreground], check=False)

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
