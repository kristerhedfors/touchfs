"""Plugin that provides access to LLMFS logs."""
from pathlib import Path
import logging
import os
from typing import Dict, Optional
from ..plugins.proc import ProcPlugin
from ...models.filesystem import FileNode

logger = logging.getLogger(__name__)

class LogPlugin(ProcPlugin):
    """Plugin that exposes LLMFS logs as a virtual file."""
    
    def __init__(self):
        """Initialize the log plugin and capture initial log file size."""
        super().__init__()
        # Minimize logging during initialization
        self._log_offset = self._get_initial_offset()
        # Store file handle to avoid reopening
        self._log_file: Optional[Path] = None
        self._current_content: Optional[str] = None
        
    def _get_initial_offset(self) -> int:
        """Get the initial size of the log file to use as offset."""
        log_file = Path("/var/log/llmfs/llmfs.log")
        try:
            if log_file.exists():
                return os.path.getsize(str(log_file))
            return 0
        except Exception:
            return 0
    
    def generator_name(self) -> str:
        return "log"
        
    def get_proc_path(self) -> str:
        return "log"

    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        """
        Read and return the contents of the LLMFS log file from the stored offset.
        Minimizes logging to prevent recursive growth.
        """
        log_file = Path("/var/log/llmfs/llmfs.log")
        
        if not log_file.exists():
            return "No logs available - log file not found"
            
        try:
            # Cache log content to prevent repeated reads
            if self._current_content is None:
                with open(log_file, 'r') as f:
                    f.seek(self._log_offset)
                    self._current_content = f.read()
            
            # Return the cached content
            # The FUSE layer will handle proper chunking via read() operations
            return self._current_content

        except Exception as e:
            return f"Error reading logs: {str(e)}"

    def read(self, path: str, size: int, offset: int) -> bytes:
        """
        Handle chunked reads properly to avoid FUSE errors.
        This overrides the default read implementation.
        """
        if self._current_content is None:
            # Generate content if not cached
            self._current_content = self.generate(path, None, {})
            
        # Return the requested chunk
        chunk = self._current_content[offset:offset + size]
        return chunk.encode('utf-8')
