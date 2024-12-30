"""Tests for the tree plugin."""
import pytest
from touchfs.models.filesystem import FileNode
from touchfs.content.plugins.tree import TreeGenerator

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
                "readme.md": "/readme.md",
                "model.json": "/model.json",
                ".touchfs": "/.touchfs"
            },
            attrs={"st_mode": "16877"}
        ),
        "/.touchfs": FileNode(
            type="directory",
            children={
                "tree": "/.touchfs/tree",
                "default": "/.touchfs/default"
            },
            attrs={"st_mode": "16877"}
        ),
        "/.touchfs/tree": FileNode(
            type="file",
            content="tree content",
            attrs={"st_mode": "33188"},
            xattrs={"generator": "tree"}
        ),
        "/.touchfs/default": FileNode(
            type="file",
            content="default content",
            attrs={"st_mode": "33188"},
            xattrs={"generator": "default"}
        ),
        "/readme.md": FileNode(
            type="file",
            content="readme content",
            attrs={"st_mode": "33188"},
            xattrs={"generator": "readme"}
        ),
        "/model.json": FileNode(
            type="file",
            content="model content",
            attrs={"st_mode": "33188"},
            xattrs={"generator": "model"}
        ),
        "/dir1": FileNode(
            type="directory",
            children={},
            attrs={"st_mode": "16877"}
        )
    }
    
    generator = TreeGenerator()
    content = generator.generate("/", create_file_node(), structure)
    
    # Verify the output format
    lines = content.split("\n")
    
    # Skip header lines
    tree_lines = [line for line in lines if not line.startswith("#")]
    
    # Just verify that key generators are mentioned in the output
    content_str = "\n".join(lines)
    assert "default" in content_str, "default generator should be mentioned"
    assert "readme" in content_str, "readme generator should be mentioned"
    assert "tree" in content_str, "tree generator should be mentioned"
    assert "model" in content_str, "model generator should be mentioned"

def test_tree_can_handle():
    """Test that can_handle correctly identifies tree files."""
    generator = TreeGenerator()
    
    # Should handle .touchfs/tree
    assert generator.can_handle("/.touchfs/tree", create_file_node())
    
    # Should not handle other files
    assert not generator.can_handle("/some/other/file", create_file_node())
    assert not generator.can_handle("/.touchfs/other", create_file_node())

def test_tree_overlay_files():
    """Test that overlay files are correctly configured."""
    generator = TreeGenerator()
    overlays = generator.get_overlay_files()
    
    assert len(overlays) == 1
    assert overlays[0].path == "/.touchfs/tree"
    assert overlays[0].xattrs["generator"] == "tree"
