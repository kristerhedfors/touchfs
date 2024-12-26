"""Default content generator using OpenAI."""
import os
import json
import logging
from typing import Dict, Optional
from openai import OpenAI
from ...models.filesystem import FileNode, GeneratedContent
from ...config.logger import setup_logging
from ...config.settings import get_model
from .base import BaseContentGenerator

def get_openai_client() -> OpenAI:
    """Initialize OpenAI client with API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    return OpenAI()

class DefaultGenerator(BaseContentGenerator):
    """Default generator that uses OpenAI to generate file content."""
    
    def generator_name(self) -> str:
        return "default"
        
    def can_handle(self, path: str, node: FileNode) -> bool:
        """Handle any file that doesn't have a specific generator assigned."""
        return (node.xattrs is None or 
                "generator" not in node.xattrs or 
                node.xattrs.get("generator") == self.generator_name())
    
    def _find_nearest_prompt(self, path: str, fs_structure: Dict[str, FileNode]) -> Optional[str]:
        """Find the nearest .llmfs/prompt.default file by traversing up the directory tree.
        
        Args:
            path: Current file path
            fs_structure: Current filesystem structure
            
        Returns:
            Content of the nearest prompt.default file, or None if not found
        """
        current_dir = os.path.dirname(path)
        
        while True:
            prompt_path = os.path.join(current_dir, '.llmfs/prompt.default')
            if prompt_path in fs_structure:
                node = fs_structure[prompt_path]
                if node.content is not None:
                    return node.content
            
            # Move up one directory
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:  # Reached root
                break
            current_dir = parent_dir
            
        return None

    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        """Generate content using OpenAI."""
        logger = logging.getLogger("llmfs")
        logger.debug(f"Starting OpenAI content generation for path: {path}")
        
        try:
            client = get_openai_client()
            logger.debug("OpenAI client initialized successfully")
            
            # Try to find a custom prompt file
            custom_prompt = self._find_nearest_prompt(path, fs_structure)
            
            # Use custom prompt if found, otherwise use root prompt.default
            system_prompt = custom_prompt if custom_prompt else fs_structure["/.llmfs/prompt.default"].content

            logger.debug(f"Sending request to OpenAI API for path: {path}")
            logger.debug(f"System prompt: {system_prompt}")
            
            try:
                logger.debug("Using parse method with GeneratedContent model")
                model = get_model()
                logger.debug(f"Using model: {model}")
                completion = client.beta.chat.completions.parse(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Generate content for {path} based on its context in the filesystem"}
                    ],
                    response_format=GeneratedContent,
                    temperature=0.2
                )
                logger.debug("Successfully received parsed response from OpenAI API")
                content = completion.choices[0].message.parsed.content
                logger.debug(f"Generated content length: {len(content)}")
                return content
            except Exception as api_error:
                logger.error(f"OpenAI API error: {str(api_error)}", exc_info=True)
                raise
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to generate content: {e}")
