"""Tests for the DefaultGenerator."""
import pytest
import logging
from unittest.mock import patch, MagicMock, ANY
from touchfs.content.plugins.default import DefaultGenerator
from touchfs.models.filesystem import FileNode, GeneratedContent, ContentMetadata
from touchfs.config.settings import get_global_prompt, get_model

def mock_completion(content="Generated content"):
    """Create a mock OpenAI completion response"""
    mock_message = MagicMock()
    mock_message.parsed = GeneratedContent(
        content=content,
        metadata=ContentMetadata(
            file_type="text",
            dependencies=[],
            imports=[]
        )
    )
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    return mock_completion

def create_file_node(content=None):
    """Helper to create a FileNode instance"""
    return FileNode(
        type="file",
        content=content,
        attrs={"st_mode": "33188"},  # 644 permissions
        xattrs={}
    )

@patch('touchfs.content.plugins.default.get_openai_client')
def test_prompt_file_lookup(mock_get_client, caplog):
    """Test prompt file lookup using settings module"""
    # Setup mock client
    mock_client = MagicMock()
    mock_client.beta.chat.completions.parse.return_value = mock_completion()
    mock_get_client.return_value = mock_client
    
    generator = DefaultGenerator()
    caplog.set_level(logging.DEBUG)
    
    # Create filesystem structure
    fs_structure = {
        "/project/src/file.py": create_file_node(),
        "/project/src/.touchfs.prompt": create_file_node("src prompt"),
        "/project/.touchfs.prompt": create_file_node("project prompt"),
        "/.touchfs.prompt": create_file_node("root prompt"),
    }
    
    # Test finding src/.touchfs.prompt (closest prompt)
    content = generator.generate("/project/src/file.py", fs_structure["/project/src/file.py"], fs_structure)
    assert "Found .touchfs.prompt in current dir: /project/src/.touchfs.prompt" in caplog.text
    assert """prompt_source:
  type: nearest_file
  path: /project/src/.touchfs.prompt""" in caplog.text
    caplog.clear()
    
    # Test finding root/.touchfs.prompt when src has no prompt
    fs_structure.pop("/project/src/.touchfs.prompt")
    content = generator.generate("/project/src/file.py", fs_structure["/project/src/file.py"], fs_structure)
    assert "Found .touchfs.prompt in root" in caplog.text
    assert """prompt_source:
  type: nearest_file
  path: /.touchfs.prompt""" in caplog.text
    caplog.clear()
    
    # Test finding root/.touchfs.prompt when project has no prompt
    fs_structure.pop("/project/.touchfs.prompt")
    content = generator.generate("/project/src/file.py", fs_structure["/project/src/file.py"], fs_structure)
    assert "Found .touchfs.prompt in root" in caplog.text
    assert """prompt_source:
  type: nearest_file
  path: /.touchfs.prompt""" in caplog.text
    caplog.clear()
    
    # Test falling back to global prompt when no files found
    fs_structure.pop("/.touchfs.prompt")
    content = generator.generate("/project/src/file.py", fs_structure["/project/src/file.py"], fs_structure)
    assert "No prompt file found" in caplog.text
    assert """prompt_source:
  type: global
  reason: no_nearest_file""" in caplog.text

