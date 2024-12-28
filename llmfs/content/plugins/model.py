"""Plugin that handles model configuration files (.llmfs.model and .model)."""
from typing import List
import logging
from pydantic import BaseModel
from .proc import ProcPlugin
from .base import OverlayFile
from ...models.filesystem import FileNode
from ...config.settings import get_model, set_model, find_nearest_model_file

logger = logging.getLogger("llmfs")

class ModelConfig(BaseModel):
    model: str = get_model()  # Use current model as default

class ModelPlugin(ProcPlugin):
    """Plugin that handles model configuration files (.llmfs.model and .model)."""
    
    def generator_name(self) -> str:
        return "model"
    
    def get_proc_path(self) -> str:
        """Return path for model.default file."""
        return "model.default"
        
    def generate(self, path: str, node: FileNode, fs_structure: dict) -> str:
        """Return the model configuration content and update global config.
        
        First checks for nearest model file in the directory hierarchy,
        then falls back to node content or global default.
        """
        # Try to find nearest model file
        nearest_model_path = find_nearest_model_file(path, fs_structure)
        if nearest_model_path and nearest_model_path != path:  # Avoid self-reference
            nearest_node = fs_structure.get(nearest_model_path)
            if nearest_node and nearest_node.content:
                try:
                    config = ModelConfig.model_validate_json(nearest_node.content)
                    model = config.model
                    logger.debug(f"Using model from nearest file: {nearest_model_path}")
                except:
                    model = nearest_node.content.strip()
                    logger.debug(f"Using raw model from nearest file: {nearest_model_path}")
                set_model(model)
                return model + "\n"
        
        # Fall back to node content if available
        if node.content:
            try:
                config = ModelConfig.model_validate_json(node.content)
                model = config.model
                logger.debug(f"Parsed model from JSON: {model}")
            except:
                model = node.content.strip()
                logger.debug(f"Using raw model input: {model}")
            set_model(model)
            return model + "\n"
            
        # Fall back to global default
        model = get_model()
        logger.debug(f"Using default model: {model}")
        return model + "\n"
