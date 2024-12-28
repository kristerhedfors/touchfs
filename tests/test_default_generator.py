"""Tests for the DefaultGenerator."""
import pytest
import logging
from unittest.mock import patch, MagicMock, ANY
from llmfs.content.plugins.default import DefaultGenerator
from llmfs.models.filesystem import FileNode, GeneratedContent
from llmfs.config.settings import get_global_prompt, get_model

def mock_completion(content="Generated content"):
    """Create a mock OpenAI completion response"""
    mock_message = MagicMock()
    mock_message.parsed = GeneratedContent(content=content)
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

@patch('llmfs.content.plugins.default.get_openai_client')
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
        "/project/src/.llmfs.prompt": create_file_node("src prompt"),
        "/project/.llmfs.prompt": create_file_node("project prompt"),
        "/.llmfs.prompt": create_file_node("root prompt"),
    }
    
    # Test finding src/.llmfs.prompt (closest prompt)
    content = generator.generate("/project/src/file.py", fs_structure["/project/src/file.py"], fs_structure)
    assert "Found .llmfs.prompt in current dir: /project/src/.llmfs.prompt" in caplog.text
    assert "Using prompt from nearest file: /project/src/.llmfs.prompt" in caplog.text
    caplog.clear()
    
    # Test finding project/.llmfs.prompt when src has no prompt
    fs_structure.pop("/project/src/.llmfs.prompt")
    content = generator.generate("/project/src/file.py", fs_structure["/project/src/file.py"], fs_structure)
    assert "Found .llmfs.prompt in root" in caplog.text
    assert "Using prompt from nearest file: /.llmfs.prompt" in caplog.text
    caplog.clear()
    
    # Test finding root/.llmfs.prompt when no other prompts exist
    fs_structure.pop("/project/.llmfs.prompt")
    content = generator.generate("/project/src/file.py", fs_structure["/project/src/file.py"], fs_structure)
    assert "Found .llmfs.prompt in root" in caplog.text
    assert "Using prompt from nearest file: /.llmfs.prompt" in caplog.text
    caplog.clear()
    
    # Test falling back to global prompt when no files found
    fs_structure.pop("/.llmfs.prompt")
    content = generator.generate("/project/src/file.py", fs_structure["/project/src/file.py"], fs_structure)
    assert "No prompt file found" in caplog.text
    assert "Using global prompt (no nearest file)" in caplog.text

@patch('llmfs.content.plugins.default.get_openai_client')
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
        "/project/src/.llmfs.model": create_file_node("gpt-4o-2024-08-06"),
        "/project/.llmfs.model": create_file_node("gpt-3.5-turbo"),
        "/.llmfs.model": create_file_node("gpt-4"),
    }
    
    # Test finding src/.llmfs.model (closest model)
    content = generator.generate("/project/src/file.py", fs_structure["/project/src/file.py"], fs_structure)
    assert "Found .llmfs.model in current dir: /project/src/.llmfs.model" in caplog.text
    assert "Using model from nearest file: /project/src/.llmfs.model" in caplog.text
    # Verify the correct model was used in the API call
    mock_client.beta.chat.completions.parse.assert_called_with(
        model="gpt-4o-2024-08-06",
        messages=ANY,
        response_format=GeneratedContent,
        temperature=0.2
    )
    caplog.clear()
    
    # Test finding project/.llmfs.model when src has no model
    fs_structure.pop("/project/src/.llmfs.model")
    content = generator.generate("/project/src/file.py", fs_structure["/project/src/file.py"], fs_structure)
    assert "Found .llmfs.model in root" in caplog.text
    assert "Using model from nearest file: /.llmfs.model" in caplog.text
    # Verify the correct model was used in the API call
    mock_client.beta.chat.completions.parse.assert_called_with(
        model="gpt-4",
        messages=ANY,
        response_format=GeneratedContent,
        temperature=0.2
    )
    caplog.clear()
    
    # Test finding root/.llmfs.model when no other models exist
    fs_structure.pop("/project/.llmfs.model")
    content = generator.generate("/project/src/file.py", fs_structure["/project/src/file.py"], fs_structure)
    assert "Found .llmfs.model in root" in caplog.text
    assert "Using model from nearest file: /.llmfs.model" in caplog.text
    # Verify the correct model was used in the API call
    mock_client.beta.chat.completions.parse.assert_called_with(
        model="gpt-4",
        messages=ANY,
        response_format=GeneratedContent,
        temperature=0.2
    )
    caplog.clear()
    
    # Test falling back to global model when no files found
    fs_structure.pop("/.llmfs.model")
    content = generator.generate("/project/src/file.py", fs_structure["/project/src/file.py"], fs_structure)
    assert "No model file found" in caplog.text
    assert "Using global model (no nearest file)" in caplog.text
    # Verify the correct model was used in the API call
    mock_client.beta.chat.completions.parse.assert_called_with(
        model=get_model(),
        messages=ANY,
        response_format=GeneratedContent,
        temperature=0.2
    )

@patch('llmfs.content.plugins.default.get_openai_client')
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
        "/project/src/.llmfs.prompt": create_file_node(""),  # Empty prompt
        "/project/src/.llmfs.model": create_file_node(""),  # Empty model
        "/project/.llmfs.prompt": create_file_node("project prompt"),
        "/project/.llmfs.model": create_file_node("gpt-4"),
    }
    
    # Should skip empty files and find next ones
    content = generator.generate("/project/src/file.py", fs_structure["/project/src/file.py"], fs_structure)
    assert "Found .llmfs.prompt in current dir: /project/src/.llmfs.prompt" in caplog.text
    assert "Using global prompt (nearest file empty)" in caplog.text
    assert "Found .llmfs.model in current dir: /project/src/.llmfs.model" in caplog.text
    assert "Using global model (nearest file empty)" in caplog.text
    # Verify the correct model was used in the API call
    mock_client.beta.chat.completions.parse.assert_called_with(
        model=get_model(),
        messages=ANY,
        response_format=GeneratedContent,
        temperature=0.2
    )
