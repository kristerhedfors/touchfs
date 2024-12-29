"""Default content generator using OpenAI."""
import os
import json
import logging
from typing import Dict, Optional
from openai import OpenAI
from ...models.filesystem import FileNode, GeneratedContent
from ...config.logger import setup_logging
from ...config.settings import get_model, get_global_prompt, find_nearest_model_file, find_nearest_prompt_file
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
                
    def get_prompt(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        """Get the prompt that would be used for generation."""
        # Find nearest prompt file
        nearest_prompt_path = find_nearest_prompt_file(path, fs_structure)
        if nearest_prompt_path:
            nearest_node = fs_structure.get(nearest_prompt_path)
            if nearest_node and nearest_node.content:
                return nearest_node.content.strip()
        return get_global_prompt()
    
    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        """Generate content using OpenAI."""
        logger = logging.getLogger("llmfs")
        logger.debug(f"Starting OpenAI content generation for path: {path}")
        
        try:
            client = get_openai_client()
            logger.debug("OpenAI client initialized successfully")
            
            # Try to find nearest prompt file
            nearest_prompt_path = find_nearest_prompt_file(path, fs_structure)
            if nearest_prompt_path:
                nearest_node = fs_structure.get(nearest_prompt_path)
                if nearest_node and nearest_node.content:
                    system_prompt = nearest_node.content.strip()
                    logger.debug(f"Using prompt from nearest file: {nearest_prompt_path}")
                else:
                    system_prompt = get_global_prompt()
                    logger.debug("Using global prompt (nearest file empty)")
            else:
                system_prompt = get_global_prompt()
                logger.debug("Using global prompt (no nearest file)")

            # Try to find nearest model file
            nearest_model_path = find_nearest_model_file(path, fs_structure)
            if nearest_model_path:
                nearest_node = fs_structure.get(nearest_model_path)
                if nearest_node and nearest_node.content:
                    model = nearest_node.content.strip()
                    logger.debug(f"Using model from nearest file: {nearest_model_path}")
                else:
                    model = get_model()
                    logger.debug("Using global model (nearest file empty)")
            else:
                model = get_model()
                logger.debug("Using global model (no nearest file)")

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
