"""Plugin that provides model configuration file in .llmfs."""
from typing import List
import logging
from pydantic import BaseModel
from .proc import ProcPlugin
from .base import OverlayFile
from ...models.filesystem import FileNode
from ...config.settings import get_model, set_model

logger = logging.getLogger("llmfs")

class ModelConfig(BaseModel):
    model: str = get_model()  # Use current model as default

class ModelPlugin(ProcPlugin):
    """Plugin that provides the model.default file in .llmfs."""
    
    def generator_name(self) -> str:
        return "model"
    
    def get_proc_path(self) -> str:
        """Return path for model.default file."""
        return "model.default"
        
    def generate(self, path: str, node: FileNode, fs_structure: dict) -> str:
        """Return the model configuration content and update global config."""
        model = get_model()  # Start with current model
        
        if node.content:
            # Parse and validate input
            try:
                # First try parsing as JSON
                config = ModelConfig.model_validate_json(node.content)
                model = config.model
                logger.debug(f"Parsed model from JSON: {model}")
            except:
                # If not JSON, treat as raw model name
                model = node.content.strip()
                logger.debug(f"Using raw model input: {model}")
        else:
            logger.debug(f"Using default model: {model}")
        
        # Update global configuration
        set_model(model)  # This will log at info level
        return model
