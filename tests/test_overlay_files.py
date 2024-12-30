"""Tests for overlay file functionality."""
import pytest
from touchfs.core.jsonfs import JsonFS
from touchfs.content.plugins.base import BaseContentGenerator, OverlayFile
from touchfs.content.plugins.registry import PluginRegistry
from touchfs.models.filesystem import FileNode

class TestOverlayPlugin(BaseContentGenerator):
    """Test plugin that provides overlay files."""
    
    def generator_name(self) -> str:
        return "test_overlay"
    
    def get_overlay_files(self) -> list[OverlayFile]:
        """Provide test overlay files."""
        overlays = [
            OverlayFile("/test.overlay", {"generator": "test_overlay"}),
            OverlayFile("/nested/test.overlay", {"generator": "test_overlay"})
        ]
        return overlays
    
    def generate(self, path: str, node: FileNode, fs_structure: dict) -> str:
        return f"Generated overlay content for {path}"

def test_overlay_file_initialization():
    """Test that overlay files are properly initialized in the filesystem."""
    # Create filesystem
    fs = JsonFS()
    
    # Create and register test plugin
    test_plugin = TestOverlayPlugin()
    registry = PluginRegistry(root=fs)
    registry.register_generator(test_plugin)
    
    # Verify overlay files were added
    assert "/test.overlay" in fs._data
    assert "/nested/test.overlay" in fs._data
    assert "/nested" in fs._data
    
    # Verify overlay file structure
    test_file = fs._data["/test.overlay"]
    assert test_file["type"] == "file"
    assert test_file["xattrs"]["generator"] == "test_overlay"
    
    # Verify nested directory was created
    nested_dir = fs._data["/nested"]
    assert nested_dir["type"] == "directory"
    assert nested_dir["children"]["test.overlay"] == "/nested/test.overlay"

def test_overlay_file_content_generation():
    """Test that overlay file content is generated correctly."""
    # Create filesystem with initial structure
    fs = JsonFS()
    fs._data["/"] = {
        "type": "directory",
        "children": {},
        "attrs": {"st_mode": "16877"}
    }
    
    # Create and register test plugin
    test_plugin = TestOverlayPlugin()
    registry = PluginRegistry(root=fs)
    registry.register_generator(test_plugin)
    
    # Get overlay file node
    overlay_node = fs._data["/test.overlay"]
    node = FileNode(
        type=overlay_node["type"],
        content=overlay_node.get("content", ""),
        attrs=overlay_node["attrs"],
        xattrs=overlay_node["xattrs"]
    )
    
    # Get generator and generate content
    generator = registry.get_generator("/test.overlay", node)
    assert generator is not None
    
    content = generator.generate("/test.overlay", node, fs._data)
    assert content == "Generated overlay content for /test.overlay"
