"""Tests for executive summary plugin functionality."""
import pytest
from unittest.mock import patch, MagicMock
from touchfs.content.plugins.executive import ExecutiveGenerator
from touchfs.models.filesystem import FileNode

def create_file_node(content=None, xattrs=None):
    """Helper to create a FileNode for testing."""
    return FileNode(
        type="file",
        content=content,
        attrs={"st_mode": "33188"},
        xattrs=xattrs
    )

def test_overlay_file_creation():
    """Test overlay file is created in .touchfs directory."""
    generator = ExecutiveGenerator()
    overlays = generator.get_overlay_files()
    assert len(overlays) == 1
    assert overlays[0].path == "/.touchfs/executive"
    assert overlays[0].xattrs["generator"] == "executive"

def test_executive_summary_generation():
    """Test executive summary generation."""
    # Setup test structure
    structure = {
        "/": {
            "type": "directory",
            "attrs": {"st_mode": "16877"},
            "children": {
                "src": "/src",
                ".touchfs": "/.touchfs",
                "requirements.txt": "/requirements.txt"
            }
        },
        "/src/utils.py": create_file_node(xattrs={"touched": "true"}),
        "/.touchfs": FileNode(
            type="directory",
            attrs={"st_mode": "16877"},
            children={
                "tree": "/.touchfs/tree",
                "prompt.default": "/.touchfs/prompt.default"
            },
        ),
        "/.touchfs/tree": create_file_node(xattrs={"generator": "tree"}),
        "/.touchfs/prompt.default": create_file_node(
            content="test prompt",
            attrs={"st_mode": "33188"}
        )
    }
    
    generator = ExecutiveGenerator()
    summary = generator.generate("/.touchfs/executive", create_file_node(), structure)
    
    # Verify summary content
    assert "Project Structure" in summary
    assert "src" in summary
    assert "utils.py" in summary
    assert "requirements.txt" in summary

def test_path_handling():
    """Test that plugin correctly handles different paths."""
    generator = ExecutiveGenerator()
    
    # Should handle .touchfs/executive
    assert generator.can_handle(
        "/.touchfs/executive",
        create_file_node(xattrs={"generator": "executive"})
    )
    
    # Should not handle other files
    assert not generator.can_handle(
        "/.touchfs/other",
        create_file_node(xattrs={"generator": "other"})
    )
