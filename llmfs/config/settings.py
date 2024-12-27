"""Configuration settings and environment handling."""
import os
import json
import dotenv
import logging
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger("llmfs")

# Global configurations that can be updated at runtime
_current_model = "gpt-4o-2024-08-06"
_current_filesystem_generation_prompt = "Create an empty filesystem"
_cache_enabled = True

def _format_fs_structure(fs_structure: dict) -> str:
    """Format filesystem structure, excluding .llmfs folders."""
    # First convert all nodes to dicts
    dumped_structure = {p: n.model_dump() for p, n in fs_structure.items()}
    
    # Then filter out .llmfs paths - handle all possible path formats
    filtered_structure = {
        p: n for p, n in dumped_structure.items()
        if not any(p.endswith('.llmfs') or '.llmfs/' in p or p == '.llmfs')
    }
    
    return json.dumps(filtered_structure, indent=2)

# Global prompt configuration that can be updated at runtime
_current_prompt = """Generate appropriate content for the file {path}.
The file exists within this filesystem structure:
{_format_fs_structure(fs_structure)}

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

def get_model() -> str:
    """Get current model configuration.
    
    Returns:
        str: Current model name
    """
    return _current_model

def set_model(model: str):
    """Update current model configuration.
    
    Args:
        model: New model name to use
    """
    global _current_model
    logger.info(f"Setting model to: {model}")
    _current_model = model

def get_global_prompt() -> str:
    """Get current global prompt configuration.
    
    Returns:
        str: Current prompt template
    """
    return _current_prompt

def set_global_prompt(prompt: str):
    """Update current global prompt configuration.
    
    Args:
        prompt: New prompt template to use
    """
    global _current_prompt
    logger.info("Setting new prompt template")
    _current_prompt = prompt

# Load environment variables from .env file
dotenv.load_dotenv()

def read_prompt_file(path: str) -> str:
    """Read prompt from a file.
    
    Args:
        path: Path to the prompt file
        
    Returns:
        Contents of the prompt file
        
    Raises:
        ValueError: If file cannot be read
    """
    try:
        with open(path, 'r') as f:
            return f.read().strip()
    except Exception as e:
        raise ValueError(f"Failed to read prompt file: {e}")

def get_prompt(prompt_arg: Optional[str] = None) -> str:
    """Get content generation prompt from command line or environment.
    
    The prompt is retrieved in the following order of precedence:
    1. Command line argument (if provided)
    2. LLMFS_PROMPT environment variable
    3. Default prompt template
    
    Args:
        prompt_arg: Optional command line argument for prompt
        
    Returns:
        The prompt string to use
    """
    # Try command line argument first
    if prompt_arg:
        return prompt_arg

    # Try environment variable
    prompt = os.getenv("LLMFS_PROMPT")
    if prompt:
        return prompt

    # Fall back to default template
    return _current_prompt

def get_filesystem_generation_prompt(prompt_arg: Optional[str] = None) -> str:
    """Get filesystem generation prompt from command line or environment.
    
    The prompt is retrieved in the following order of precedence:
    1. Command line argument (if provided)
    2. LLMFS_FILESYSTEM_GENERATION_PROMPT environment variable
    3. Default empty filesystem
    
    Args:
        prompt_arg: Optional command line argument for prompt
        
    Returns:
        The prompt string to use
    """
    # Try command line argument first
    if prompt_arg:
        return prompt_arg

    # Try environment variable
    prompt = os.getenv("LLMFS_FILESYSTEM_GENERATION_PROMPT")
    if prompt:
        return prompt

    # Fall back to default
    return _current_filesystem_generation_prompt

def set_filesystem_generation_prompt(prompt: str):
    """Update current filesystem generation prompt configuration.
    
    Args:
        prompt: New prompt to use
    """
    global _current_filesystem_generation_prompt
    logger.info(f"Setting filesystem generation prompt to: {prompt}")
    _current_filesystem_generation_prompt = prompt

def find_nearest_prompt_file(path: str, fs_structure: dict) -> Optional[str]:
    """Find the nearest prompt file by traversing up the directory tree.
    
    Looks for files in this order at each directory level:
    1. .llmfs/prompt
    2. .llmfs/prompt.default
    
    Args:
        path: Current file path
        fs_structure: Current filesystem structure
        
    Returns:
        Path to the nearest prompt file, or None if not found
    """
    current_dir = os.path.dirname(path)
    while True:
        # Check for prompt file
        prompt_path = os.path.join(current_dir, '.llmfs/prompt')
        if prompt_path in fs_structure:
            return prompt_path
        
        # Check for prompt.default
        default_path = os.path.join(current_dir, '.llmfs/prompt.default')
        if default_path in fs_structure:
            return default_path
        
        # Move up one directory
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # Reached root
            break
        current_dir = parent_dir
    return None

def get_cache_enabled() -> bool:
    """Get current cache enabled state.
    
    Returns:
        bool: Whether caching is enabled
    """
    return _cache_enabled

def set_cache_enabled(enabled: bool):
    """Update cache enabled state.
    
    Args:
        enabled: Whether to enable caching
    """
    global _cache_enabled
    logger.info(f"Setting cache enabled to: {enabled}")
    _cache_enabled = enabled

def get_openai_key() -> str:
    """Get OpenAI API key from environment.
    
    Returns:
        OpenAI API key
        
    Raises:
        ValueError: If API key is not set
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    return api_key
