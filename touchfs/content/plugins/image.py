"""Image generator plugin that creates images using OpenAI's DALL-E API."""
import os
import base64
import logging
from typing import Dict, Optional
import requests
from openai import OpenAI
from openai.types import ImagesResponse
from ...models.filesystem import FileNode
from .base import BaseContentGenerator, OverlayFile

class ImageGenerator(BaseContentGenerator):
    """Generator that creates images using OpenAI's DALL-E API."""
    
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
    DEFAULT_SIZE = "1024x1024"  # Square images are fastest to generate
    DEFAULT_MODEL = "dall-e-3"
    DEFAULT_QUALITY = "standard"
    
    def __init__(self):
        """Initialize the image generator."""
        self.logger = logging.getLogger("touchfs")
        try:
            self.client = OpenAI()  # Uses OPENAI_API_KEY environment variable
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            self.client = None
    
    def generator_name(self) -> str:
        return "image"
    
    def can_handle(self, path: str, node: FileNode) -> bool:
        """Check if this generator should handle the given file."""
        ext = os.path.splitext(path)[1].lower()
        return ext in self.SUPPORTED_EXTENSIONS
    
    def get_overlay_files(self):
        """No overlay files needed for image generation."""
        return []
    
    def _download_image(self, url: str) -> Optional[bytes]:
        """Download image from URL and return as bytes."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.content
        except Exception as e:
            self.logger.error(f"Failed to download image: {str(e)}")
            return None
    
    def _generate_prompt(self, path: str, fs_structure: Dict[str, FileNode]) -> str:
        """Generate a prompt based on the file path and context."""
        # Extract filename without extension
        filename = os.path.splitext(os.path.basename(path))[0]
        # Replace underscores and dashes with spaces
        prompt = filename.replace('_', ' ').replace('-', ' ')
        
        # Look for a .prompt file in the same directory or parent directories
        dirname = os.path.dirname(path)
        while dirname:
            prompt_path = os.path.join(dirname, '.prompt')
            if prompt_path in fs_structure:
                prompt_node = fs_structure[prompt_path]
                if prompt_node.content:
                    # Use the prompt file's content instead
                    prompt = prompt_node.content.strip()
                    break
            if dirname == '/':
                break
            dirname = os.path.dirname(dirname)
        
        # Add a prefix to prevent DALL-E from adding details
        prompt = f"I NEED to test how the tool works with extremely simple prompts. DO NOT add any detail, just use it AS-IS: {prompt}"
        return prompt
    
    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> Optional[str]:
        """Generate an image using OpenAI's DALL-E API."""
        if not self.client:
            self.logger.error("OpenAI client not initialized")
            return None
            
        try:
            # Generate prompt from filename or .prompt file
            prompt = self._generate_prompt(path, fs_structure)
            self.logger.info(f"Generating image for path '{path}' with prompt: {prompt}")
            
            # Generate image
            response: ImagesResponse = self.client.images.generate(
                model=self.DEFAULT_MODEL,
                prompt=prompt,
                size=self.DEFAULT_SIZE,
                quality=self.DEFAULT_QUALITY,
                response_format="b64_json",  # Get base64 data directly instead of URL
                n=1
            )
            
            if not response.data:
                self.logger.error("No image data in response")
                return None
                
            # Get base64 image data
            if not response.data or not hasattr(response.data[0], 'model_dump'):
                self.logger.error("Invalid response format from OpenAI API")
                return None
                
            image_data = response.data[0].model_dump().get('b64_json')
            if not image_data:
                self.logger.error("No base64 data in response")
                return None
                
            # Return as string - the filesystem will handle binary conversion
            return image_data
            
        except Exception as e:
            self.logger.error(f"Failed to generate image: {str(e)}")
            return None
