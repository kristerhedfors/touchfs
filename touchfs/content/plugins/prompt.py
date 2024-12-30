"""Plugin that handles prompt configuration files (.touchfs.prompt and .prompt)."""
from typing import List
import logging
from pydantic import BaseModel
from .proc import ProcPlugin
from .base import OverlayFile
from ...models.filesystem import FileNode
from ...config.settings import get_global_prompt, find_nearest_prompt_file, _read_template

logger = logging.getLogger("touchfs")

class PromptConfig(BaseModel):
    """Model for parsing JSON prompt configurations."""
    prompt: str

class PromptPlugin(ProcPlugin):
    """Plugin that handles prompt configuration files (.touchfs.prompt and .prompt)."""
    
    def generator_name(self) -> str:
        return "prompt"
    
    def get_proc_path(self) -> str:
        """Return path for prompt.default file."""
        return "prompt.default"
        
    def generate(self, path: str, node: FileNode, fs_structure: dict) -> str:
        """Return the prompt content and update global config.
        
        First checks for nearest prompt file in the directory hierarchy,
        then falls back to node content or global default.
        """
        # First check if this is a prompt file being read
        if node.content:
            try:
                # Try to parse as JSON first
                config = PromptConfig.model_validate_json(node.content)
                prompt = config.prompt
                logger.debug("prompt_source: json")
            except:
                # Fall back to raw content
                prompt = node.content.strip()
                logger.debug("prompt_source: raw")
            return prompt + "\n"
            
        # If not a prompt file, try to find nearest prompt file
        nearest_prompt_path = find_nearest_prompt_file(path, fs_structure)
        if nearest_prompt_path and nearest_prompt_path != path:  # Avoid self-reference
            nearest_node = fs_structure.get(nearest_prompt_path)
            if nearest_node and nearest_node.content:
                try:
                    config = PromptConfig.model_validate_json(nearest_node.content)
                    prompt = config.prompt
                    logger.debug(f"""prompt_source: nearest_file
path: {nearest_prompt_path}
format: json""")
                except:
                    prompt = nearest_node.content.strip()
                    logger.debug(f"""prompt_source: nearest_file
path: {nearest_prompt_path}
format: raw""")
                return prompt + "\n"
            
        # Fall back to template
        logger.debug("prompt_source: default_template")
        return get_global_prompt() + "\n"
