"""Tests for filesystem structure generation and prompt templates."""
import os
import json
from unittest.mock import patch, mock_open
from openai import OpenAI
from touchfs.models.filesystem import FileSystem, FileNode, FileAttrs
from touchfs.core.context.context import ContextBuilder

def test_filesystem_generation_prompt_template():
    """Test that filesystem generation prompt template properly integrates context."""
    # Create test context
    builder = ContextBuilder()
    builder.add_file_content("/test/example.py", "print('Hello')")
    context = builder.build()
    
    # Read prompt template
    with patch("builtins.open", mock_open(read_data="""
You are a filesystem generator. Your task is to generate a JSON structure representing a filesystem based on the provided context.

Context Information:
{CONTEXT}

The filesystem must follow this exact structure:
""")):
        with open("touchfs/templates/prompts/filesystem_generation.prompt") as f:
            prompt_template = f.read()
    
    # Replace context placeholder
    prompt = prompt_template.replace("{CONTEXT}", context)
    
    # Verify prompt integration
    assert "You are a filesystem generator" in prompt
    assert "Context Information:" in prompt
    assert "print('Hello')" in prompt
    assert "/test/example.py" in prompt

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
        with patch('touchfs.content.generator.get_openai_client', return_value=client):
            from touchfs.content.generator import generate_filesystem
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

def test_default_generator_context_building():
    """Test that DefaultGenerator properly uses ContextBuilder for content generation."""
    from touchfs.content.plugins.default import DefaultGenerator
    from touchfs.models.filesystem import FileNode
    import json
    
    # Set up test data
    fs_structure = {
        "/test/file1.py": FileNode(
            type="file",
            content="def test1(): pass",
            attrs=FileAttrs(st_mode="33188")
        ),
        "/test/file2.py": FileNode(
            type="file",
            content="def test2(): pass",
            attrs=FileAttrs(st_mode="33188")
        )
    }
    
    # Create generator instance
    generator = DefaultGenerator()
    
    # Mock OpenAI client to capture the messages sent
    class MockOpenAI:
        def __init__(self):
            self.beta = type('Beta', (), {
                'chat': type('Chat', (), {
                    'completions': type('Completions', (), {
                        'parse': self.mock_parse
                    })()
                })()
            })()
            self.last_messages = None
            
        def mock_parse(self, model, messages, response_format, temperature):
            self.last_messages = messages
            return type('Response', (), {
                'choices': [type('Choice', (), {
                    'message': type('Message', (), {
                        'parsed': type('Parsed', (), {
                            'content': 'Generated content'
                        })()
                    })()
                })]
            })()
    
    mock_client = MockOpenAI()
    
    # Patch environment and OpenAI client
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'dummy-key'}):
        with patch('touchfs.content.plugins.default.get_openai_client', return_value=mock_client):
            # Generate content for a new file
            generator.generate("/test/new_file.py", FileNode(type="file", attrs=FileAttrs(st_mode="33188")), fs_structure)
    
    # Get the user message that was sent to OpenAI
    user_message = mock_client.last_messages[1]['content']
    
    # Verify context building
    assert '# Context Information' in user_message
    assert 'Total Files:' in user_message
    assert 'Token Count:' in user_message
    assert '# File: /test/file1.py' in user_message
    assert '# File: /test/file2.py' in user_message
    assert 'def test1(): pass' in user_message
    assert 'def test2(): pass' in user_message
