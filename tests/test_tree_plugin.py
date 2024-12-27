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
                "file1": "/file1",
                "touched": "/touched",
                "empty": "/empty",
                ".llmfs": "/.llmfs"
            },
            attrs={"st_mode": "16877"}
        ),
        "/.llmfs": FileNode(
            type="directory",
            children={
                "prompt.default": "/.llmfs/prompt.default"
            },
            attrs={"st_mode": "16877"}
        ),
        "/.llmfs/prompt.default": FileNode(
            type="file",
            content="system prompt",
            attrs={"st_mode": "33188"},
            xattrs={"generator": "prompt"}
        ),
        "/dir1": FileNode(
            type="directory",
            children={
                "file2": "/dir1/file2",
                ".llmfs": "/dir1/.llmfs"
            },
            attrs={"st_mode": "16877"}
        ),
        "/dir1/.llmfs": FileNode(
            type="directory",
            children={
                "prompt.default": "/dir1/.llmfs/prompt.default"
            },
            attrs={"st_mode": "16877"}
        ),
        "/dir1/.llmfs/prompt.default": FileNode(
            type="file",
            content="dir1 prompt",
            attrs={"st_mode": "33188"},
            xattrs={"generator": "prompt"}
        ),
        "/file1": FileNode(
            type="file",
            attrs={"st_mode": "33188"},
            xattrs={"generator": "config"}
        ),
        "/touched": FileNode(
            type="file",
            content=None,
            attrs={"st_mode": "33188"},
            xattrs={"touched": "true"}
        ),
        "/empty": FileNode(
            type="file",
            content=None,
            attrs={"st_mode": "33188"}
        ),
        "/dir1/file2": FileNode(
            type="file",
            attrs={"st_mode": "33188"},
            xattrs={"touched": "true"}
        )
    }
    
    generator = TreeGenerator()
    content = generator.generate("/", create_file_node(), structure)
    
    # Verify the output format
    lines = content.split("\n")
    
    # Skip header lines
    tree_lines = [line for line in lines if not line.startswith("#")]
    
    # Verify all nodes are present with correct formatting
    file1_line = next(line for line in tree_lines if "file1" in line)
    assert "🔄 config" in file1_line, "file1 should show config generator"
    
    touched_line = next(line for line in tree_lines if "touched" in line)
    assert "🔄 default:/.llmfs/prompt.default" in touched_line, "touched file should show root prompt path"
    
    empty_line = next(line for line in tree_lines if "empty" in line)
    assert "🔄" not in empty_line, "empty file without touched xattr should not show generator"
    
    dir1_line = next(line for line in tree_lines if "dir1" in line and "file" not in line)
    assert "🔄" not in dir1_line, "dir1 should not have generator tag"
    
    file2_line = next(line for line in tree_lines if "file2" in line)
    assert "🔄 default:/dir1/.llmfs/prompt.default" in file2_line, "file2 should show dir1 prompt path"
    
    # Verify proper indentation structure
    assert any(file2_line.startswith(indent) for indent in [" ", "│", "└", "├"]), "file2 should be indented under dir1"
    
    # Verify header format
    header_lines = [line for line in lines if line.startswith("#")]
    assert any("Generator" in line for line in header_lines), "Header should include Generator column"
    assert not any("│" in line for line in header_lines), "Header should not include column separator"

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
