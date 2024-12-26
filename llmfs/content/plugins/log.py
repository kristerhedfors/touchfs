"""Plugin that provides access to LLMFS logs."""
from pathlib import Path
import logging
from typing import Dict
from ..plugins.proc import ProcPlugin
from ...models.filesystem import FileNode

logger = logging.getLogger(__name__)

class LogPlugin(ProcPlugin):
    """Plugin that exposes LLMFS logs as a virtual file."""
    
    def generator_name(self) -> str:
        return "log"
        
    def get_proc_path(self) -> str:
        return "log"

    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        """
        Read and return the contents of the LLMFS log file.
        """
        log_file = Path("/var/log/llmfs/llmfs.log")
        
        if not log_file.exists():
            logger.warning(f"Log file not found at {log_file}")
            return "No logs available - log file not found"
            
        try:
            return log_file.read_text()
        except Exception as e:
            logger.error(f"Failed to read log file: {str(e)}")
            return f"Error reading logs: {str(e)}"
