"""Plugin that provides the prompt.default file in .llmfs."""
from typing import List
import logging
from pydantic import BaseModel
from .proc import ProcPlugin
from .base import OverlayFile
from ...models.filesystem import FileNode
from ...config.settings import get_global_prompt, set_global_prompt

logger = logging.getLogger("llmfs")

class PromptConfig(BaseModel):
    prompt: str = get_global_prompt()  # Use current prompt as default

class PromptPlugin(ProcPlugin):
    """Plugin that provides the prompt.default file in .llmfs."""
    
    def generator_name(self) -> str:
        return "prompt"
    
    def get_proc_path(self) -> str:
        """Return path for prompt.default file."""
        return "prompt.default"
        
    def generate(self, path: str, node: FileNode, fs_structure: dict) -> str:
        """Return the prompt content and update global config."""
        prompt = get_global_prompt()  # Start with current prompt
        
        if node.content:
            # Parse and validate input
            try:
                # First try parsing as JSON
                config = PromptConfig.model_validate_json(node.content)
                prompt = config.prompt
                logger.debug("Parsed prompt from JSON")
            except:
                # If not JSON, treat as raw prompt text
                prompt = node.content.strip()
                logger.debug("Using raw prompt input")
        else:
            logger.debug("Using default prompt template")
        
        # Update global configuration
        set_global_prompt(prompt)
        return prompt + "\n"