@patch('touchfs.content.plugins.default.get_openai_client')
def test_model_file_lookup(mock_get_client, caplog):
    """Test model file lookup using settings module"""
    # Setup mock client
    mock_client = MagicMock()
    mock_client.beta.chat.completions.parse.return_value = mock_completion()
    mock_get_client.return_value = mock_client
    
    generator = DefaultGenerator()
    caplog.set_level(logging.DEBUG)
    
    # Create filesystem structure
    fs_structure = {
        "/project/src/file.py": create_file_node(),
        "/project/src/.touchfs.model": create_file_node("gpt-4o-2024-08-06"),
        "/project/.touchfs.model": create_file_node("gpt-3.5-turbo"),
        "/.touchfs.model": create_file_node("gpt-4"),
    }
    
    # Test finding src/.touchfs.model (closest model)
    content = generator.generate("/project/src/file.py", fs_structure["/project/src/file.py"], fs_structure)
    assert "Found .touchfs.model in current dir: /project/src/.touchfs.model" in caplog.text
    assert """model_source:
  type: nearest_file
  path: /project/src/.touchfs.model""" in caplog.text
    # Verify the correct model was used in the API call
    mock_client.beta.chat.completions.parse.assert_called_with(
        model="gpt-4o-2024-08-06",
        messages=ANY,
        response_format=GeneratedContent,
        temperature=0.2
    )
    caplog.clear()
    
    # Test finding project/.touchfs.model when src has no model
    fs_structure.pop("/project/src/.touchfs.model")
    content = generator.generate("/project/src/file.py", fs_structure["/project/src/file.py"], fs_structure)
    assert "Found .touchfs.model in root" in caplog.text
    assert """model_source:
  type: nearest_file
  path: /.touchfs.model""" in caplog.text
    # Verify the correct model was used in the API call
    mock_client.beta.chat.completions.parse.assert_called_with(
        model="gpt-4",
        messages=ANY,
        response_format=GeneratedContent,
        temperature=0.2
    )
    caplog.clear()
    
    # Test finding root/.touchfs.model when no other models exist
    fs_structure.pop("/project/.touchfs.model")
    content = generator.generate("/project/src/file.py", fs_structure["/project/src/file.py"], fs_structure)
    assert "Found .touchfs.model in root" in caplog.text
    assert """model_source:
  type: nearest_file
  path: /.touchfs.model""" in caplog.text
    # Verify the correct model was used in the API call
    mock_client.beta.chat.completions.parse.assert_called_with(
        model="gpt-4",
        messages=ANY,
        response_format=GeneratedContent,
        temperature=0.2
    )
    caplog.clear()
    
    # Test falling back to global model when no files found
    fs_structure.pop("/.touchfs.model")
    content = generator.generate("/project/src/file.py", fs_structure["/project/src/file.py"], fs_structure)
    assert "No model file found" in caplog.text
    assert """model_source:
  type: global
  reason: no_nearest_file""" in caplog.text
    # Verify the correct model was used in the API call
    mock_client.beta.chat.completions.parse.assert_called_with(
        model=get_model(),
        messages=ANY,
        response_format=GeneratedContent,
        temperature=0.2
    )

@patch('touchfs.content.plugins.default.get_openai_client')
def test_dict_conversion(mock_get_client, caplog):
    """Test handling of dictionary inputs for filesystem structure"""
    # Setup mock client
    mock_client = MagicMock()
    mock_client.beta.chat.completions.parse.return_value = mock_completion()
    mock_get_client.return_value = mock_client
    
    generator = DefaultGenerator()
    caplog.set_level(logging.DEBUG)
    
    # Create filesystem structure with dict instead of FileNode
    fs_structure = {
        "/test.py": {
            "type": "file",
            "content": "test content",
            "attrs": {"st_mode": "33188"},
            "xattrs": {}
        }
    }
    
    # Should successfully convert dict to FileNode and generate content
    content = generator.generate("/test.py", create_file_node(), fs_structure)
    assert content == "Generated content"  # From mock_completion
    
    # Verify context building worked with converted node
    assert "content_length:" in caplog.text  # Indicates successful generation
    
@patch('touchfs.content.plugins.default.get_openai_client')
def test_empty_files(mock_get_client, caplog):
    """Test handling of empty prompt and model files"""
    # Setup mock client
    mock_client = MagicMock()
    mock_client.beta.chat.completions.parse.return_value = mock_completion()
    mock_get_client.return_value = mock_client
    
    generator = DefaultGenerator()
    caplog.set_level(logging.DEBUG)
    
    # Create filesystem structure with empty files
    fs_structure = {
        "/project/src/file.py": create_file_node(),
        "/project/src/.touchfs.prompt": create_file_node(""),  # Empty prompt
        "/project/src/.touchfs.model": create_file_node(""),  # Empty model
        "/project/.touchfs.prompt": create_file_node("project prompt"),
        "/project/.touchfs.model": create_file_node("gpt-4"),
    }
    
    # Should skip empty files and find next ones
    content = generator.generate("/project/src/file.py", fs_structure["/project/src/file.py"], fs_structure)
    assert "Found .touchfs.prompt in current dir: /project/src/.touchfs.prompt" in caplog.text
    assert """prompt_source:
  type: global
  reason: nearest_file_empty""" in caplog.text
    assert "Found .touchfs.model in current dir: /project/src/.touchfs.model" in caplog.text
    assert """model_source:
  type: global
  reason: nearest_file_empty""" in caplog.text
    # Verify the correct model was used in the API call
    mock_client.beta.chat.completions.parse.assert_called_with(
        model=get_model(),
        messages=ANY,
        response_format=GeneratedContent,
        temperature=0.2
    )
