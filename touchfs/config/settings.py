"""Configuration settings and environment handling."""
import os
import json
import dotenv
import logging
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger("touchfs")

import pkg_resources

# System prompt template constants
SYSTEM_PROMPT_EXTENSION = ".system_prompt"
CONTENT_GENERATION_SYSTEM_PROMPT_TEMPLATE = f"content_generation{SYSTEM_PROMPT_EXTENSION}"
FILESYSTEM_GENERATION_SYSTEM_PROMPT_TEMPLATE = f"filesystem_generation{SYSTEM_PROMPT_EXTENSION}"
FILESYSTEM_GENERATION_WITH_CONTEXT_SYSTEM_PROMPT_TEMPLATE = f"filesystem_generation_with_context{SYSTEM_PROMPT_EXTENSION}"
IMAGE_GENERATION_SYSTEM_PROMPT_TEMPLATE = f"image_generation{SYSTEM_PROMPT_EXTENSION}"

# Global configurations that can be updated at runtime
_current_model = "gpt-4o-2024-08-06"
_cache_enabled = True
_executive_enabled = False  # Executive plugin disabled by default
_last_final_prompt = ""  # Last complete prompt sent to LLM
_filesystem_prompt = ""  # Last filesystem generation prompt used

def _get_template_path(template_name: str) -> str:
    """Get the full path to a template file.
    
    Args:
        template_name: Name of the template file
        
    Returns:
        str: Full path to the template file
    """
    return pkg_resources.resource_filename('touchfs', f'templates/prompts/{template_name}')

def _read_template(template_name: str) -> str:
    """Read a template file from the templates directory.
    
    Args:
        template_name: Name of the template file
        
    Returns:
        str: Contents of the template file
        
    Raises:
        ValueError: If template file cannot be read
    """
    try:
        template_path = _get_template_path(template_name)
        with open(template_path, 'r') as f:
            return f.read().strip()
    except Exception as e:
        raise ValueError(f"Failed to read template {template_name}: {e}")

def _format_fs_structure(fs_structure: dict) -> str:
    """Format filesystem structure, excluding .touchfs folders."""
    # First convert all nodes to dicts
    dumped_structure = {p: n.model_dump() for p, n in fs_structure.items()}
    
    # Then filter out .touchfs paths - handle all possible path formats
    filtered_structure = {
        p: n for p, n in dumped_structure.items()
        if not any(p.endswith('.touchfs') or '.touchfs/' in p or p == '.touchfs')
    }
    
    return json.dumps(filtered_structure, indent=2)

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

def get_global_prompt() -> str:
    """Get current global prompt configuration.
    
    Returns:
        str: Current prompt template from CONTENT_GENERATION_SYSTEM_PROMPT_TEMPLATE
    """
    try:
        return _read_template(CONTENT_GENERATION_SYSTEM_PROMPT_TEMPLATE)
    except Exception as e:
        logger.error(f"Failed to read content generation template: {e}")
        raise

def set_global_prompt(prompt: str):
    """Update current global prompt configuration.
    
    Args:
        prompt: New prompt template to use
        
    Note: This is deprecated as prompts should come from template files
    """
    logger.warning("set_global_prompt is deprecated - prompts should come from template files")
    pass

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
        return _read_template(CONTENT_GENERATION_SYSTEM_PROMPT_TEMPLATE)
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

def set_filesystem_generation_prompt(prompt: str):
    """Update filesystem generation prompt configuration.
    
    Args:
        prompt: New prompt to use
        
    Note: This is deprecated as prompts should come from template files
    """
    logger.warning("set_filesystem_generation_prompt is deprecated - prompts should come from template files")
    pass

