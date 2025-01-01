"""Image generation plugin using DALL-E."""
import os
import logging
from typing import Dict, List, Optional
from openai import OpenAI
from ....models.filesystem import FileNode
from ..base import BaseContentGenerator, OverlayFile
from .constants import SUPPORTED_EXTENSIONS
from .types import ImageGenerationConfig
from .cache import get_cached_image, cache_image, validate_image_data
from .prompt import generate_prompt
from .generator import generate_image

class ImageGenerator(BaseContentGenerator):
    """Generator that creates images using OpenAI's DALL-E API."""
    
    def __init__(self):
        """Initialize the image generator."""
        self.logger = logging.getLogger("touchfs")
        try:
            self.client = OpenAI()  # Uses OPENAI_API_KEY environment variable
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            self.client = None
    
    def generator_name(self) -> str:
        """Get the name of this generator."""
        return "image"
    
    def can_handle(self, path: str, node: FileNode) -> bool:
        """Check if this generator should handle the given file.
        
        Args:
            path: Path to the file
            node: FileNode object representing the file
            
        Returns:
            bool: True if this generator can handle the file
        """
        ext = os.path.splitext(path)[1].lower()
        return ext in SUPPORTED_EXTENSIONS
    
    def get_overlay_files(self) -> List[OverlayFile]:
        """Get list of overlay files needed for this generator.
        
        Returns:
            List[OverlayFile]: Empty list as no overlay files are needed
        """
        return []
    
    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> Optional[bytes]:
        """Generate an image using DALL-E.
        
        Args:
            path: Path to generate the image at
            node: FileNode object representing the file
            fs_structure: Current filesystem structure
            
        Returns:
            Optional[bytes]: Generated image data or None on error
        """
        # Only return existing content if it's valid image data
        if node and node.content:
            validation = validate_image_data(node.content)
            if validation.is_valid:
                return node.content
            self.logger.warning(f"Existing content for {path} is not valid image data: {validation.error}")

        try:
            self.logger.info(f"""image_generation:
  status: started
  path: {path}
  operation: generate""")

            if not self.client:
                self.logger.error("OpenAI client not initialized")
                return None

            # Check cache first
            cached = get_cached_image(path, fs_structure)
            if cached:
                self.logger.info(f"""image_generation:
  status: completed
  path: {path}
  operation: cache_hit
  size: {len(cached)} bytes""")
                return cached

            # Generate prompt
            prompt_result = generate_prompt(self.client, path, fs_structure)
            
            # Generate image
            config = ImageGenerationConfig(
                model="dall-e-3",
                size="1024x1024",
                quality="standard"
            )
            
            result = generate_image(
                client=self.client,
                prompt=prompt_result.summarized_prompt,
                path=path,
                config=config
            )
            
            if result.error:
                self.logger.error(result.error)
                return None
                
            # Cache the result
            cache_image(path, fs_structure, result.content)
            
            self.logger.info(f"""image_generation:
  status: completed
  path: {path}
  operation: generated
  size: {len(result.content)} bytes""")
            
            return result.content
            
        except Exception as e:
            self.logger.error(f"""image_generation:
  status: failed
  path: {path}
  error: {str(e)}""")
            return None
