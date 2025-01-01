"""Model configuration and management."""
import logging
import os
from typing import Optional

logger = logging.getLogger("touchfs")

# Global model configuration
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
    # Always strip content when setting model
    stripped = model.strip()
    # Assert content is clean
    if stripped != stripped.strip():
        raise ValueError("Model content contains embedded newlines or extra whitespace")
    logger.info(f"Setting model to: {stripped}")
    _current_model = stripped

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
