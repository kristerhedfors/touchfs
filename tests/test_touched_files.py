"""Tests for touched files functionality."""
import os
import pytest
from touchfs.core.memory import Memory
from touchfs.config.logger import setup_logging

def test_touched_file_attributes():
    """Test that files marked with generate_content=true have correct attributes and xattrs."""
    fs_data = {
        "data": {
            "/": {
                "type": "directory",
                "children": {
                    "touched.txt": "/touched.txt",
                    "untouched.txt": "/untouched.txt"
                },
                "attrs": {
                    "st_mode": "16877"
                }
            },
            "/touched.txt": {
                "type": "file",
                "content": None,
                "attrs": {
                    "st_mode": "33188"
                },
                "xattrs": {
                    "touchfs.generate_content": "true"
                }
            },
            "/untouched.txt": {
                "type": "file",
                "content": None,
                "attrs": {
                    "st_mode": "33188"
                }
            }
        }
    }
    
    # Initialize Memory filesystem with the structure
    mounted_fs = Memory(fs_data["data"])
    
    # Verify initial touched file structure and xattr
    touched_xattr = mounted_fs.getxattr("/touched.txt", "touchfs.generate_content")
    assert touched_xattr == b"true"  # Should have xattr before content generation
    
    # Trigger content generation
    touched_attrs = mounted_fs.getattr("/touched.txt")
    assert touched_attrs is not None
    assert touched_attrs["st_mode"] == 33188  # Regular file
    
    # Verify xattr is removed after content generation
    touched_xattr = mounted_fs.getxattr("/touched.txt", "touchfs.generate_content")
    assert touched_xattr == b""  # xattr should be removed after generation
    
    # Verify untouched file structure
    untouched_attrs = mounted_fs.getattr("/untouched.txt")
    assert untouched_attrs is not None
    assert untouched_attrs["st_mode"] == 33188  # Regular file
    
    # Verify untouched file has no generate_content xattr
    untouched_xattr = mounted_fs.getxattr("/untouched.txt", "touchfs.generate_content")
    assert untouched_xattr == b""  # Empty string for non-existent xattr

def test_touched_file_project_structure():
    """Test file generation attributes in a realistic project structure."""
    fs_data = {
        "data": {
            "/": {
                "type": "directory",
                "children": {
                    "src": "/src",
                    "README.md": "/README.md"
                },
                "attrs": {
                    "st_mode": "16877"
                }
            },
            "/src": {
                "type": "directory",
                "children": {
                    "main.py": "/src/main.py"
                },
                "attrs": {
                    "st_mode": "16877"
                }
            },
            "/src/main.py": {
                "type": "file",
                "content": None,
                "attrs": {
                    "st_mode": "33188"
                }
            },
            "/README.md": {
                "type": "file",
                "content": None,
                "attrs": {
                    "st_mode": "33188"
                },
                "xattrs": {
                    "touchfs.generate_content": "true"
                }
            }
        }
    }
    
    # Initialize Memory filesystem with the structure
    mounted_fs = Memory(fs_data["data"])
    
    # Verify initial README structure and xattr
    readme_xattr = mounted_fs.getxattr("/README.md", "touchfs.generate_content")
    assert readme_xattr == b"true"  # Should have xattr before content generation
    
    # Trigger content generation
    readme_attrs = mounted_fs.getattr("/README.md")
    assert readme_attrs is not None
    assert readme_attrs["st_mode"] == 33188  # Regular file
    
    # Verify xattr is removed after content generation
    readme_xattr = mounted_fs.getxattr("/README.md", "touchfs.generate_content")
    assert readme_xattr == b""  # xattr should be removed after generation
    
    # Verify main.py structure
    main_attrs = mounted_fs.getattr("/src/main.py")
    assert main_attrs is not None
    assert main_attrs["st_mode"] == 33188  # Regular file
    
    # Verify main.py has no generate_content xattr
    main_xattr = mounted_fs.getxattr("/src/main.py", "touchfs.generate_content")
    assert main_xattr == b""  # Empty string for non-existent xattr

def test_touch_empty_file(caplog):
    # Setup logging
    logger = setup_logging()
    """Test that touching an empty file marks it for generation."""
    fs_data = {
        "data": {
            "/": {
                "type": "directory",
                "children": {
                    "empty.txt": "/empty.txt"
                },
                "attrs": {
                    "st_mode": "16877"
                }
            },
            "/empty.txt": {
                "type": "file",
                "content": None,  # Empty file
                "attrs": {
                    "st_mode": "33188"
                }
            }
        }
    }
    
    # Initialize Memory filesystem with the structure
    mounted_fs = Memory(fs_data["data"])
    
    # Verify empty.txt has no generate_content xattr initially
    empty_xattr = mounted_fs.getxattr("/empty.txt", "touchfs.generate_content")
    assert empty_xattr == b""
    
    # Touch the empty file
    mounted_fs.utimens("/empty.txt")
    
    # Verify empty.txt now has generate_content xattr
    empty_xattr = mounted_fs.getxattr("/empty.txt", "touchfs.generate_content")
    assert empty_xattr == b"true"

