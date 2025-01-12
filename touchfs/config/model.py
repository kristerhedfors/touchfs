"""Model configuration and management."""
import logging
import os
import json
from typing import Optional, Dict, Any

logger = logging.getLogger("touchfs")

# Global model configuration
_current_model = "gpt-4o-2024-08-06"
_overlay_path = None

def set_overlay_path(path: Optional[str]) -> None:
    """Set the overlay path for finding model configuration files.
    
    Args:
        path: Path to overlay directory, or None to clear
    """
    global _overlay_path
    _overlay_path = path
    logger.debug(f"Set model overlay path to: {path}")

def _read_model_file(path: str) -> Optional[str]:
    """Read model configuration from a file.
    
    Args:
        path: Path to model configuration file
        
    Returns:
        Model configuration if file exists and is valid, None otherwise
    """
    try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                content = f.read().strip()
                # Try parsing as JSON first
                try:
                    config = json.loads(content)
                    if isinstance(config, dict) and "model" in config:
                        return config["model"]
                except json.JSONDecodeError:
                    # Not JSON, treat as plain model name
                    return content
    except Exception as e:
        logger.debug(f"Error reading model file {path}: {e}")
    return None

def get_model() -> str:
    """Get current model configuration.
    
    Checks in the following order:
    1. Environment variable TOUCHFS_DEFAULT_MODEL
    2. .model file in current directory
    3. .touchfs/model_default in current directory
    4. Same files in overlay path if set
    5. Default model (gpt-4o-2024-08-06)
    
    Returns:
        str: Current model name
    """
    # Check environment first
    if env_model := os.getenv("TOUCHFS_DEFAULT_MODEL"):
        return env_model.strip()
        
    # Check current directory first
    if model := _read_model_file(".model"):
        return model
    if model := _read_model_file(os.path.join(".touchfs", "model_default")):
        return model
        
    # Check overlay path if set
    if _overlay_path:
        # Check .model in overlay
        if model := _read_model_file(os.path.join(_overlay_path, ".model")):
            return model
        # Check .touchfs/model_default in overlay
        if model := _read_model_file(os.path.join(_overlay_path, ".touchfs", "model_default")):
            return model
            
    # Return default if no configuration found
    return _current_model

def set_model(model: str) -> None:
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
