"""Default content generator using OpenAI."""
import os
import json
from typing import Dict
from openai import OpenAI
from ...models.filesystem import FileNode, GeneratedContent
from ...config.logger import setup_logging
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
    
    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        """Generate content using OpenAI."""
        logger = setup_logging(debug=True)
        logger.debug(f"Starting OpenAI content generation for path: {path}")
        
        try:
            client = get_openai_client()
            logger.debug("OpenAI client initialized successfully")
            
            system_prompt = f"""Generate appropriate content for the file {path}.
The file exists within this filesystem structure:
{json.dumps({p: n.model_dump() for p, n in fs_structure.items()}, indent=2)}

Consider:
1. The file's location and name to determine its purpose
2. Its relationship to other files and directories
3. Follow appropriate best practices for the file type
4. Generate complete, working code that would make sense in this context

For Python files:
- If it's a module's main implementation file (like operations.py), include relevant classes and functions
- If it's a test file, include proper test cases using pytest
- If it's __init__.py, include appropriate imports and exports
- Include docstrings and type hints
- Ensure the code is complete and properly structured

For shell scripts:
- Include proper shebang line
- Add error handling and logging
- Make the script robust and reusable

Keep the content focused and production-ready."""

            logger.debug(f"Sending request to OpenAI API for path: {path}")
            logger.debug(f"System prompt: {system_prompt}")
            
            try:
                logger.debug("Using parse method with GeneratedContent model")
                completion = client.beta.chat.completions.parse(
                    model="gpt-4o-2024-08-06",
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
