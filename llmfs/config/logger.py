"""Logging configuration for LLMFS."""
import logging
import os
from pathlib import Path

def setup_logging(log_rotate: bool = False) -> logging.Logger:
    """Setup logging with full details at DEBUG level.
    
    Args:
        log_rotate: Whether to rotate (clear) logs before starting
        
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
    
    # Rotate (clear) log if requested
    log_file = log_path / "llmfs.log"
    if log_rotate and log_file.exists():
        log_file.unlink()
    
    # Setup detailed formatter for file logging
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - '
        '%(funcName)s - %(process)d - %(thread)d - %(message)s'
    )
    
    # Setup file handler for single log file
    file_handler = logging.FileHandler(
        os.path.join(log_dir, "llmfs.log")
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    # Log and flush initial message to ensure file exists with content
    logger.info("Logger initialized")
    for handler in logger.handlers:
        handler.flush()

    return logger
