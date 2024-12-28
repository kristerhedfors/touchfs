"""Logging configuration for LLMFS."""
import logging
import os
import sys
import fcntl
from pathlib import Path
from typing import Any

# Global file handler reference to prevent garbage collection
_file_handler = None

class ImmediateFileHandler(logging.FileHandler):
    """A FileHandler that flushes immediately after each write with file locking."""
    def emit(self, record: logging.LogRecord) -> None:
        """Emit a record with file locking and immediate flush."""
        try:
            msg = self.format(record)
            # Ensure stream is open
            if self.stream is None:
                if self.mode != 'w' and os.path.exists(self.baseFilename):
                    with open(self.baseFilename, 'r') as f:
                        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                        f.close()
                self.stream = self._open()
            
            # Acquire exclusive lock
            fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX)
            try:
                self.stream.write(msg + self.terminator)
                self.stream.flush()
                os.fsync(self.stream.fileno())  # Force write to disk
            finally:
                # Release lock
                fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            self.handleError(record)
            # Try to log the error itself
            try:
                sys.stderr.write(f'Failed to log message: {str(e)}\n')
            except:
                pass

def setup_logging() -> logging.Logger:
    """Setup logging with full details at DEBUG level. Logs are rotated (cleared)
    for each new invocation to ensure clean logs that can be accessed through
    the proc plugin.
    
    The function performs the following steps:
    1. Creates log directory if it doesn't exist
    2. Rotates existing log file with incremented suffix
    3. Sets up new log file with proper permissions
    4. Validates ability to write to new log file
    
    Returns:
        Configured logger instance
        
    Raises:
        OSError: If log directory cannot be created or accessed
        PermissionError: If log file cannot be written to
        RuntimeError: If log rotation fails
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

    try:
        # Create log directory if it doesn't exist
        log_dir = "/var/log/llmfs"
        log_path = Path(log_dir)
        try:
            log_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise OSError(f"Failed to create/access log directory {log_dir}: {str(e)}")

        # Validate directory and file permissions
        if not os.access(log_dir, os.W_OK):
            raise PermissionError(f"No write permission for log directory {log_dir}")
            
        log_file = log_path / "llmfs.log"
        if log_file.exists() and not os.access(log_file, os.W_OK):
            raise PermissionError(f"No write permission for log file {log_file}")
        
        
        # Rotate existing log if it exists
        if log_file.exists():
            try:
                # Read existing content in case we need to restore it
                with open(log_file, 'r') as f:
                    original_content = f.read()
                
                # Find next available suffix number
                suffix = 1
                while (log_path / f"llmfs.log.{suffix}").exists():
                    suffix += 1
                
                # Rename existing log file with suffix
                backup_path = log_path / f"llmfs.log.{suffix}"
                log_file.rename(backup_path)
                
                # Verify backup was created
                if not backup_path.exists():
                    raise RuntimeError("Failed to create backup log file")
                    
            except Exception as e:
                # If rotation fails, try to restore original content
                try:
                    with open(log_file, 'w') as f:
                        f.write(original_content)
                except Exception as restore_error:
                    raise RuntimeError(f"Failed to rotate log AND restore original: {str(restore_error)}")
                raise RuntimeError(f"Failed to rotate log file: {str(e)}")
    
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
        
        # Test write to new log file
        try:
            file_handler.emit(
                logging.LogRecord(
                    "llmfs", logging.INFO, "", 0, 
                    "Logger initialized with rotation", (), None
                )
            )
        except Exception as e:
            raise RuntimeError(f"Failed to write to new log file: {str(e)}")
        
        # Add handler to logger
        logger.addHandler(file_handler)
        
        # Store handler in global to prevent garbage collection
        global _file_handler
        _file_handler = file_handler
        
        return logger
        
    except Exception as e:
        # Log setup failure to stderr and re-raise
        sys.stderr.write(f"Failed to setup logging: {str(e)}\n")
        raise
