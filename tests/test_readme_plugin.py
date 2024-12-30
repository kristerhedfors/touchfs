"""Tests for README plugin functionality."""
import pytest
from unittest.mock import patch, MagicMock
from touchfs.content.plugins.readme import ReadmePlugin
from touchfs.models.filesystem import FileNode

def create_file_node(content=None, xattrs=None):
    """Helper to create a FileNode for testing."""
    return FileNode(
        type="file",
        content=content,
        attrs={"st_mode": "33188"},
        xattrs=xattrs
    )

def test_readme_plugin_path_handling():
    """Test that plugin correctly handles different paths."""
    plugin = ReadmePlugin()
    
    # Should handle root readme
    assert plugin.can_handle("/.touchfs/readme", create_file_node())
    
    # Should not handle non-root readme files
    assert not plugin.can_handle("/project/.touchfs/readme", create_file_node())  # Only handles root .touchfs
    assert not plugin.can_handle("/README.md", create_file_node())
    
    # Should not handle other files
    assert not plugin.can_handle("/.touchfs/other", create_file_node())

def test_readme_generation():
    """Test readme content generation."""
    plugin = ReadmePlugin()
    
    # Setup test filesystem structure
    fs_structure = {
        "/": {
            "type": "directory",
            "children": {
                "src": "/src",
                "tests": "/tests"
            }
        },
        "/src": {
            "type": "directory",
            "children": {}
        },
        "/tests": {
            "type": "directory",
            "children": {}
        }
    }
    
    content = plugin.generate("/.touchfs/readme", create_file_node(), fs_structure)
    
    # Verify readme content
    assert "# Project Structure" in content
    assert "/src" in content
    assert "/tests" in content
