"""Logging configuration for TouchFS."""
import logging
import os
import sys
import fcntl
from pathlib import Path
from typing import Any, Optional

# Global state
_file_handler = None
_logger_pid = None

def _debug_write(msg: str) -> None:
    """Write debug message to stderr with flush."""
    sys.stderr.write(msg)
    sys.stderr.flush()

def _reinit_logger_after_fork():
    """Reinitialize logger after fork to ensure proper file handles."""
    global _logger_pid
    current_pid = os.getpid()
    if _logger_pid is not None and _logger_pid != current_pid:
        # Get debug_stderr setting from existing logger
        debug_stderr = logger.handlers[-1].stream == sys.stderr if logger.handlers else False
        if debug_stderr:
            _debug_write(f"[Logger Debug] Fork detected! Reinitializing logger for PID {current_pid}\n")
        logger = logging.getLogger("touchfs")
        if _file_handler:
            # Close existing handler
            _file_handler.close()
            logger.removeHandler(_file_handler)
        # Setup new handler with same debug_stderr setting
        setup_logging(debug_stderr=logger.handlers[-1].stream == sys.stderr if logger.handlers else False)
        _logger_pid = current_pid

class ImmediateFileHandler(logging.FileHandler):
    """A FileHandler that flushes immediately after each write with file locking."""
    def __init__(self, filename, mode='a', encoding=None, delay=False, debug_stderr=False):
        """Initialize the handler with verification."""
        super().__init__(filename, mode, encoding, delay)
        self.debug_stderr = debug_stderr
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
            if self.debug_stderr:
                _debug_write(f"[Logger Debug] {error_msg}\n")
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
                    if self.debug_stderr:
                        _debug_write(f"[Logger Debug] Write verification failed: {error_context}\n")
                    raise IOError("Write verification failed - file size did not increase")
            finally:
                fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN)
                
        except Exception as e:
            error_msg = f"Logging failed ({error_context}): {str(e)}"
            if self.debug_stderr:
                _debug_write(f"[Logger Debug] {error_msg}\n")
            
            # Try to recover stream
            try:
                if self.stream:
                    self.stream.close()
                self.stream = None
            except:
                pass
                
            raise RuntimeError(error_msg)

def setup_logging(force_new: bool = False, test_tag: Optional[str] = None, debug_stderr: bool = False) -> logging.Logger:
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
    global _logger_pid
    current_pid = os.getpid()
    
    # Check if we need to reinitialize after fork
    if _logger_pid is not None and _logger_pid != current_pid:
        force_new = True
        if debug_stderr:
            _debug_write(f"[Logger Debug] Fork detected - Old PID: {_logger_pid}, New PID: {current_pid}\n")
    
    # Create or get logger
    logger = logging.getLogger("touchfs")
    
    # Store current PID
    _logger_pid = current_pid
    logger.setLevel(logging.DEBUG)
    # Remove any existing handlers to prevent duplicates
    logger.handlers.clear()
    # Ensure logger propagates and isn't disabled by parent loggers
    logger.propagate = True
    logging.getLogger().setLevel(logging.DEBUG)  # Set root logger to DEBUG

    # Setup detailed console handler for stderr if debug_stderr is enabled
    if debug_stderr:
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

    # Try system log directory first
    system_log_dir = "/var/log/touchfs"
    home_log_file = os.path.expanduser("~/.touchfs.log")
    
    try:
        # Try system log directory
        log_path = Path(system_log_dir)
        try:
            log_path.mkdir(parents=True, exist_ok=True)
            if os.access(system_log_dir, os.W_OK):
                log_dir = system_log_dir
                log_file = log_path / "touchfs.log"
                if log_file.exists() and os.access(log_file, os.W_OK):
                    if debug_stderr:
                        _debug_write(f"[Logger Debug] Using system log file: {log_file}\n")
                else:
                    # Try creating the file to verify write access
                    try:
                        with open(log_file, 'a') as f:
                            f.write("")
                        if debug_stderr:
                            _debug_write(f"[Logger Debug] Created system log file: {log_file}\n")
                    except:
                        raise PermissionError("Cannot write to system log file")
            else:
                raise PermissionError("No write permission for system log directory")
        except Exception as e:
            if debug_stderr:
                _debug_write(f"[Logger Debug] System log setup failed, falling back to home directory: {str(e)}\n")
            raise

    except Exception:
        # Fall back to home directory
        log_dir = os.path.dirname(home_log_file)
        log_file = Path(home_log_file)
        if debug_stderr:
            _debug_write(f"[Logger Debug] Using home directory log file: {log_file}\n")
        
        
    # Setup detailed formatter for file logging
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
        try:
            # Read existing content in case we need to restore it
            with open(log_file, 'r') as f:
                original_content = f.read()
            
            # Find next available suffix number
            suffix = 1
            while (log_path / f"touchfs.log.{suffix}").exists():
                suffix += 1
            
            # Rename existing log file with suffix
            backup_path = log_path / f"touchfs.log.{suffix}"
            log_file.rename(backup_path)
            
            # Verify backup was created
            if not backup_path.exists():
                if debug_stderr:
                    _debug_write(f"[Logger Debug] Failed to create backup log file: {backup_path}\n")
                raise RuntimeError("Failed to create backup log file")
        except Exception as e:
            error_msg = f"Failed to rotate log file: {str(e)}"
            if debug_stderr:
                _debug_write(f"[Logger Debug] {error_msg}\n")
            # If rotation fails, try to restore original content
            try:
                with open(log_file, 'w') as f:
                    f.write(original_content)
            except Exception as restore_error:
                error_msg = f"Failed to rotate log AND restore original: {str(restore_error)}"
                if debug_stderr:
                    _debug_write(f"[Logger Debug] {error_msg}\n")
                raise RuntimeError(error_msg)
            raise RuntimeError(error_msg)
    
    # Setup file handler for single log file with immediate flush in append mode
    try:
        file_handler = ImmediateFileHandler(
            os.path.join(log_dir, "touchfs.log"),
            mode='a',
            debug_stderr=debug_stderr
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # Test write to new log file
        test_record = logging.LogRecord(
            "touchfs", logging.INFO, "", 0,
            "Logger initialized with rotation", (), None
        )
        file_handler.emit(test_record)
        
        # Verify the write actually occurred
        if not os.path.exists(log_file) or os.path.getsize(log_file) == 0:
            raise RuntimeError("Log file exists but is empty after test write")
            
        
        # Add handler to logger
        logger.addHandler(file_handler)
        
        # Store handler in global to prevent garbage collection
        global _file_handler
        _file_handler = file_handler
        
        return logger
        
    except Exception as e:
        error_msg = f"Failed to setup/test file handler: {str(e)}"
        if debug_stderr:
            _debug_write(f"[Logger Debug] {error_msg}\n")
        raise RuntimeError(error_msg)
