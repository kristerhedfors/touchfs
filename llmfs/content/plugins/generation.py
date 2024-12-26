"""Plugin that provides generation configuration files in .llmfs."""
from typing import List
from pydantic import BaseModel
from .proc import ProcPlugin
from .base import OverlayFile
from ...models.filesystem import FileNode

class GenerationConfig(BaseModel):
    model: str = "gpt-4o-2024-08-06"

class GenerationModelPlugin(ProcPlugin):
    """Plugin that provides the generation.model file in .llmfs."""
    
    def generator_name(self) -> str:
        return "generation_model"
    
    def get_proc_path(self) -> str:
        """Return path for generation.model file."""
        return "generation.model"
        
    def generate(self, path: str, node: FileNode, fs_structure: dict) -> str:
        """Return the model configuration content."""
        if node.content:
            # Parse and validate input
            config = GenerationConfig.model_validate_json(node.content)
            return config.model
        return GenerationConfig().model
