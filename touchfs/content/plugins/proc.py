"""Base class for plugins that provide auto-generated overlay files similar to /proc."""
from abc import abstractmethod
from typing import Dict, List
from .base import BaseContentGenerator, ProcFile
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
        Return the path where this plugin's overlay file should be created in .touchfs.

        Returns:
            str: Path relative to .touchfs directory (e.g., "generation.model" for .touchfs/generation.model)
        """
        pass
    
    def get_proc_files(self) -> List[ProcFile]:
        """Provide auto-generated file as a proc file in .touchfs directory."""
        path = f"/.touchfs/{self.get_proc_path()}"
        proc_file = ProcFile(path, {"generator": self.generator_name()})
        return [proc_file]
        
    def can_handle(self, path: str, node: FileNode) -> bool:
        """
        Check if this generator should handle the given file.
        Returns True for files matching the proc path in .touchfs directory.
        """
        expected_path = f"/.touchfs/{self.get_proc_path()}"
        return path == expected_path
