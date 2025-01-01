"""Prompt configuration and management."""
import os
import logging
from typing import Optional
from . import templates

logger = logging.getLogger("touchfs")

# Global prompt state
_last_final_prompt = ""  # Last complete prompt sent to LLM
_filesystem_prompt = ""  # Last filesystem generation prompt used

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
    """Get content generation prompt from command line, environment, or template.
    
    The prompt is retrieved in the following order of precedence:
    1. Command line argument (if provided)
    2. TOUCHFS_PROMPT environment variable
    3. CONTENT_GENERATION_SYSTEM_PROMPT_TEMPLATE
    
    Args:
        prompt_arg: Optional command line argument for prompt
        
    Returns:
        The prompt string to use
    """
    # Try command line argument first
    if prompt_arg:
        return prompt_arg

    # Try environment variable
    prompt = os.getenv("TOUCHFS_PROMPT")
    if prompt:
        return prompt

    # Fall back to template
    try:
        return templates.read_template(templates.CONTENT_GENERATION_SYSTEM_PROMPT_TEMPLATE)
    except Exception as e:
        logger.error(f"Failed to read content generation template: {e}")
        raise

def get_filesystem_generation_prompt(prompt_arg: Optional[str] = None) -> Optional[str]:
    """Get filesystem generation prompt from command line or environment.
    
    The prompt is retrieved in the following order of precedence:
    1. Command line argument (if provided)
    2. TOUCHFS_FILESYSTEM_GENERATION_PROMPT environment variable
    
    If no prompt is provided through either method, returns None.
    
    Args:
        prompt_arg: Optional command line argument for prompt
        
    Returns:
        The prompt string to use, or None if no prompt provided
    """
    # Try command line argument first
    if prompt_arg:
        return prompt_arg

    # Try environment variable
    prompt = os.getenv("TOUCHFS_FILESYSTEM_GENERATION_PROMPT")
    if prompt:
        return prompt

    # Return None if no prompt provided
    return None

def get_last_final_prompt() -> str:
    """Get last complete prompt sent to LLM.
    
    Returns:
        str: Last final prompt or empty string if none
    """
    return _last_final_prompt

def set_last_final_prompt(prompt: str):
    """Update last complete prompt sent to LLM.
    
    Args:
        prompt: New final prompt
    """
    global _last_final_prompt
    logger.info(f"""prompt_operation:
  action: set_last_final
  status: success
  length: {len(prompt)}""")
    _last_final_prompt = prompt

def get_current_filesystem_prompt() -> str:
    """Get last filesystem generation prompt used.
    
    Returns:
        str: Last filesystem prompt or empty string if none
    """
    return _filesystem_prompt

def set_current_filesystem_prompt(prompt: str):
    """Update last filesystem generation prompt used.
    
    Args:
        prompt: New filesystem prompt
    """
    global _filesystem_prompt
    logger.info(f"""prompt_operation:
  action: set_filesystem
  status: success
  length: {len(prompt)}""")
    _filesystem_prompt = prompt

def get_global_prompt(prompt_arg: Optional[str] = None) -> str:
    """Get global prompt from command line or environment.
    
    The prompt is retrieved in the following order of precedence:
    1. Command line argument (if provided)
    2. TOUCHFS_GLOBAL_PROMPT environment variable
    3. Default empty string
    
    Args:
        prompt_arg: Optional command line argument for prompt
        
    Returns:
        The global prompt string to use
    """
    # Try command line argument first
    if prompt_arg:
        return prompt_arg

    # Try environment variable
    prompt = os.getenv("TOUCHFS_GLOBAL_PROMPT")
    if prompt:
        return prompt

    # Return empty string if no prompt provided
    return ""
