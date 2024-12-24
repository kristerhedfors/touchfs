import logging
import logging.handlers
import os
from pathlib import Path

def setup_logging(log_dir: str = "/var/log/llmfs") -> logging.Logger:
    """Setup production-level logging with rotation and proper formatting."""
    # Create logger
    logger = logging.getLogger("llmfs")
    logger.setLevel(logging.INFO)

    # Create log directory if it doesn't exist
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # Setup formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(process)d - %(thread)d - %(message)s'
    )
    
    # Setup file handlers with rotation
    # Main application log
    app_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, "llmfs.log"),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(detailed_formatter)
    
    # Error log
    error_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, "error.log"),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    # Access log for filesystem operations
    access_handler = logging.handlers.TimedRotatingFileHandler(
        os.path.join(log_dir, "access.log"),
        when="midnight",
        interval=1,
        backupCount=30
    )
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))

    # Add handlers to logger
    logger.addHandler(app_handler)
    logger.addHandler(error_handler)
    logger.addHandler(access_handler)

    return logger
