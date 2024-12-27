"""Base class for plugins that provide multiple auto-generated overlay files similar to /proc."""
from abc import abstractmethod
from typing import Dict, List
from .base import BaseContentGenerator, OverlayFile
from ...models.filesystem import FileNode

class MultiProcPlugin(BaseContentGenerator):
    """
    Base class for plugins that provide multiple auto-generated overlay files.
    Similar to Linux's /proc filesystem, these plugins create virtual files
    whose contents are generated on-demand and reflect the current system state.
    """
    
    @abstractmethod
    def get_proc_paths(self) -> List[str]:
        """
        Return the paths where this plugin's overlay files should be created in .llmfs.
        
        Returns:
            List[str]: Paths relative to .llmfs directory (e.g., ["cache_enabled", "cache_stats"])
        """
        pass
    
    def get_overlay_files(self) -> List[OverlayFile]:
        """Provide auto-generated files as overlays in .llmfs directory."""
        overlays = []
        for path in self.get_proc_paths():
            overlay = OverlayFile(f"/.llmfs/{path}", {"generator": self.generator_name()})
            overlays.append(overlay)
        return overlays
        
    def can_handle(self, path: str, node: FileNode) -> bool:
        """
        Check if this generator should handle the given file.
        Returns True for files matching any of the proc paths in .llmfs directory.
        """
        for proc_path in self.get_proc_paths():
            if path == f"/.llmfs/{proc_path}":
                return True
        return False
