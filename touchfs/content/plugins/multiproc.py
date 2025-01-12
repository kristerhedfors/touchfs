"""Base class for plugins that provide multiple auto-generated overlay files similar to /proc."""
from abc import abstractmethod
from typing import Dict, List
from .base import BaseContentGenerator, ProcFile
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
        Return the paths where this plugin's overlay files should be created in .touchfs.

        Returns:
            List[str]: Paths relative to .touchfs directory (e.g., ["cache_enabled", "cache_stats"])
        """
        pass
    
    def get_proc_files(self) -> List[ProcFile]:
        """Provide auto-generated files as proc files in .touchfs directory."""
        proc_files = []
        for path in self.get_proc_paths():
            proc_file = ProcFile(f"/.touchfs/{path}", {"generator": self.generator_name()})
            proc_files.append(proc_file)
        return proc_files
        
    def can_handle(self, path: str, node: FileNode) -> bool:
        """
        Check if this generator should handle the given file.
        Returns True for files matching any of the proc paths in .touchfs directory.
        """
        for proc_path in self.get_proc_paths():
            if path == f"/.touchfs/{proc_path}":
                return True
        return False