def find_nearest_prompt_file(path: str, fs_structure: dict) -> Optional[str]:
    """Find the nearest prompt file by traversing up the directory tree.
    
    Looks for files in this order at each directory level:
    1. .touchfs.prompt
    2. .prompt
    
    Args:
        path: Current file path
        fs_structure: Current filesystem structure
        
    Returns:
        Path to the nearest prompt file, or None if not found
    """
    logger.debug(f"Finding nearest prompt file for path: {path}")
    
    # Start with the directory containing our file
    current_dir = os.path.dirname(path)
    if current_dir == "":
        current_dir = "/"
    logger.debug(f"Starting in directory: {current_dir}")
    
    # First check in the current directory
    touchfs_prompt_path = os.path.join(current_dir, '.touchfs.prompt')
    prompt_path = os.path.join(current_dir, '.prompt')
    
    # Normalize paths (ensure single leading slash)
    touchfs_prompt_path = "/" + touchfs_prompt_path.lstrip("/")
    prompt_path = "/" + prompt_path.lstrip("/")
    
    logger.debug(f"Checking for prompt files in current dir: {current_dir}")
    if touchfs_prompt_path in fs_structure:
        logger.debug(f"Found .touchfs.prompt in current dir: {touchfs_prompt_path}")
        return touchfs_prompt_path
    if prompt_path in fs_structure:
        logger.debug(f"Found .prompt in current dir: {prompt_path}")
        return prompt_path
    
    # Then traverse up the directory tree using the filesystem structure
    while current_dir != "/":
        # Get parent directory from filesystem structure
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # Reached root
            break
            
        logger.debug(f"Moving to parent directory: {parent_dir}")
        
        # Check if parent exists and is a directory
        parent_node = fs_structure.get(parent_dir)
        if not parent_node:
            logger.debug(f"Parent directory {parent_dir} not found")
            break
            
        # Handle both dict and FileNode objects
        node_type = parent_node.get('type', '') if isinstance(parent_node, dict) else getattr(parent_node, 'type', '')
        if node_type != "directory":
            logger.debug(f"Parent directory {parent_dir} is not a directory")
            break
            
        # Check for prompt files in parent directory
        touchfs_prompt_path = os.path.join(parent_dir, '.touchfs.prompt')
        prompt_path = os.path.join(parent_dir, '.prompt')
        
        # Normalize paths
        touchfs_prompt_path = "/" + touchfs_prompt_path.lstrip("/")
        prompt_path = "/" + prompt_path.lstrip("/")
        
        if touchfs_prompt_path in fs_structure:
            logger.debug(f"Found .touchfs.prompt at: {touchfs_prompt_path}")
            return touchfs_prompt_path
        if prompt_path in fs_structure:
            logger.debug(f"Found .prompt at: {prompt_path}")
            return prompt_path
            
        current_dir = parent_dir
    
    # Finally check root if we haven't already
    if current_dir != "/":
        logger.debug("Checking root directory")
        if "/.touchfs.prompt" in fs_structure:
            logger.debug("Found .touchfs.prompt in root")
            return "/.touchfs.prompt"
        if "/.prompt" in fs_structure:
            logger.debug("Found .prompt in root")
            return "/.prompt"
    
    logger.debug("No prompt file found")
    return None

def find_nearest_model_file(path: str, fs_structure: dict) -> Optional[str]:
    """Find the nearest model file by traversing up the directory tree.
    
    Looks for files in this order at each directory level:
    1. .touchfs.model
    2. .model
    
    Args:
        path: Current file path (absolute FUSE path)
        fs_structure: Current filesystem structure
        
    Returns:
        Path to the nearest model file, or None if not found
    """
    logger.debug(f"Finding nearest model file for path: {path}")
    
    # Start with the directory containing our file
    current_dir = os.path.dirname(path)
    if current_dir == "":
        current_dir = "/"
    logger.debug(f"Starting in directory: {current_dir}")
    
    # First check in the current directory
    touchfs_model_path = os.path.join(current_dir, '.touchfs.model')
    model_path = os.path.join(current_dir, '.model')
    
    # Normalize paths (ensure single leading slash)
    touchfs_model_path = "/" + touchfs_model_path.lstrip("/")
    model_path = "/" + model_path.lstrip("/")
    
    logger.debug(f"Checking for model files in current dir: {current_dir}")
    if touchfs_model_path in fs_structure:
        logger.debug(f"Found .touchfs.model in current dir: {touchfs_model_path}")
        return touchfs_model_path
    if model_path in fs_structure:
        logger.debug(f"Found .model in current dir: {model_path}")
        return model_path
    
    # Then traverse up the directory tree using the filesystem structure
    while current_dir != "/":
        # Get parent directory from filesystem structure
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # Reached root
            break
            
        logger.debug(f"Moving to parent directory: {parent_dir}")
        
        # Check if parent exists and is a directory
        parent_node = fs_structure.get(parent_dir)
        if not parent_node:
            logger.debug(f"Parent directory {parent_dir} not found")
            break
            
        # Handle both dict and FileNode objects
        node_type = parent_node.get('type', '') if isinstance(parent_node, dict) else getattr(parent_node, 'type', '')
        if node_type != "directory":
            logger.debug(f"Parent directory {parent_dir} is not a directory")
            break
            
        # Check for model files in parent directory
        touchfs_model_path = os.path.join(parent_dir, '.touchfs.model')
        model_path = os.path.join(parent_dir, '.model')
        
        # Normalize paths
        touchfs_model_path = "/" + touchfs_model_path.lstrip("/")
        model_path = "/" + model_path.lstrip("/")
        
        if touchfs_model_path in fs_structure:
            logger.debug(f"Found .touchfs.model at: {touchfs_model_path}")
            return touchfs_model_path
        if model_path in fs_structure:
            logger.debug(f"Found .model at: {model_path}")
            return model_path
            
        current_dir = parent_dir
    
    # Finally check root if we haven't already
    if current_dir != "/":
        logger.debug("Checking root directory")
        if "/.touchfs.model" in fs_structure:
            logger.debug("Found .touchfs.model in root")
            return "/.touchfs.model"
        if "/.model" in fs_structure:
            logger.debug("Found .model in root")
            return "/.model"
    
    logger.debug("No model file found")
    return None

def get_executive_enabled() -> bool:
    """Get current executive plugin enabled state.
    
    Returns:
        bool: Whether executive plugin is enabled
    """
    return _executive_enabled

def set_executive_enabled(enabled: bool):
    """Update executive plugin enabled state.
    
    Args:
        enabled: Whether to enable executive plugin
    """
    global _executive_enabled
    logger.info(f"Setting executive plugin enabled to: {enabled}")
    _executive_enabled = enabled

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
