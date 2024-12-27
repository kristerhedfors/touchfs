"""Tests for filesystem structure generation."""
import os
import json
from unittest.mock import patch
from openai import OpenAI
from llmfs.models.filesystem import FileSystem

def test_filesystem_structure_generation():
    """Test filesystem structure generation for a Python calculator package."""
    # Set up environment
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "your-api-key-here")
    
    # Create filesystem structure for a calculator package
    fs_data = {
        "data": {
            "/": {
                "type": "directory",
                "children": {
                    "calculator": "/calculator",
                    "tests": "/tests",
                    "setup.py": "/setup.py",
                    "README.md": "/README.md"
                },
                "attrs": {
                    "st_mode": "16877"
                }
            },
            "/calculator": {
                "type": "directory",
                "children": {
                    "__init__.py": "/calculator/__init__.py",
                    "operations.py": "/calculator/operations.py"
                },
                "attrs": {
                    "st_mode": "16877"
                }
            },
            "/calculator/__init__.py": {
                "type": "file",
                "content": None,
                "attrs": {
                    "st_mode": "33188"
                }
            },
            "/calculator/operations.py": {
                "type": "file",
                "content": None,
                "attrs": {
                    "st_mode": "33188"
                }
            },
            "/tests": {
                "type": "directory",
                "children": {
                    "test_operations.py": "/tests/test_operations.py"
                },
                "attrs": {
                    "st_mode": "16877"
                }
            },
            "/tests/test_operations.py": {
                "type": "file",
                "content": None,
                "attrs": {
                    "st_mode": "33188"
                }
            },
            "/setup.py": {
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
                }
            }
        }
    }
    
    # Validate the structure using the FileSystem model
    fs = FileSystem.model_validate(fs_data)
    
    # Verify structure matches a typical Python package
    assert "/" in fs.data
    assert "/calculator" in fs.data
    assert "/calculator/__init__.py" in fs.data
    assert "/calculator/operations.py" in fs.data
    assert "/tests" in fs.data
    assert "/tests/test_operations.py" in fs.data
    assert "/setup.py" in fs.data
    assert "/README.md" in fs.data
    
    # Verify file attributes
    operations_py = fs.data["/calculator/operations.py"]
    assert operations_py.type == "file"
    assert operations_py.content is None  # Content should be null initially
    assert operations_py.attrs.st_mode == "33188"  # 644 permissions

def test_filesystem_prompt_generation():
    """Test filesystem generation from prompt."""
    # Set up environment
    os.environ["OPENAI_API_KEY"] = "dummy"
    
    # Create a real OpenAI client instance
    client = OpenAI(api_key="dummy")
    
    # Mock response that matches calculator package structure
    mock_fs = {
        "data": {
            "/": {
                "type": "directory",
                "children": {
                    "calculator": "/calculator",
                    "tests": "/tests",
                    "setup.py": "/setup.py",
                    "README.md": "/README.md"
                },
                "attrs": {
                    "st_mode": "16877"
                }
            },
            "/calculator": {
                "type": "directory",
                "children": {
                    "__init__.py": "/calculator/__init__.py",
                    "operations.py": "/calculator/operations.py"
                },
                "attrs": {
                    "st_mode": "16877"
                }
            },
            "/calculator/__init__.py": {
                "type": "file",
                "content": None,
                "attrs": {
                    "st_mode": "33188"
                }
            },
            "/calculator/operations.py": {
                "type": "file",
                "content": None,
                "attrs": {
                    "st_mode": "33188"
                }
            },
            "/tests": {
                "type": "directory",
                "children": {
                    "test_operations.py": "/tests/test_operations.py"
                },
                "attrs": {
                    "st_mode": "16877"
                }
            },
            "/tests/test_operations.py": {
                "type": "file",
                "content": None,
                "attrs": {
                    "st_mode": "33188"
                }
            },
            "/setup.py": {
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
                }
            }
        }
    }
    
    mock_response = type('Response', (), {
        'choices': [type('Choice', (), {
            'message': type('Message', (), {
                'content': json.dumps(mock_fs)
            })()
        })()]
    })()
    
    with patch.object(client.chat.completions, 'create', return_value=mock_response):
        with patch('llmfs.content.generator.get_openai_client', return_value=client):
            from llmfs.content.generator import generate_filesystem
            fs_data = generate_filesystem("Create a Python calculator package")
    
    # Validate structure using FileSystem model
    fs = FileSystem.model_validate(fs_data)
    
    # Verify structure matches calculator package layout
    assert "/" in fs.data
    assert "/calculator" in fs.data
    assert "/calculator/__init__.py" in fs.data
    assert "/calculator/operations.py" in fs.data
    assert "/tests" in fs.data
    assert "/tests/test_operations.py" in fs.data
    assert "/setup.py" in fs.data
    assert "/README.md" in fs.data
    
    # Verify file attributes
    operations_py = fs.data["/calculator/operations.py"]
    assert operations_py.type == "file"
    assert operations_py.content is None
