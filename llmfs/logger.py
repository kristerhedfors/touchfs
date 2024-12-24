import logging
import logging.handlers
import os
from pathlib import Path

def setup_logging(log_dir: str = "/var/log/llmfs", debug: bool = False) -> logging.Logger:
    """Setup logging with rotation and proper formatting.
    
    Args:
        log_dir: Directory to store log files
        debug: Enable debug logging and console output
    """
    # Create logger
    logger = logging.getLogger("llmfs")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Setup console handler for debug mode
    if debug:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(console_handler)

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
