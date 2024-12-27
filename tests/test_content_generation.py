import os
import json
import time
import pytest
import subprocess
from fuse import FUSE
from unittest.mock import patch
from openai import OpenAI
from llmfs.models.filesystem import FileSystem, GeneratedContent
from llmfs.core.memory import Memory
from stat import S_IFREG

def test_content_generation_on_first_read(mounted_fs_foreground):
    """Test that file content is generated when first read using a real Python project structure."""
    # Set up environment for the test process
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "your-api-key-here")
    os.environ["LLMFS_PROMPT"] = "Create a Python calculator package"
    
    # Create initial filesystem structure
    fs_data = {
        "data": {
            "/": {
                "type": "directory",
                "children": {
                    "calculator": "/calculator",
                    "tests": "/tests"
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
            "/tests": {
                "type": "directory",
                "children": {
                    "test_operations.py": "/tests/test_operations.py"
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
            "/tests/test_operations.py": {
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
    
    # Ensure mountpoint exists and has correct permissions
    os.makedirs(mounted_fs_foreground, exist_ok=True)
    os.chmod(mounted_fs_foreground, 0o777)  # Give full permissions for testing
    
    # Mount the filesystem with nonempty option in foreground mode
    fuse = FUSE(mounted_fs, mounted_fs_foreground, foreground=True, nonempty=True)
    
    # Wait for filesystem to be mounted
    time.sleep(1)
    
    # Create paths for testing
    operations_file = os.path.join(mounted_fs_foreground, "calculator", "operations.py")
    test_file = os.path.join(mounted_fs_foreground, "tests", "test_operations.py")
    
    try:
        # First read should trigger content generation for operations.py
        with open(operations_file, "r") as f:
            operations_content = f.read()
            # Verify content was generated and makes sense for a calculator operations file
            assert "class Calculator" in operations_content or "def add" in operations_content
            assert len(operations_content.strip()) > 0
        
        # Second read should return cached content
        with open(operations_file, "r") as f:
            cached_content = f.read()
            assert cached_content == operations_content
            
        # Read test file to verify different but related content is generated
        with open(test_file, "r") as f:
            test_content = f.read()
            # Verify test content references operations
            assert "test" in test_content.lower()
            assert "calculator" in test_content.lower() or "operations" in test_content.lower()
            assert len(test_content.strip()) > 0
    finally:
        # Clean up
        import subprocess
        subprocess.run(["fusermount", "-u", mounted_fs_foreground], check=False)

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

def test_content_generation_model_validation():
    """Test that content generation uses the correct structured output model."""
    import pytest
    from pydantic import ValidationError
    from llmfs.models.filesystem import GeneratedContent
    
    # Test valid content
    valid_content = GeneratedContent(content="Hello World")
    assert valid_content.content == "Hello World"
    
    # Test empty content
    empty_content = GeneratedContent(content="")
    assert empty_content.content == ""
    
    # Test invalid model (missing required field)
    with pytest.raises(ValidationError):
        GeneratedContent()
    
    # Test invalid type
    with pytest.raises(ValidationError):
        GeneratedContent(content=123)  # content must be string

def test_content_generation_error_handling(mounted_fs_foreground):
    """Test error handling when content generation fails."""
    test_file = os.path.join(mounted_fs_foreground, "error_test.txt")
    with open(test_file, "w") as f:
        pass
    
    # Mock OpenAI API error
    def mock_api_error(**kwargs):
        raise Exception("API Error")
    
    # Read file with mocked API error
    with patch('openai.OpenAI') as mock_openai:
        mock_client = mock_openai.return_value
        mock_client.beta.chat.completions.parse.side_effect = mock_api_error
        mock_client.chat.completions.create.side_effect = mock_api_error
        with open(test_file, "r") as f:
            content = f.read()
    
    # Verify empty content is returned on error
    assert content == ""
    
    # Verify file is still accessible after error
    assert os.path.exists(test_file)

def test_llmfs_directory_filtering():
    """Test that .llmfs directory and its contents are filtered correctly."""
    # Set up environment
    os.environ["OPENAI_API_KEY"] = "dummy"
    
    # Create a real OpenAI client instance
    client = OpenAI(api_key="dummy")
    
    # Mock response with .llmfs entries
    mock_fs = {
        "data": {
            "/": {
                "type": "directory",
                "children": {
                    "calculator": "/calculator",
                    ".llmfs": "/.llmfs"
                },
                "attrs": {
                    "st_mode": "16877"
                }
            },
            "/calculator": {
                "type": "directory",
                "children": {
                    "operations.py": "/calculator/operations.py"
                },
                "attrs": {
                    "st_mode": "16877"
                }
            },
            "/.llmfs": {
                "type": "directory",
                "children": {
                    "cache": "/.llmfs/cache",
                    "prompt.default": "/.llmfs/prompt.default"
                },
                "attrs": {
                    "st_mode": "16877"
                }
            },
            "/.llmfs/cache": {
                "type": "file",
                "content": None,
                "attrs": {
                    "st_mode": "33188"
                }
            },
            "/.llmfs/prompt.default": {
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
            }
        }
    }
    
    # Test 1: User-generated filesystem should filter out .llmfs
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
            
            # User prompt - should filter .llmfs
            fs_data = generate_filesystem("Create a calculator")
            fs = FileSystem.model_validate(fs_data)
            
            # Verify .llmfs entries are filtered out
            assert "/" in fs.data
            assert "/calculator" in fs.data
            assert "/calculator/operations.py" in fs.data
            assert "/.llmfs" not in fs.data
            assert "/.llmfs/cache" not in fs.data
            assert "/.llmfs/prompt.default" not in fs.data
            assert ".llmfs" not in fs.data["/"].children
            
            # Internal prompt - should keep .llmfs
            fs_data = generate_filesystem("internal:setup")
            fs = FileSystem.model_validate(fs_data)
            
            # Verify .llmfs entries are preserved
            assert "/" in fs.data
            assert "/.llmfs" in fs.data
            assert "/.llmfs/cache" in fs.data
            assert "/.llmfs/prompt.default" in fs.data
            assert ".llmfs" in fs.data["/"].children
    
    # Test 2: Content generation
    mock_content_response = type('Response', (), {
        'choices': [type('Choice', (), {
            'message': type('Message', (), {
                'parsed': GeneratedContent(content="test content")
            })()
        })()]
    })()
    
    with patch.object(client.beta.chat.completions, 'parse', return_value=mock_content_response):
        with patch('llmfs.content.generator.get_openai_client', return_value=client):
            from llmfs.content.generator import generate_file_content
            
            # Setup test structure with both user and .llmfs files
            fs_structure = {
                "/": {
                    "type": "directory",
                    "children": {
                        "calculator": "/calculator",
                        ".llmfs": "/.llmfs"
                    },
                    "attrs": {"st_mode": "16877"}
                },
                "/calculator": {
                    "type": "directory",
                    "children": {
                        "operations.py": "/calculator/operations.py"
                    },
                    "attrs": {"st_mode": "16877"}
                },
                "/calculator/operations.py": {
                    "type": "file",
                    "content": None,
                    "attrs": {"st_mode": "33188"}
                },
                "/.llmfs": {
                    "type": "directory",
                    "children": {
                        "cache_stats": "/.llmfs/cache_stats"
                    },
                    "attrs": {"st_mode": "16877"}
                },
                "/.llmfs/cache_stats": {
                    "type": "file",
                    "content": None,
                    "attrs": {"st_mode": "33188"},
                    "xattrs": {"generator": "cache_control"}
                }
            }
            
                # Add plugin registry to structure
            from llmfs.content.plugins.registry import PluginRegistry
            from llmfs.content.plugins.default import DefaultGenerator
            
            # Create registry with mocked default generator
            registry = PluginRegistry()
            default_gen = DefaultGenerator()
            
            # Mock the generate method to avoid OpenAI API call
            def mock_generate(*args, **kwargs):
                return "test content"
            default_gen.generate = mock_generate
            registry._generators['default'] = default_gen
            
            fs_structure['_plugin_registry'] = registry
            
            # Test user file - should filter .llmfs from context
            content = generate_file_content("/calculator/operations.py", fs_structure)
            assert content == "test content"
            
            # Test .llmfs file - should use plugin generator and generate content immediately
            
            # Mock plugin generation for cache_stats
            mock_stats = (
                "Hits: 0\n"
                "Misses: 0\n"
                "Size: 0 bytes\n"
                "Enabled: True\n"
            )
            
            with patch('llmfs.content.plugins.cache_control.CacheControlPlugin.generate', return_value=mock_stats):
                    # First verify content is generated during size calculation
                    from llmfs.core.memory.base import MemoryBase
                    # Create clean copy of structure without registry
                    fs_structure_clean = {k: v for k, v in fs_structure.items() if k != '_plugin_registry'}
                    base = MemoryBase(fs_structure_clean)
                    node = base[("/.llmfs/cache_stats")]
                    
                    # Size calculation should trigger content generation
                    size = base._get_size(node)
                    assert size == len(mock_stats.encode('utf-8'))
                    assert node["content"] == mock_stats
                
                    # Content should already be available when explicitly requested
                    content = generate_file_content("/.llmfs/cache_stats", fs_structure)
                    assert content == mock_stats
                    assert "Hits:" in content
                    assert "Size:" in content

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
