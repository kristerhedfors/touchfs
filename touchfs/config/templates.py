"""Template management and configuration."""
import pkg_resources
import logging
from typing import Optional

logger = logging.getLogger("touchfs")

# System prompt template constants
SYSTEM_PROMPT_EXTENSION = ".system_prompt"
CONTENT_GENERATION_SYSTEM_PROMPT_TEMPLATE = f"content_generation{SYSTEM_PROMPT_EXTENSION}"
FILESYSTEM_GENERATION_SYSTEM_PROMPT_TEMPLATE = f"filesystem_generation{SYSTEM_PROMPT_EXTENSION}"
FILESYSTEM_GENERATION_WITH_CONTEXT_SYSTEM_PROMPT_TEMPLATE = f"filesystem_generation_with_context{SYSTEM_PROMPT_EXTENSION}"
IMAGE_GENERATION_SYSTEM_PROMPT_TEMPLATE = f"image_generation{SYSTEM_PROMPT_EXTENSION}"
FILENAME_SUGGESTIONS_SYSTEM_PROMPT_TEMPLATE = f"filename_suggestions{SYSTEM_PROMPT_EXTENSION}"

def get_template_path(template_name: str) -> str:
    """Get the full path to a template file.
    
    Args:
        template_name: Name of the template file
        
    Returns:
        str: Full path to the template file
    """
    return pkg_resources.resource_filename('touchfs', f'templates/prompts/{template_name}')

def read_template(template_name: str) -> str:
    """Read a template file from the templates directory.
    
    Args:
        template_name: Name of the template file
        
    Returns:
        str: Contents of the template file
        
    Raises:
        ValueError: If template file cannot be read
    """
    try:
        template_path = get_template_path(template_name)
        with open(template_path, 'r') as f:
            return f.read().strip()
    except Exception as e:
        raise ValueError(f"Failed to read template {template_name}: {e}")
