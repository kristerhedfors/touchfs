"""Plugin that provides a symlink to the LLMFS log file."""
from pathlib import Path
from typing import Dict, List
from ...models.filesystem import FileNode
from .base import BaseContentGenerator, OverlaySymlink
from .proc import ProcPlugin

class LogSymlinkPlugin(ProcPlugin):
    """Plugin that creates a symlink to the LLMFS log file."""
    
    def generator_name(self) -> str:
        return "log_symlink"
        
    def get_proc_path(self) -> str:
        return "log"

    def get_overlay_files(self):
        """Create a symlink to the current log file."""
        return [
            OverlaySymlink(
                path="/.llmfs/log",
                target="/var/log/llmfs/llmfs.log"
            )
        ]

    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        """Not used for symlinks."""
        return ""
