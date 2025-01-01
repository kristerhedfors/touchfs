"""Plugin that exposes current prompt configuration through /.touchfs/prompt_default."""
from .proc import ProcPlugin
from ...models.filesystem import FileNode
from ...config.settings import get_global_prompt

class PromptPlugin(ProcPlugin):
    """Plugin that exposes current prompt configuration through /.touchfs/prompt_default."""
    
    def generator_name(self) -> str:
        return "prompt"
    
    def get_proc_path(self) -> str:
        """Return path for prompt_default file."""
        return "prompt_default"
        
    def generate(self, path: str, node: FileNode, fs_structure: dict) -> str:
        """Return the current prompt configuration."""
        return get_global_prompt() + "\n"
