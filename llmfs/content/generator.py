"""Content generation using OpenAI's API."""
import os
import json
from openai import OpenAI
from ..models.filesystem import FileSystem, GeneratedContent
from ..config.logger import setup_logging

def get_openai_client() -> OpenAI:
    """Initialize OpenAI client with API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    return OpenAI()

def generate_filesystem(prompt: str) -> dict:
    """Generate filesystem structure using OpenAI.
    
    Args:
        prompt: User prompt describing desired filesystem structure
        
    Returns:
        Dict containing the generated filesystem structure
        
    Raises:
        RuntimeError: If filesystem generation fails
    """
    client = get_openai_client()
    
    system_prompt = """
    You are a filesystem generator. Given a prompt, generate a JSON structure representing a filesystem.
    The filesystem must follow this exact structure:
    {
      "data": {
        "/": {
          "type": "directory",
          "children": {
            "example": "/example",
            "test": "/test"
          },
          "attrs": {
            "st_mode": "16877",  # directory with 755 permissions
            "st_size": "0"
          }
        },
        "/example": {
          "type": "directory",
          "children": {},
          "attrs": {
            "st_mode": "16877",
            "st_size": "0"
          }
        },
        "/test": {
          "type": "file",
          "content": null,  # Content will be generated on first read
          "attrs": {
            "st_mode": "33188",  # regular file with 644 permissions
            "st_size": "0"
          }
        }
      }
    }

    Rules:
    1. The response must have a top-level "data" field containing the filesystem structure
    2. Each node must have a "type" ("file", "directory", or "symlink")
    3. Each node must have "attrs" with st_mode and st_size
    4. For files:
       - Set content to null initially (it will be generated on first read)
       - Use st_mode "33188" for regular files (644 permissions)
    5. For directories:
       - Must have "children" mapping names to absolute paths
       - Use st_mode "16877" for directories (755 permissions)
    6. For symlinks:
       - Must have "content" with the target path
       - Use st_mode "41471" for symlinks (777 permissions)
    7. All paths must be absolute and normalized
    8. Root directory ("/") must always exist
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        # Parse and validate the response
        fs_data = json.loads(completion.choices[0].message.content)
        FileSystem.model_validate(fs_data)
        return fs_data
    except Exception as e:
        raise RuntimeError(f"Failed to generate filesystem: {e}")

def generate_file_content(path: str, fs_structure: str) -> str:
    """Generate content for a file using OpenAI.
    
    Args:
        path: Path of the file to generate content for
        fs_structure: String representation of the entire filesystem structure
        
    Returns:
        Generated content for the file
        
    Raises:
        RuntimeError: If content generation fails
    """
    logger = setup_logging(debug=True)
    logger.debug(f"Starting content generation for path: {path}")
    try:
        client = get_openai_client()
        logger.debug("OpenAI client initialized successfully")
        system_prompt = f"""Generate appropriate Python code content for the file {path}.
The file exists within this filesystem structure:
{fs_structure}

Consider:
1. The file's location and name to determine its purpose
2. Its relationship to other files and directories
3. Follow Python best practices and PEP 8 style guide
4. Generate complete, working code that would make sense in this context

For Python files:
- If it's a module's main implementation file (like operations.py), include relevant classes and functions
- If it's a test file, include proper test cases using pytest
- If it's __init__.py, include appropriate imports and exports
- Include docstrings and type hints
- Ensure the code is complete and properly structured

Keep the code focused and production-ready."""

        logger.debug(f"Sending request to OpenAI API for path: {path}")
        logger.debug(f"System prompt: {system_prompt}")
        
        try:
            logger.debug("Using parse method with GeneratedContent model")
            completion = client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate Python code for {path} based on its context in the filesystem"}
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
