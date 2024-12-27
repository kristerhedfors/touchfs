"""Tests for basic file content generation."""
import os
import time
import pytest
import subprocess
from fuse import FUSE
from unittest.mock import patch
from openai import OpenAI
from llmfs.models.filesystem import FileSystem, GeneratedContent
from llmfs.core.memory import Memory

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
