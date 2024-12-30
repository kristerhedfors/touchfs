"""Logging configuration for LLMFS."""
import logging
import os
import sys
import fcntl
from pathlib import Path
from typing import Any, Optional

# Global state
_file_handler = None
_logger_pid = None

def _reinit_logger_after_fork():
    """Reinitialize logger after fork to ensure proper file handles."""
    global _logger_pid
    current_pid = os.getpid()
    if _logger_pid is not None and _logger_pid != current_pid:
        sys.stderr.write(f"[Logger Debug] Fork detected! Reinitializing logger for PID {current_pid}\n")
        logger = logging.getLogger("llmfs")
        if _file_handler:
            # Close existing handler
            _file_handler.close()
            logger.removeHandler(_file_handler)
        # Setup new handler
        setup_logging()
        _logger_pid = current_pid

class ImmediateFileHandler(logging.FileHandler):
    """A FileHandler that flushes immediately after each write with file locking."""
    def __init__(self, filename, mode='a', encoding=None, delay=False):
        """Initialize the handler with verification."""
        super().__init__(filename, mode, encoding, delay)
        self._verify_file_access()
    
    def _verify_file_access(self) -> None:
        """Verify file can be opened and written to."""
        try:
            with open(self.baseFilename, 'a') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                f.write("")
                f.flush()
                os.fsync(f.fileno())
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            error_msg = f"Cannot access log file {self.baseFilename}: {str(e)}"
            sys.stderr.write(f"CRITICAL ERROR: {error_msg}\n")
            raise RuntimeError(error_msg)

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a record with file locking and immediate flush."""
        msg = self.format(record)
        error_context = f"PID={os.getpid()}, File={self.baseFilename}"
        
        try:
            if not self.stream:
                self.stream = self._open()
                if not self.stream:
                    raise IOError("Failed to open stream")
            
            # Verify stream is writable
            if not self.stream.writable():
                raise IOError("Stream not writable")
                
            sys.stderr.write(f"[Logger Debug] Attempting write: {error_context}\n")
            
            # Acquire exclusive lock
            fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX)
            initial_size = os.path.getsize(self.baseFilename)
            
            try:
                self.stream.write(msg + self.terminator)
                self.stream.flush()
                os.fsync(self.stream.fileno())
                
                # Verify write actually occurred
                new_size = os.path.getsize(self.baseFilename)
                if new_size <= initial_size:
                    raise IOError("Write verification failed - file size did not increase")
                
                sys.stderr.write(f"[Logger Debug] Write successful: {error_context}\n")
            finally:
                fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN)
                
        except Exception as e:
            error_msg = f"Logging failed ({error_context}): {str(e)}"
            sys.stderr.write(f"CRITICAL ERROR: {error_msg}\n")
            
            # Try to recover stream
            try:
                if self.stream:
                    self.stream.close()
                self.stream = None
            except:
                pass
                
            raise RuntimeError(error_msg)

def setup_logging(force_new: bool = False, test_tag: Optional[str] = None) -> logging.Logger:
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
    sys.stderr.write("[Logger Setup] Starting logging initialization\n")
    global _logger_pid
    current_pid = os.getpid()
    
    # Check if we need to reinitialize after fork
    if _logger_pid is not None and _logger_pid != current_pid:
        force_new = True
        sys.stderr.write(f"[Logger Debug] Fork detected in setup_logging! Old PID: {_logger_pid}, New PID: {current_pid}\n")
    
    # Create or get logger
    logger = logging.getLogger("llmfs")
    
    # Store current PID
    _logger_pid = current_pid
    logger.setLevel(logging.DEBUG)
    # Remove any existing handlers to prevent duplicates
    logger.handlers.clear()
    # Ensure logger propagates and isn't disabled by parent loggers
    logger.propagate = True
    logging.getLogger().setLevel(logging.DEBUG)  # Set root logger to DEBUG

    # Setup detailed console handler for stderr
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - '
        '%(funcName)s - %(process)d - %(thread)d - %(message)s'
    ))
    logger.addHandler(console_handler)

    # Force flush after each log
    def flush_after(func):
        def wrapper(msg, *args, **kwargs):
            result = func(msg, *args, **kwargs)
            for handler in logger.handlers:
                handler.flush()
            return result
        return wrapper

    logger.info = flush_after(logger.info)
    logger.debug = flush_after(logger.debug)
    logger.warning = flush_after(logger.warning)
    logger.error = flush_after(logger.error)

    # Create log directory if it doesn't exist
    log_dir = "/var/log/llmfs"
    log_path = Path(log_dir)
    sys.stderr.write(f"[Logger Setup] Ensuring log directory exists: {log_dir}\n")
    
    try:
        log_path.mkdir(parents=True, exist_ok=True)
        sys.stderr.write("[Logger Setup] Log directory created/verified\n")
    except Exception as e:
        error_msg = f"Failed to create/access log directory {log_dir}: {str(e)}"
        sys.stderr.write(f"[Logger Setup] CRITICAL ERROR: {error_msg}\n")
        raise OSError(error_msg)

    # Validate directory and file permissions
    sys.stderr.write("[Logger Setup] Checking directory permissions\n")
    if not os.access(log_dir, os.W_OK):
        error_msg = f"No write permission for log directory {log_dir}"
        sys.stderr.write(f"[Logger Setup] CRITICAL ERROR: {error_msg}\n")
        raise PermissionError(error_msg)
        
    log_file = log_path / "llmfs.log"
    sys.stderr.write(f"[Logger Setup] Checking log file permissions: {log_file}\n")
    if log_file.exists() and not os.access(log_file, os.W_OK):
        error_msg = f"No write permission for log file {log_file}"
        sys.stderr.write(f"[Logger Setup] CRITICAL ERROR: {error_msg}\n")
        raise PermissionError(error_msg)
        
        
    # Setup detailed formatter for file logging
    sys.stderr.write("[Logger Setup] Creating detailed formatter\n")
    if test_tag:
        detailed_formatter = logging.Formatter(
            f'%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - '
            f'%(funcName)s - %(process)d - %(thread)d - [{test_tag}] %(message)s'
        )
    else:
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - '
            '%(funcName)s - %(process)d - %(thread)d - %(message)s'
        )
    
    # Rotate existing log if it exists
    if log_file.exists():
        sys.stderr.write("[Logger Setup] Rotating existing log file\n")
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
            sys.stderr.write(f"[Logger Setup] Creating backup at: {backup_path}\n")
            log_file.rename(backup_path)
            
            # Verify backup was created
            if not backup_path.exists():
                raise RuntimeError("Failed to create backup log file")
                
            sys.stderr.write("[Logger Setup] Log rotation successful\n")
        except Exception as e:
            error_msg = f"Failed to rotate log file: {str(e)}"
            sys.stderr.write(f"[Logger Setup] CRITICAL ERROR: {error_msg}\n")
            # If rotation fails, try to restore original content
            try:
                with open(log_file, 'w') as f:
                    f.write(original_content)
            except Exception as restore_error:
                error_msg = f"Failed to rotate log AND restore original: {str(restore_error)}"
                sys.stderr.write(f"[Logger Setup] CRITICAL ERROR: {error_msg}\n")
                raise RuntimeError(error_msg)
            raise RuntimeError(error_msg)
    
    # Setup file handler for single log file with immediate flush in append mode
    sys.stderr.write("[Logger Setup] Creating file handler\n")
    try:
        file_handler = ImmediateFileHandler(
            os.path.join(log_dir, "llmfs.log"),
            mode='a'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # Test write to new log file
        sys.stderr.write("[Logger Setup] Testing initial log write\n")
        test_record = logging.LogRecord(
            "llmfs", logging.INFO, "", 0,
            "Logger initialized with rotation", (), None
        )
        file_handler.emit(test_record)
        
        # Verify the write actually occurred
        if not os.path.exists(log_file) or os.path.getsize(log_file) == 0:
            raise RuntimeError("Log file exists but is empty after test write")
            
        sys.stderr.write("[Logger Setup] Initial log write successful\n")
        
        # Add handler to logger
        logger.addHandler(file_handler)
        
        # Store handler in global to prevent garbage collection
        global _file_handler
        _file_handler = file_handler
        
        sys.stderr.write("[Logger Setup] Logger initialization complete\n")
        return logger
        
    except Exception as e:
        error_msg = f"Failed to setup/test file handler: {str(e)}"
        sys.stderr.write(f"[Logger Setup] CRITICAL ERROR: {error_msg}\n")
        raise RuntimeError(error_msg)
