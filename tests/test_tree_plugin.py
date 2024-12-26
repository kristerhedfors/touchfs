"""Tests for the tree plugin."""
import pytest
from llmfs.models.filesystem import FileNode
from llmfs.content.plugins.tree import TreeGenerator

def create_file_node(content=None):
    """Helper to create a FileNode instance"""
    return FileNode(
        type="file",
        content=content,
        attrs={"st_mode": "33188"},  # 644 permissions
        xattrs={}
    )

def test_tree_generator_name():
    """Test that generator name is correct."""
    generator = TreeGenerator()
    assert generator.generator_name() == "tree"
    assert generator.get_proc_path() == "tree"

def test_tree_generation():
    """Test tree generation with a sample filesystem structure."""
    # Create a sample filesystem structure
    structure = {
        "/": FileNode(
            type="directory",
            children={
                "dir1": "/dir1",
                "file1": "/file1"
            },
            attrs={"st_mode": "16877"}
        ),
        "/dir1": FileNode(
            type="directory",
            children={
                "file2": "/dir1/file2"
            },
            attrs={"st_mode": "16877"}
        ),
        "/file1": FileNode(
            type="file",
            attrs={"st_mode": "33188"},
            xattrs={"generator": "config"}
        ),
        "/dir1/file2": FileNode(
            type="file",
            attrs={"st_mode": "33188"}
        )
    }
    
    generator = TreeGenerator()
    content = generator.generate("/", create_file_node(), structure)
    
    # Verify the output format
    lines = content.split("\n")
    assert "├── file1 [generator:config]" in content
    assert "├── dir1" in content
    assert "    └── file2 [generator:default]" in content

def test_tree_can_handle():
    """Test that can_handle correctly identifies tree files."""
    generator = TreeGenerator()
    
    # Should handle .llmfs/tree
    assert generator.can_handle("/.llmfs/tree", create_file_node())
    
    # Should not handle other files
    assert not generator.can_handle("/some/other/file", create_file_node())
    assert not generator.can_handle("/.llmfs/other", create_file_node())

def test_tree_overlay_files():
    """Test that overlay files are correctly configured."""
    generator = TreeGenerator()
    overlays = generator.get_overlay_files()
    
    assert len(overlays) == 1
    assert overlays[0].path == "/.llmfs/tree"
    assert overlays[0].xattrs["generator"] == "tree"
