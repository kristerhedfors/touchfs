"""Tests for the image generator plugin."""
import os
import base64
import pytest
from unittest.mock import patch, MagicMock
from touchfs.models.filesystem import FileNode, FileAttrs
from touchfs.content.plugins.image import ImageGenerator

def create_file_node(content=None, xattrs=None):
    """Helper to create a FileNode instance."""
    return FileNode(
        type="file",
        content=content,
        attrs=FileAttrs(st_mode="33188"),  # 644 permissions
        xattrs=xattrs or {}
    )

def test_image_generator_name():
    """Test that generator name is correct."""
    generator = ImageGenerator()
    assert generator.generator_name() == "image"

def test_supported_extensions():
    """Test that supported file extensions are handled."""
    generator = ImageGenerator()
    
    # Test supported extensions
    assert generator.can_handle("/test/image.jpg", create_file_node())
    assert generator.can_handle("/test/image.jpeg", create_file_node())
    assert generator.can_handle("/test/image.png", create_file_node())
    
    # Test unsupported extensions
    assert not generator.can_handle("/test/image.gif", create_file_node())
    assert not generator.can_handle("/test/image.txt", create_file_node())

def test_prompt_generation():
    """Test prompt generation from filename and .prompt file."""
    generator = ImageGenerator()
    
    # Test prompt from filename
    fs_structure = {
        "/test/sunset_over_mountains.jpg": create_file_node()
    }
    prompt = generator._generate_prompt("/test/sunset_over_mountains.jpg", fs_structure)
    assert "sunset over mountains" in prompt.lower()
    
    # Test prompt from .prompt file
    fs_structure = {
        "/test/.prompt": create_file_node(content="A beautiful mountain landscape at sunset"),
        "/test/image.jpg": create_file_node()
    }
    prompt = generator._generate_prompt("/test/image.jpg", fs_structure)
    assert "beautiful mountain landscape" in prompt.lower()

@patch('openai.OpenAI')
@patch('touchfs.content.plugins.image.get_cache_enabled')
def test_image_generation(mock_get_cache, mock_openai):
    """Test image generation with mocked OpenAI client."""
    # Disable caching for this test
    mock_get_cache.return_value = False
    # Mock chat completion response
    mock_chat_completion = MagicMock()
    mock_chat_completion.choices = [
        MagicMock(message=MagicMock(content="A beautiful sunset over mountains"))
    ]
    
    # Mock image generation response
    mock_data = MagicMock()
    # Add proper base64 padding
    mock_data.model_dump.return_value = {"b64_json": "ZmFrZV9iYXNlNjRfZGF0YQ=="}  # "fake_base64_data" in base64
    mock_response = MagicMock()
    mock_response.data = [mock_data]
    
    # Set up mock client
    mock_client = mock_openai.return_value
    mock_client.chat.completions.create.return_value = mock_chat_completion
    mock_client.images.generate.return_value = mock_response
    
    generator = ImageGenerator()
    generator.client = mock_client
    
    # Test successful generation
    fs_structure = {
        "/test/sunset.jpg": create_file_node()
    }
    result = generator.generate(
        path="/test/sunset.jpg",
        node=create_file_node(),
        fs_structure=fs_structure
    )
    assert result == b'fake_base64_data'
    
    # Verify OpenAI was called with correct parameters
    mock_client.images.generate.assert_called_once_with(
        model=generator.DEFAULT_MODEL,
        prompt="A beautiful sunset over mountains",  # This is the summarized prompt from chat completion
        size=generator.DEFAULT_SIZE,
        quality=generator.DEFAULT_QUALITY,
        response_format="b64_json",
        n=1
    )

@patch('openai.OpenAI')
def test_image_generation_error_handling(mock_openai):
    """Test error handling during image generation."""
    generator = ImageGenerator()
    
    # Test API error
    mock_client = mock_openai.return_value
    mock_client.images.generate.side_effect = Exception("API Error")
    generator.client = mock_client
    
    fs_structure = {
        "/test/error.jpg": create_file_node()
    }
    result = generator.generate("/test/error.jpg", create_file_node(), fs_structure)
    assert result is None

# Note: Integration tests for mounted filesystem functionality should be
# handled separately from unit tests, preferably in a dedicated test suite
# that can properly set up the required environment and handle filesystem
# mounting/unmounting safely.
