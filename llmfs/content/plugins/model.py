"""Plugin that provides model configuration file in .llmfs."""
from typing import List
from pydantic import BaseModel
from .proc import ProcPlugin
from .base import OverlayFile
from ...models.filesystem import FileNode

class ModelConfig(BaseModel):
    model: str = "gpt-4o-2024-08-06"

class ModelPlugin(ProcPlugin):
    """Plugin that provides the model.default file in .llmfs."""
    
    def generator_name(self) -> str:
        return "model"
    
    def get_proc_path(self) -> str:
        """Return path for model.default file."""
        return "model.default"
        
    def generate(self, path: str, node: FileNode, fs_structure: dict) -> str:
        """Return the model configuration content."""
        if node.content:
            # Parse and validate input
            try:
                # First try parsing as JSON
                config = ModelConfig.model_validate_json(node.content)
                return config.model
            except:
                # If not JSON, treat as raw model name
                return node.content.strip()
        return ModelConfig().model
