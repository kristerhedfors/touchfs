"""Plugin that exposes current model configuration through /.touchfs/model_default."""
from .proc import ProcPlugin
from ...models.filesystem import FileNode
from ... import config

class ModelPlugin(ProcPlugin):
    """Plugin that exposes current model configuration through /.touchfs/model_default."""
    
    def generator_name(self) -> str:
        return "model"
    
    def get_proc_path(self) -> str:
        """Return path for model_default file."""
        return "model_default"
        
    def generate(self, path: str, node: FileNode, fs_structure: dict) -> str:
        """Return the current model configuration."""
        return config.model.get_model()
