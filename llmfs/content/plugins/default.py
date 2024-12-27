"""Default content generator using OpenAI."""
import os
import json
import logging
from typing import Dict, Optional
from openai import OpenAI
from ...models.filesystem import FileNode, GeneratedContent
from ...config.logger import setup_logging
from ...config.settings import get_model, get_global_prompt
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
    
    def _find_nearest_file(self, path: str, fs_structure: Dict[str, FileNode], base_name: str) -> Optional[str]:
        """Find the nearest file by traversing up the directory tree.
        
        Looks for files in this order at each directory level:
        1. .llmfs/<base_name>
        2. .llmfs/<base_name>.default
        
        Args:
            path: Current file path
            fs_structure: Current filesystem structure
            base_name: Base name of file to look for (e.g., 'prompt' or 'model')
            
        Returns:
            Content of the nearest file, or None if not found
        """
        logger = logging.getLogger("llmfs")
        current_dir = os.path.dirname(path)
        logger.debug(f"Starting {base_name} lookup from directory: {current_dir}")
        
        while True:
            # Check for base file first
            file_path = os.path.join(current_dir, f'.llmfs/{base_name}')
            if file_path in fs_structure:
                node = fs_structure[file_path]
                if node.content:  # Will be falsy for None or empty string
                    logger.debug(f"Found {base_name} at: {file_path}")
                    return node.content
                logger.debug(f"Empty {base_name} at: {file_path}, continuing search")
            
            # Then check for .default
            default_path = os.path.join(current_dir, f'.llmfs/{base_name}.default')
            if default_path in fs_structure:
                node = fs_structure[default_path]
                if node.content:  # Will be falsy for None or empty string
                    logger.debug(f"Found {base_name}.default at: {default_path}")
                    return node.content
                logger.debug(f"Empty {base_name}.default at: {default_path}, continuing search")
            
            # Move up one directory
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:  # Reached root
                logger.debug(f"Reached filesystem root, ending {base_name} lookup")
                break
            current_dir = parent_dir
            logger.debug(f"Moving up to directory: {current_dir}")
        
        logger.debug(f"No {base_name} files found in directory hierarchy")
        return None

    def _find_nearest_prompt(self, path: str, fs_structure: Dict[str, FileNode]) -> Optional[str]:
        """Find the nearest prompt file by traversing up the directory tree."""
        return self._find_nearest_file(path, fs_structure, "prompt")

    def _find_nearest_model(self, path: str, fs_structure: Dict[str, FileNode]) -> Optional[str]:
        """Find the nearest model file by traversing up the directory tree."""
        return self._find_nearest_file(path, fs_structure, "model")

    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        """Generate content using OpenAI."""
        logger = logging.getLogger("llmfs")
        logger.debug(f"Starting OpenAI content generation for path: {path}")
        
        try:
            client = get_openai_client()
            logger.debug("OpenAI client initialized successfully")
            
            # Try to find custom files
            custom_prompt = self._find_nearest_prompt(path, fs_structure)
            custom_model = self._find_nearest_model(path, fs_structure)
            
            # Use custom values if found, otherwise use global values
            system_prompt = custom_prompt if custom_prompt else get_global_prompt()
            model = custom_model if custom_model else get_model()

            logger.debug(f"Sending request to OpenAI API for path: {path}")
            # Construct messages with resolved content
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"""Generate unique content for file {path}.

Current filesystem context:
{json.dumps({p: n.model_dump() for p, n in fs_structure.items()}, indent=2)}

Requirements:
1. Content must be unique to this specific file path
2. Content should be appropriate for the file's name and location
3. Content must be different from any other files in the same directory
4. Content should be consistent with the overall filesystem structure
5. Content should follow standard conventions for the file type

Generate content that fulfills these requirements and is specific to {path}."""}
            ]
            
            # Log the actual messages being sent
            logger.debug("Messages being sent to OpenAI:")
            for msg in messages:
                logger.debug(f"{msg['role'].upper()}: {msg['content']}")
            logger.debug(f"Using model: {model}")
            
            try:
                logger.debug("Using parse method with GeneratedContent model")
                completion = client.beta.chat.completions.parse(
                    model=model,
                    messages=messages,
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
