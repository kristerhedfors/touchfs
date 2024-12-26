"""Base class for plugins that provide auto-generated overlay files similar to /proc."""
from abc import abstractmethod
from typing import Dict, List
from .base import BaseContentGenerator, OverlayFile
from ...models.filesystem import FileNode

class ProcPlugin(BaseContentGenerator):
    """
    Base class for plugins that provide auto-generated overlay files.
    Similar to Linux's /proc filesystem, these plugins create virtual files
    whose contents are generated on-demand and reflect the current system state.
    """
    
    @abstractmethod
    def get_proc_path(self) -> str:
        """
        Return the path where this plugin's overlay file should be created in .llmfs.
        
        Returns:
            str: Path relative to .llmfs directory (e.g., "generation.model" for .llmfs/generation.model)
        """
        pass
    
    def get_overlay_files(self) -> List[OverlayFile]:
        """Provide auto-generated file as an overlay in .llmfs directory."""
        path = f"/.llmfs/{self.get_proc_path()}"
        overlay = OverlayFile(path, {"generator": self.generator_name()})
        return [overlay]
        
    def can_handle(self, path: str, node: FileNode) -> bool:
        """
        Check if this generator should handle the given file.
        Returns True for files matching the proc path in .llmfs directory.
        """
        expected_path = f"/.llmfs/{self.get_proc_path()}"
        return path == expected_path
