"""Tests for proc file functionality."""
import os
import pytest
from typing import Dict, List, Optional
from touchfs.core.jsonfs import JsonFS
from touchfs.content.plugins.base import BaseContentGenerator, ProcFile, ContentGenerator
from touchfs.models.filesystem import FileNode

class CustomPluginRegistry:
    """Simplified registry for testing that only registers specified plugins."""
    
    def __init__(self, root=None):
        self._generators = {}
        self._root = root
        
    def register_generator(self, generator: ContentGenerator) -> None:
        """Register a content generator."""
        name = generator.generator_name()
        if hasattr(generator, 'base'):
            generator.base = self._root
        self._generators[name] = generator
        
        # Initialize proc files
        if self._root:
            proc_files = generator.get_proc_files()
            for proc_file in proc_files:
                dirname = os.path.dirname(proc_file.path)
                basename = os.path.basename(proc_file.path)
                
                # Ensure parent directories exist
                current_path = "/"
                if dirname != "/":
                    for part in dirname.split("/")[1:]:
                        current_path = os.path.join(current_path, part)
                        if current_path not in self._root._data:
                            self._root._data[current_path] = {
                                "type": "directory",
                                "children": {},
                                "attrs": {"st_mode": "16877"}
                            }
                            parent_dir = os.path.dirname(current_path)
                            if parent_dir != current_path:
                                self._root._data[parent_dir]["children"][part] = current_path
                
                # Add file to filesystem
                self._root._data[proc_file.path] = {
                    "type": proc_file.type,
                    "content": proc_file.content,
                    "attrs": proc_file.attrs,
                    "xattrs": proc_file.xattrs
                }
                self._root._data[dirname]["children"][basename] = proc_file.path
    
    def get_generator(self, path: str, node: FileNode) -> Optional[ContentGenerator]:
        """Get generator that can handle the file."""
        for generator in self._generators.values():
            if generator.generator_name() == node.xattrs.get("generator"):
                return generator
        return None

class TestProcPlugin(BaseContentGenerator):
    """Test plugin that provides proc files."""
    
    def generator_name(self) -> str:
        return "test_proc"
    
    def get_proc_files(self) -> list[ProcFile]:
        """Provide test proc files."""
        proc_files = [
            ProcFile("/test.proc", {"generator": "test_proc"}),
            ProcFile("/nested/test.proc", {"generator": "test_proc"})
        ]
        return proc_files
    
    def generate(self, path: str, node: FileNode, fs_structure: dict) -> str:
        return f"Generated proc content for {path}"

def test_proc_file_initialization():
    """Test that proc files are properly initialized in the filesystem."""
    # Create filesystem
    fs = JsonFS()
    fs._data["/"] = {
        "type": "directory",
        "children": {},
        "attrs": {"st_mode": "16877"}
    }
    
    # Create and register test plugin
    test_plugin = TestProcPlugin()
    registry = CustomPluginRegistry(root=fs)
    registry.register_generator(test_plugin)
    
    # Verify proc files were added
    assert "/test.proc" in fs._data
    assert "/nested/test.proc" in fs._data
    assert "/nested" in fs._data
    
    # Verify proc file structure
    test_file = fs._data["/test.proc"]
    assert test_file["type"] == "file"
    assert test_file["xattrs"]["generator"] == "test_proc"
    
    # Verify nested directory was created
    nested_dir = fs._data["/nested"]
    assert nested_dir["type"] == "directory"
    assert nested_dir["children"]["test.proc"] == "/nested/test.proc"

def test_proc_file_content_generation():
    """Test that proc file content is generated correctly."""
    # Create filesystem with initial structure
    fs = JsonFS()
    fs._data["/"] = {
        "type": "directory",
        "children": {},
        "attrs": {"st_mode": "16877"}
    }
    
    # Create and register test plugin
    test_plugin = TestProcPlugin()
    registry = CustomPluginRegistry(root=fs)
    registry.register_generator(test_plugin)
    
    # Get proc file node
    proc_node = fs._data["/test.proc"]
    node = FileNode(
        type=proc_node["type"],
        content=proc_node.get("content", ""),
        attrs=proc_node["attrs"],
        xattrs=proc_node["xattrs"]
    )
    
    # Get generator and generate content
    generator = registry.get_generator("/test.proc", node)
    assert generator is not None
    
    content = generator.generate("/test.proc", node, fs._data)
    assert content == "Generated proc content for /test.proc"
