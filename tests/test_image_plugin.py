"""Tests for the image generator plugin."""
import os
import base64
import pytest
from unittest.mock import patch, MagicMock
from touchfs.models.filesystem import FileNode, FileAttrs
from touchfs.content.plugins.image import ImageGenerator
from touchfs.content.plugins.image.types import (
    ImageGenerationConfig,
    ImageGenerationResult,
    PromptGenerationResult,
    ImageValidationResult
)

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

@patch('openai.OpenAI')
@patch('touchfs.content.plugins.image.prompt.generate_prompt')
@patch('touchfs.content.plugins.image.validate_image_data', return_value=ImageValidationResult(is_valid=False, format=None))
@patch('touchfs.content.plugins.image.cache.validate_image_data', return_value=ImageValidationResult(is_valid=False, format=None))
@patch('touchfs.config.settings.get_cache_enabled', return_value=False)
@patch('touchfs.core.cache.get_cached_response', return_value=None)
def test_prompt_generation(mock_core_cache, mock_cache_enabled, mock_cache_validate, mock_validate, mock_generate_prompt, mock_openai):
    """Test prompt generation from filename and .prompt file."""
    # Mock prompt generation result
    mock_generate_prompt.return_value = PromptGenerationResult(
        base_prompt="A beautiful mountain landscape at sunset",
        context="Context from filesystem",
        summarized_prompt="A serene mountain vista at dusk",
        source="nearest_file",
        source_path="/test/.prompt"
    )
    
    # Set up mock OpenAI client
    mock_client = mock_openai.return_value
    
    # Mock image generation response
    mock_data = MagicMock()
    mock_data.model_dump.return_value = {"b64_json": base64.b64encode(b'fake_image_data').decode()}
    mock_response = MagicMock()
    mock_response.data = [mock_data]
    mock_client.images.generate.return_value = mock_response
    
    generator = ImageGenerator()
    generator.client = mock_client
    
    # Test prompt generation with context
    fs_structure = {
        "/test/.prompt": create_file_node(content="A beautiful mountain landscape at sunset"),
        "/test/image.jpg": create_file_node()
    }
    
    result = generator.generate("/test/image.jpg", create_file_node(), fs_structure)
    
    # Verify prompt generation was called correctly
    mock_generate_prompt.assert_called_once()
    call_args = mock_generate_prompt.call_args
    assert call_args[0][1] == "/test/image.jpg"  # path
    assert call_args[0][2] == fs_structure  # fs_structure

@patch('openai.OpenAI')
def test_image_generation(mock_openai):
    """Test image generation with mocked components."""
    # Set up mock OpenAI client
    mock_client = mock_openai.return_value
    
    # Mock chat completion response
    mock_chat_completion = MagicMock()
    mock_chat_completion.choices = [
        MagicMock(message=MagicMock(content="A serene mountain sunset with hero silhouette"))
    ]
    mock_client.chat.completions.create.return_value = mock_chat_completion
    
    # Mock image generation response
    mock_data = MagicMock()
    mock_data.model_dump.return_value = {"b64_json": base64.b64encode(b'fake_image_data').decode()}
    mock_response = MagicMock()
    mock_response.data = [mock_data]
    mock_client.images.generate.return_value = mock_response
    
    generator = ImageGenerator()
    generator.client = mock_client
    
    # Test successful generation with context
    fs_structure = {
        "/test/sunset.jpg": create_file_node(),
        "/test/story.txt": create_file_node(content="An epic tale of a hero's journey through the mountains.")
    }
    
    result = generator.generate(
        path="/test/sunset.jpg",
        node=create_file_node(),
        fs_structure=fs_structure
    )
    
    assert result == b'fake_image_data'
    
    # Verify chat completion was called
    mock_client.chat.completions.create.assert_called_once()
    
    # Verify image generation was called
    mock_client.images.generate.assert_called_once()
    call_args = mock_client.images.generate.call_args
    assert call_args[1]['prompt'] == "A serene mountain sunset with hero silhouette"
    assert call_args[1]['model'] == "dall-e-3"
    assert call_args[1]['size'] == "1024x1024"

@patch('openai.OpenAI')
def test_image_caching(mock_openai):
    """Test image caching behavior."""
    # Set up mock OpenAI client
    mock_client = mock_openai.return_value
    
    # Mock chat completion response
    mock_chat_completion = MagicMock()
    mock_chat_completion.choices = [
        MagicMock(message=MagicMock(content="A serene mountain sunset with hero silhouette"))
    ]
    mock_client.chat.completions.create.return_value = mock_chat_completion
    
    # Mock image generation response
    mock_data = MagicMock()
    mock_data.model_dump.return_value = {"b64_json": base64.b64encode(b'generated_image_data').decode()}
    mock_response = MagicMock()
    mock_response.data = [mock_data]
    mock_client.images.generate.return_value = mock_response
    
    generator = ImageGenerator()
    generator.client = mock_client
    
    # Test cache hit and miss scenarios
    fs_structure = {
        "/test/cached.jpg": create_file_node(),
        "/test/story.txt": create_file_node(content="Context content")
    }
    
    # Test cache hit
    with patch('touchfs.config.settings.get_cache_enabled', return_value=True), \
         patch('touchfs.core.cache.get_cached_response', return_value=b'cached_image_data'), \
         patch('touchfs.content.plugins.image.validate_image_data', return_value=ImageValidationResult(is_valid=False, format=None)), \
         patch('touchfs.content.plugins.image.cache.validate_image_data', return_value=ImageValidationResult(is_valid=True, format='jpeg')):
        result = generator.generate(
            path="/test/cached.jpg",
            node=create_file_node(),
            fs_structure=fs_structure
        )
        assert result == b'cached_image_data'
        mock_client.images.generate.assert_not_called()
    
    # Test cache miss
    mock_client.images.generate.reset_mock()
    with patch('touchfs.config.settings.get_cache_enabled', return_value=True), \
         patch('touchfs.core.cache.get_cached_response', return_value=None), \
         patch('touchfs.content.plugins.image.validate_image_data', return_value=ImageValidationResult(is_valid=False, format=None)), \
         patch('touchfs.content.plugins.image.cache.validate_image_data', return_value=ImageValidationResult(is_valid=False, format=None)):
        result = generator.generate(
            path="/test/cached.jpg",
            node=create_file_node(),
            fs_structure=fs_structure
        )
        assert result == b'generated_image_data'
        mock_client.images.generate.assert_called_once()

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

def test_image_validation():
    """Test validation of existing image content."""
    generator = ImageGenerator()
    
    # Test valid JPEG
    jpeg_header = b'\xFF\xD8\xFF' + b'dummy_jpeg_data'
    node = create_file_node(content=jpeg_header)
    result = generator.generate("/test/valid.jpg", node, {})
    assert result == jpeg_header
    
    # Test valid PNG
    png_header = b'\x89PNG\r\n\x1A\n' + b'dummy_png_data'
    node = create_file_node(content=png_header)
    result = generator.generate("/test/valid.png", node, {})
    assert result == png_header
    
    # Test invalid image data
    node = create_file_node(content=b'invalid_image_data')
    result = generator.generate("/test/invalid.jpg", node, {})
    assert result != b'invalid_image_data'  # Should trigger regeneration
