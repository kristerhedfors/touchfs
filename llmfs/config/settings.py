"""Configuration settings and environment handling."""
import os
import dotenv
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("llmfs")

# Global model configuration that can be updated at runtime
_current_model = "gpt-4o-2024-08-06"

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
    """Get prompt from environment, command line, or file.
    
    The prompt is retrieved in the following order of precedence:
    1. LLMFS_PROMPT environment variable
    2. Command line argument (if provided)
    3. File content (if argument is a file path)
    
    Args:
        prompt_arg: Optional command line argument for prompt or file path
        
    Returns:
        The prompt string to use
        
    Raises:
        ValueError: If no prompt could be found
    """
    # Try environment variable first
    prompt = os.getenv("LLMFS_PROMPT")
    if prompt:
        return prompt

    # Try command line argument
    if prompt_arg:
        # If it's a file path, read from file
        if os.path.isfile(prompt_arg):
            return read_prompt_file(prompt_arg)
        return prompt_arg

    raise ValueError(
        "Prompt must be provided via LLMFS_PROMPT environment variable, "
        "command line argument, or file"
    )

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
