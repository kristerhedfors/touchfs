"""Tests for touched files functionality."""
import pytest
from llmfs.core.memory import Memory
from llmfs.config.logger import setup_logging

def test_touched_file_attributes():
    """Test that files marked with touched=true have correct attributes and xattrs."""
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
                    "touched": "true"
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
    
    # Verify touched file structure
    touched_attrs = mounted_fs.getattr("/touched.txt")
    assert touched_attrs is not None
    assert touched_attrs["st_mode"] == 33188  # Regular file
    
    # Verify touched xattr
    touched_xattr = mounted_fs.getxattr("/touched.txt", "touched")
    assert touched_xattr == b"true"
    
    # Verify untouched file structure
    untouched_attrs = mounted_fs.getattr("/untouched.txt")
    assert untouched_attrs is not None
    assert untouched_attrs["st_mode"] == 33188  # Regular file
    
    # Verify untouched file has no touched xattr
    untouched_xattr = mounted_fs.getxattr("/untouched.txt", "touched")
    assert untouched_xattr == b""  # Empty string for non-existent xattr

def test_touched_file_project_structure():
    """Test touched file attributes in a realistic project structure."""
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
                    "touched": "true"
                }
            }
        }
    }
    
    # Initialize Memory filesystem with the structure
    mounted_fs = Memory(fs_data["data"])
    
    # Verify README structure
    readme_attrs = mounted_fs.getattr("/README.md")
    assert readme_attrs is not None
    assert readme_attrs["st_mode"] == 33188  # Regular file
    
    # Verify README has touched xattr
    readme_xattr = mounted_fs.getxattr("/README.md", "touched")
    assert readme_xattr == b"true"
    
    # Verify main.py structure
    main_attrs = mounted_fs.getattr("/src/main.py")
    assert main_attrs is not None
    assert main_attrs["st_mode"] == 33188  # Regular file
    
    # Verify main.py has no touched xattr
    main_xattr = mounted_fs.getxattr("/src/main.py", "touched")
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
    
    # Verify empty.txt has no touched xattr initially
    empty_xattr = mounted_fs.getxattr("/empty.txt", "touched")
    assert empty_xattr == b""
    
    # Touch the empty file
    mounted_fs.utimens("/empty.txt")
    
    # Verify empty.txt now has touched xattr
    empty_xattr = mounted_fs.getxattr("/empty.txt", "touched")
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
    
    # Verify nonempty.txt has no touched xattr initially
    nonempty_xattr = mounted_fs.getxattr("/nonempty.txt", "touched")
    assert nonempty_xattr == b""
    
    # Touch the nonempty file
    mounted_fs.utimens("/nonempty.txt")
    
    # Verify nonempty.txt still has no touched xattr
    nonempty_xattr = mounted_fs.getxattr("/nonempty.txt", "touched")
    assert nonempty_xattr == b""

def test_touched_file_basic_structure():
    """Test basic structure validation for a touched file."""
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
                    "touched": "true"
                }
            }
        }
    }
    
    # Initialize Memory filesystem with the structure
    mounted_fs = Memory(fs_data["data"])
    
    # Verify error.txt structure
    error_attrs = mounted_fs.getattr("/error.txt")
    assert error_attrs is not None
    assert error_attrs["st_mode"] == 33188  # Regular file
    
    # Verify error.txt has touched xattr
    error_xattr = mounted_fs.getxattr("/error.txt", "touched")
    assert error_xattr == b"true"
