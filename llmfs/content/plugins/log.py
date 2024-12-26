"""Plugin that provides access to LLMFS logs."""
from pathlib import Path
import logging
import os
from typing import Dict
from ..plugins.proc import ProcPlugin
from ...models.filesystem import FileNode

logger = logging.getLogger(__name__)

class LogPlugin(ProcPlugin):
    """Plugin that exposes LLMFS logs as a virtual file."""
    
    def __init__(self):
        """Initialize the log plugin and capture initial log file size."""
        super().__init__()
        logger.info("Initializing LogPlugin")
        # Ensure this log message is written before getting offset
        for handler in logger.handlers:
            handler.flush()
        self._log_offset = self._get_initial_offset()
        logger.info(f"Initial log offset set to: {self._log_offset}")
    
    def _get_initial_offset(self) -> int:
        """Get the initial size of the log file to use as offset."""
        log_file = Path("/var/log/llmfs/llmfs.log")
        try:
            if log_file.exists():
                size = os.path.getsize(str(log_file))
                logger.debug(f"Log file exists, size: {size}")
                # Verify we're not getting a zero size when file exists and has content
                if size == 0:
                    # Read first few bytes to check if file really is empty
                    with open(log_file, 'r') as f:
                        content = f.read(100)
                        if content:
                            logger.warning("File has content but size reported as 0, rereading size")
                            # Force a reread of the size
                            size = os.path.getsize(str(log_file))
                return size
            logger.debug("Log file does not exist")
            return 0
        except Exception as e:
            logger.error(f"Failed to get log file size: {str(e)}")
            return 0
    
    def generator_name(self) -> str:
        return "log"
        
    def get_proc_path(self) -> str:
        return "log"

    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        """
        Read and return the contents of the LLMFS log file from the stored offset.
        """
        log_file = Path("/var/log/llmfs/llmfs.log")
        logger.debug(f"Current log file size: {os.path.getsize(str(log_file)) if log_file.exists() else 'file not found'}")
        
        if not log_file.exists():
            logger.warning(f"Log file not found at {log_file}")
            return "No logs available - log file not found"
            
        try:
            logger.info(f"Opening log file: {log_file}")
            with open(log_file, 'r') as f:
                logger.info(f"Reading log file from offset: {self._log_offset}")
                f.seek(self._log_offset)
                content = f.read()
                logger.info(f"Read {len(content)} bytes from log file")
                if not content:
                    logger.warning("No content read from log file after offset")
                return content
        except Exception as e:
            logger.error(f"Failed to read log file: {str(e)}")
            return f"Error reading logs: {str(e)}"
