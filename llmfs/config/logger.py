"""Logging configuration for LLMFS."""
import logging
import os
import fcntl
from pathlib import Path
from typing import Any

class ImmediateFileHandler(logging.FileHandler):
    """A FileHandler that flushes immediately after each write with file locking."""
    def emit(self, record: logging.LogRecord) -> None:
        """Emit a record with file locking and immediate flush."""
        try:
            msg = self.format(record)
            stream = self.stream
            # Acquire exclusive lock
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            try:
                stream.write(msg + self.terminator)
                stream.flush()
            finally:
                # Release lock
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        except Exception:
            self.handleError(record)

def setup_logging() -> logging.Logger:
    """Setup logging with full details at DEBUG level. Logs are rotated (cleared)
    for each new invocation to ensure clean logs that can be accessed through
    the proc plugin.
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("llmfs")
    logger.setLevel(logging.DEBUG)

    # Setup console handler for debug output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(console_handler)

    # Create log directory if it doesn't exist
    log_dir = "/var/log/llmfs"
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Rotate logs with incremented suffixes
    log_file = log_path / "llmfs.log"
    if log_file.exists():
        # Find next available suffix number
        suffix = 1
        while (log_path / f"llmfs.log.{suffix}").exists():
            suffix += 1
        # Rename existing log file with suffix
        log_file.rename(log_path / f"llmfs.log.{suffix}")
    
    # Setup detailed formatter for file logging
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - '
        '%(funcName)s - %(process)d - %(thread)d - %(message)s'
    )
    
    # Setup file handler for single log file with immediate flush in append mode
    file_handler = ImmediateFileHandler(
        os.path.join(log_dir, "llmfs.log"),
        mode='a'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    # Log initial message to ensure file exists with content
    logger.info("Logger initialized")
    file_handler.flush()

    return logger
