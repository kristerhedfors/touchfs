"""Configuration settings and environment handling."""
import os
import dotenv
import logging
from typing import Optional

from . import templates
from . import model
from . import prompts
from . import filesystem
from . import features
from . import context
from . import xattrs

logger = logging.getLogger("touchfs")

# Export xattr definitions
TOUCHFS_PREFIX = xattrs.TOUCHFS_PREFIX
GENERATE_CONTENT_XATTR = xattrs.GENERATE_CONTENT
GENERATOR_XATTR = xattrs.GENERATOR
CLI_CONTEXT_XATTR = xattrs.CLI_CONTEXT

# Load environment variables from .env file
dotenv.load_dotenv()

# Re-export all components
# Context settings
DEFAULT_MAX_TOKENS = 8000  # Maximum number of tokens for context generation

# File extensions to include when building context for content generation.
# This controls which files will be included in the context during the generation phase.
# Note: This is only used for context building - when generating new files, we are more
# permissive with extensions since they are not formally specified and it's not too
# expensive to attempt generation and see if it sticks.
DEFAULT_TEXT_EXTENSIONS = {
    '.txt',   # Plain text files
    '.md',    # Markdown
    '.py',    # Python
    '.js',    # JavaScript
    '.css',   # CSS
    '.html',  # HTML
    '.json',  # JSON
    '.yml',   # YAML
    '.yaml',  # YAML (alternate)
    '.ini',   # INI config
    '.conf'   # Config files
}

# Template management
SYSTEM_PROMPT_EXTENSION = templates.SYSTEM_PROMPT_EXTENSION
CONTENT_GENERATION_SYSTEM_PROMPT_TEMPLATE = templates.CONTENT_GENERATION_SYSTEM_PROMPT_TEMPLATE
FILESYSTEM_GENERATION_SYSTEM_PROMPT_TEMPLATE = templates.FILESYSTEM_GENERATION_SYSTEM_PROMPT_TEMPLATE
FILESYSTEM_GENERATION_WITH_CONTEXT_SYSTEM_PROMPT_TEMPLATE = templates.FILESYSTEM_GENERATION_WITH_CONTEXT_SYSTEM_PROMPT_TEMPLATE
IMAGE_GENERATION_SYSTEM_PROMPT_TEMPLATE = templates.IMAGE_GENERATION_SYSTEM_PROMPT_TEMPLATE
read_template = templates.read_template
get_template_path = templates.get_template_path

# Model management
get_model = model.get_model
set_model = model.set_model
get_openai_key = model.get_openai_key

# Prompt management
read_prompt_file = prompts.read_prompt_file
get_prompt = prompts.get_prompt
get_filesystem_generation_prompt = prompts.get_filesystem_generation_prompt
get_last_final_prompt = prompts.get_last_final_prompt
set_last_final_prompt = prompts.set_last_final_prompt
get_current_filesystem_prompt = prompts.get_current_filesystem_prompt
set_current_filesystem_prompt = prompts.set_current_filesystem_prompt
get_global_prompt = prompts.get_global_prompt

# Filesystem utilities
find_nearest_prompt_file = filesystem.find_nearest_prompt_file
find_nearest_model_file = filesystem.find_nearest_model_file
format_fs_structure = filesystem.format_fs_structure

# Feature flags
get_cache_enabled = features.get_cache_enabled
set_cache_enabled = features.set_cache_enabled

# Filesystem settings
DEFAULT_FSNAME = "touchfs"  # Default name used to identify TouchFS mounts

def get_fsname() -> str:
    """Get the filesystem name used to identify TouchFS mounts.
    
    Can be overridden by TOUCHFS_FSNAME environment variable.
    
    Returns:
        Filesystem name to use for mounting
    """
    return os.environ.get('TOUCHFS_FSNAME', DEFAULT_FSNAME)