def test_touch_nonempty_file():
    """Test that touching a file with content does not mark it for generation."""
    fs_data = {
        "data": {
            "/": {
                "type": "directory",
                "children": {
                    "nonempty.txt": "/nonempty.txt"
                },
                "attrs": {
                    "st_mode": "16877"
                }
            },
            "/nonempty.txt": {
                "type": "file",
                "content": "This file has content",
                "attrs": {
                    "st_mode": "33188"
                }
            }
        }
    }
    
    # Initialize Memory filesystem with the structure
    mounted_fs = Memory(fs_data["data"])
    
    # Verify nonempty.txt has no generate_content xattr initially
    nonempty_xattr = mounted_fs.getxattr("/nonempty.txt", "touchfs.generate_content")
    assert nonempty_xattr == b""
    
    # Touch the nonempty file
    mounted_fs.utimens("/nonempty.txt")
    
    # Verify nonempty.txt still has no generate_content xattr
    nonempty_xattr = mounted_fs.getxattr("/nonempty.txt", "touchfs.generate_content")
    assert nonempty_xattr == b""

def test_content_generation_on_size_check(monkeypatch):
    """Test that content is generated when checking size for touched files."""
    from test_helpers import MockGenerator
    from touchfs.content.plugins.registry import PluginRegistry
    
    # Create and register mock generator
    mock_generator = MockGenerator()
    registry = PluginRegistry()
    registry.register_generator(mock_generator)
    
    # Patch the plugin registry to use our mock
    def mock_get_generator(*args, **kwargs):
        return mock_generator
    monkeypatch.setattr(PluginRegistry, "get_generator", mock_get_generator)
    
    fs_data = {
        "data": {
            "/": {
                "type": "directory",
                "children": {
                    "touched.txt": "/touched.txt"
                },
                "attrs": {
                    "st_mode": "16877"
                }
            },
            "/touched.txt": {
                "type": "file",
                "content": "",
                "attrs": {
                    "st_mode": "33188",
                    "st_size": "0"
                },
                "xattrs": {
                    "touchfs.generate_content": b"true"
                }
            }
        }
    }
    
    # Initialize Memory filesystem with the structure and mock registry
    mounted_fs = Memory(fs_data["data"])
    mounted_fs._plugin_registry = registry
    
    # Verify initial state
    node = mounted_fs["/touched.txt"]
    assert node["content"] == ""
    assert node["attrs"]["st_size"] == "0"
    
    # Get attributes - this should trigger content generation
    attrs = mounted_fs.getattr("/touched.txt")
    
    # Verify content was generated
    node = mounted_fs["/touched.txt"]
    expected_content = f"Mock content for /touched.txt"
    assert node["content"] == expected_content  # Content should match mock
    assert attrs["st_size"] > 0  # Size should be updated
    assert attrs["st_size"] == len(expected_content.encode('utf-8'))  # Size should match content length

def test_touched_file_basic_structure():
    """Test basic structure validation for a file marked for generation."""
    fs_data = {
        "data": {
            "/": {
                "type": "directory",
                "children": {
                    "error.txt": "/error.txt"
                },
                "attrs": {
                    "st_mode": "16877"
                }
            },
            "/error.txt": {
                "type": "file",
                "content": None,
                "attrs": {
                    "st_mode": "33188"
                },
                "xattrs": {
                    "touchfs.generate_content": "true"
                }
            }
        }
    }
    
    # Initialize Memory filesystem with the structure
    mounted_fs = Memory(fs_data["data"])
    
    # Verify initial error.txt structure and xattr
    error_xattr = mounted_fs.getxattr("/error.txt", "touchfs.generate_content")
    assert error_xattr == b"true"  # Should have xattr before content generation
    
    # Trigger content generation
    error_attrs = mounted_fs.getattr("/error.txt")
    assert error_attrs is not None
    assert error_attrs["st_mode"] == 33188  # Regular file
    
    # Verify xattr is removed after content generation
    error_xattr = mounted_fs.getxattr("/error.txt", "touchfs.generate_content")
    assert error_xattr == b""  # xattr should be removed after generation
