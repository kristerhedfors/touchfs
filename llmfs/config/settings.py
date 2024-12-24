"""Configuration settings and environment handling."""
import os
import dotenv
from pathlib import Path
from typing import Optional

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

def get_log_dir() -> str:
    """Get log directory path from environment or use default.
    
    Returns:
        Path to log directory
    """
    return os.getenv("LLMFS_LOG_DIR", "/var/log/llmfs")
