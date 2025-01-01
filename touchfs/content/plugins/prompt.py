"""Plugin that exposes prompt configuration and history through proc-like files."""
from typing import Dict, List
from .multiproc import MultiProcPlugin
from .base import OverlayFile
from ...models.filesystem import FileNode
from ...config.settings import get_global_prompt, get_last_final_prompt

class PromptPlugin(MultiProcPlugin):
    """Plugin that exposes prompt configuration and history through proc-like files.
    
    Creates the following files:
    - .touchfs/prompt_default: Current prompt configuration
    - .touchfs/prompt_last_final: Last complete prompt sent to LLM
    """
    
    def generator_name(self) -> str:
        return "prompt"
    
    def get_proc_paths(self) -> List[str]:
        """Return paths for prompt-related proc files."""
        return ["prompt_default", "prompt_last_final", "filesystem_prompt"]
    
    def get_overlay_files(self) -> List[OverlayFile]:
        """Provide auto-generated files as overlays in .touchfs directory."""
        overlays = []
        for path in self.get_proc_paths():
            overlay = OverlayFile(f"/.touchfs/{path}", {"generator": self.generator_name()})
            overlay.attrs["st_mode"] = "33188"  # Regular file with 644 permissions
            overlay.xattrs["generate_content"] = b"true"  # Force regeneration
            overlays.append(overlay)
        return overlays
        
    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        """Return the requested prompt information based on path."""
        # Strip /.touchfs/ prefix to get proc path
        proc_path = path.replace("/.touchfs/", "")
        
        # Ensure node has proper attributes for proc files
        if "attrs" not in node:
            node.attrs = {}
        node.attrs["st_mode"] = "33188"  # Regular file with 644 permissions
        
        if proc_path == "prompt_default":
            return get_global_prompt() + "\n"
        elif proc_path == "prompt_last_final":
            last_prompt = get_last_final_prompt()
            return last_prompt + "\n" if last_prompt else "No prompts generated yet\n"
        elif proc_path == "filesystem_prompt":
            from ...config.settings import get_current_filesystem_prompt
            fs_prompt = get_current_filesystem_prompt()
            return fs_prompt + "\n" if fs_prompt else "No filesystem generation prompt used\n"
        return ""
