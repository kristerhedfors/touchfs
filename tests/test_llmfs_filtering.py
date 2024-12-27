"""Tests for .llmfs directory filtering."""
import os
import json
from unittest.mock import patch
from openai import OpenAI
from llmfs.models.filesystem import FileSystem, GeneratedContent
from llmfs.content.plugins.registry import PluginRegistry
from llmfs.content.plugins.default import DefaultGenerator

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

def test_llmfs_content_generation():
    """Test content generation for .llmfs files."""
    # Mock content for cache_stats
    mock_stats = (
        "Hits: 0\n"
        "Misses: 0\n"
        "Size: 0 bytes\n"
        "Enabled: True\n"
    )
    
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
    registry = PluginRegistry()
    default_gen = DefaultGenerator()
    
    # Mock the generate method to avoid OpenAI API call
    def mock_generate(*args, **kwargs):
        return "test content"
    default_gen.generate = mock_generate
    registry._generators['default'] = default_gen
    
    fs_structure['_plugin_registry'] = registry
    
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
        from llmfs.content.generator import generate_file_content
        content = generate_file_content("/.llmfs/cache_stats", fs_structure)
        assert content == mock_stats
        assert "Hits:" in content
        assert "Size:" in content
