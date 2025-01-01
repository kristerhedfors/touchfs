"""Configuration settings and environment handling."""
import dotenv
import logging
from typing import Optional

from . import templates
from . import model
from . import prompts
from . import filesystem
from . import features

logger = logging.getLogger("touchfs")

# Load environment variables from .env file
dotenv.load_dotenv()

# Re-export all components
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
