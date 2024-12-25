"""Logging configuration for LLMFS."""
import logging
import logging.handlers
import os
from pathlib import Path

def setup_logging(log_dir: str = "/var/log/llmfs", rotate_logs: bool = False) -> logging.Logger:
    """Setup logging with rotation and proper formatting.
    
    Args:
        log_dir: Directory to store log files
        rotate_logs: Whether to rotate logs before starting
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("llmfs")
    logger.setLevel(logging.DEBUG)

    # Setup console handler for rich debug output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(console_handler)

    # Create log directory if it doesn't exist
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Rotate logs if requested
    if rotate_logs:
        for log_file in ["llmfs.log", "error.log", "access.log"]:
            log_path = Path(log_dir) / log_file
            if log_path.exists():
                log_path.unlink()  # Remove existing log file

    # Setup formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(process)d - %(thread)d - %(message)s'
    )
    
    # Setup file handler with rotation for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, "llmfs.log"),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)

    return logger
