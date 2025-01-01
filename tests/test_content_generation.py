"""Tests for file content generation and prompt templates."""
import os
import time
import pytest
import subprocess
from fuse import FUSE
from unittest.mock import patch, mock_open
from openai import OpenAI
from touchfs.models.filesystem import FileSystem, GeneratedContent
from touchfs.core.memory import Memory
from touchfs.core.context.context import ContextBuilder
from touchfs.config.settings import CONTENT_GENERATION_SYSTEM_PROMPT_TEMPLATE

def test_content_generation_prompt_template():
    """Test that content generation prompt template properly integrates context."""
    # Create test context
    builder = ContextBuilder()
    builder.add_file_content("/test/file1.py", "def test1(): pass")
    context = builder.build()
    
    # Read prompt template
    with patch("builtins.open", mock_open(read_data="""
You are a content generator for a virtual filesystem. Your task is to generate appropriate content for a specific file based on its path and the surrounding context.

{CONTEXT}

Requirements:
1. Content must be unique to this specific file path
2. Content should be appropriate for the file's name and location
3. Content must be different from any other files in the same directory
4. Content should be consistent with the overall filesystem structure
5. Content should follow standard conventions for the file type

The response must be structured as follows:
{
    "content": "The actual file content here"
}
""")):
        with open(f"touchfs/templates/prompts/{CONTENT_GENERATION_SYSTEM_PROMPT_TEMPLATE}") as f:
            prompt_template = f.read()
    
    # Replace context placeholder
    prompt = prompt_template.replace("{CONTEXT}", context)
    
    # Verify prompt integration
    assert "You are a content generator" in prompt
    assert "def test1(): pass" in prompt
    assert "Content must be unique" in prompt
    assert '"content":' in prompt

def test_content_generation_model_validation():
    """Test that content generation uses the correct structured output model."""
    import pytest
    from pydantic import ValidationError
    from touchfs.models.filesystem import GeneratedContent
    
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
