"""Generator for filesystem lists using structured outputs."""

from typing import Optional
from openai import OpenAI
from pydantic import BaseModel
from ..models.filesystem_list import FilesystemList
from ..config.logger import setup_logging

class FilesystemResponse(BaseModel):
    files: list[str]

def generate_filesystem_list(prompt: str, client: Optional[OpenAI] = None) -> FilesystemList:
    """Generate a list of files from a prompt using structured output.
    
    Args:
        prompt: The prompt describing what files to create
        client: Optional OpenAI client to use
        
    Returns:
        FilesystemList containing paths to create
    """
    logger = setup_logging(command_name="generate")
    
    if client is None:
        client = OpenAI()
    
    logger.debug("Generating filesystem list with prompt: %s", prompt)
    
    # Create system prompt that explains the task
    system_prompt = """You are a filesystem generator. Given a prompt, generate a list of files that should exist.
    
    Rules:
    1. All paths should be relative to the project root
    2. Use forward slashes (/) for path separators
    3. Include all necessary files for the project
    4. Directories will be created automatically from file paths
    5. Do not include empty directories (they are created implicitly)
    6. Use standard naming conventions for the project type

    File Types and Suffixes:
    The system handles different file types based on their suffixes:
    - .py: Python files with related Python files from same directory
    - .js/.ts: JavaScript/TypeScript files and package.json
    - .json: Related configuration files
    - .md: Related documentation files
    - .html/.css: Related web files and assets
    - Others: Files with the same extension in the directory
    
    Consider these file type relationships when generating the filesystem structure to ensure proper organization and dependencies.
    """
    
    # Call the API with structured output
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        response_format=FilesystemResponse
    )
    
    # Convert to FilesystemList
    result = FilesystemList(files=completion.choices[0].message.parsed.files)
    logger.debug("Generated filesystem list: %s", result)
    
    return result
