"""Plugin that handles prompt configuration files (.llmfs.prompt and .prompt)."""
from typing import List
import logging
from pydantic import BaseModel
from .proc import ProcPlugin
from .base import OverlayFile
from ...models.filesystem import FileNode
from ...config.settings import get_global_prompt, set_global_prompt, find_nearest_prompt_file

logger = logging.getLogger("llmfs")

class PromptConfig(BaseModel):
    prompt: str = get_global_prompt()  # Use current prompt as default

class PromptPlugin(ProcPlugin):
    """Plugin that handles prompt configuration files (.llmfs.prompt and .prompt)."""
    
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
        # Try to find nearest prompt file
        nearest_prompt_path = find_nearest_prompt_file(path, fs_structure)
        if nearest_prompt_path and nearest_prompt_path != path:  # Avoid self-reference
            nearest_node = fs_structure.get(nearest_prompt_path)
            if nearest_node and nearest_node.content:
                try:
                    config = PromptConfig.model_validate_json(nearest_node.content)
                    prompt = config.prompt
                    logger.debug(f"Using prompt from nearest file: {nearest_prompt_path}")
                except:
                    prompt = nearest_node.content.strip()
                    logger.debug(f"Using raw prompt from nearest file: {nearest_prompt_path}")
                set_global_prompt(prompt)
                return prompt + "\n"
        
        # Fall back to node content if available
        if node.content:
            try:
                config = PromptConfig.model_validate_json(node.content)
                prompt = config.prompt
                logger.debug("Parsed prompt from JSON")
            except:
                prompt = node.content.strip()
                logger.debug("Using raw prompt input")
            set_global_prompt(prompt)
            return prompt + "\n"
            
        # Fall back to global default
        logger.debug("Using default prompt template")
        return get_global_prompt() + "\n"
