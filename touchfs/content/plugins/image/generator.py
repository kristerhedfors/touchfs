"""Image generation using DALL-E API."""
import base64
import logging
import os
from typing import Optional
from openai import OpenAI
from openai.types import ImagesResponse
from ....models.filesystem import FileNode
from .types import ImageGenerationResult, ImageGenerationConfig
from .constants import DEFAULT_MODEL, DEFAULT_QUALITY, DEFAULT_SIZE, MIME_TYPES

logger = logging.getLogger("touchfs")

def get_mime_type(path: str) -> str:
    """Get MIME type based on file extension.
    
    Args:
        path: File path
        
    Returns:
        str: MIME type for the file extension
    """
    ext = os.path.splitext(path)[1].lower()
    return MIME_TYPES.get(ext, 'application/octet-stream')

def decode_image_data(image_data: str, path: str) -> Optional[bytes]:
    """Decode base64 image data to binary.
    
    Args:
        image_data: Base64 encoded image data
        path: Target file path for MIME type
        
    Returns:
        Optional[bytes]: Decoded binary data or None on error
    """
    try:
        # Add padding if needed
        padding_needed = len(image_data) % 4
        if padding_needed:
            image_data += '=' * (4 - padding_needed)
        
        # Decode base64 to raw binary
        return base64.b64decode(image_data)
    except Exception as e:
        logger.error(f"Failed to decode base64 image: {str(e)}")
        return None

def generate_image(
    client: OpenAI,
    prompt: str,
    path: str,
    config: Optional[ImageGenerationConfig] = None
) -> ImageGenerationResult:
    """Generate an image using DALL-E.
    
    Args:
        client: OpenAI client instance
        prompt: Optimized prompt for image generation
        path: Target file path
        config: Optional generation configuration
        
    Returns:
        ImageGenerationResult: Generated image data and metadata
    """
    try:
        # Use default config if none provided
        if not config:
            config = ImageGenerationConfig(
                model=DEFAULT_MODEL,
                size=DEFAULT_SIZE,
                quality=DEFAULT_QUALITY
            )
        
        # Generate image
        response: ImagesResponse = client.images.generate(
            model=config.model,
            prompt=prompt,
            size=config.size,
            quality=config.quality,
            response_format="b64_json",  # Get base64 data directly
            n=1
        )
        
        if not response.data:
            return ImageGenerationResult(
                content=b"",
                mime_type="",
                error="No image data in response"
            )
        
        # Get base64 image data
        if not hasattr(response.data[0], 'model_dump'):
            return ImageGenerationResult(
                content=b"",
                mime_type="",
                error="Invalid response format from OpenAI API"
            )
        
        image_data = response.data[0].model_dump().get('b64_json')
        if not image_data:
            return ImageGenerationResult(
                content=b"",
                mime_type="",
                error="No base64 data in response"
            )
        
        # Decode image data
        binary_data = decode_image_data(image_data, path)
        if not binary_data:
            return ImageGenerationResult(
                content=b"",
                mime_type="",
                error="Failed to decode image data"
            )
        
        # Get MIME type
        mime_type = get_mime_type(path)
        
        logger.debug(f"""generation_complete:
  content_type: binary
  mime_type: {mime_type}
  content_length: {len(binary_data)}""")
        
        return ImageGenerationResult(
            content=binary_data,
            mime_type=mime_type
        )
        
    except Exception as e:
        return ImageGenerationResult(
            content=b"",
            mime_type="",
            error=f"Failed to generate image: {str(e)}"
        )
