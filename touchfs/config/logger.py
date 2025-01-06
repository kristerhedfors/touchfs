"""Logging configuration for TouchFS."""
import logging
import os
import sys
import fcntl
import errno
from pathlib import Path
from typing import Any, Optional

# Global state
_file_handler = None
_logger_pid = None
system_log_dir = None  # Initialize at module level

# Module logger
logger = logging.getLogger("touchfs")

def _check_file_writable(path: Path, check_parent: bool = False) -> None:
    """Check if a file is writable, raising PermissionError if not."""
    if path.exists() and not os.access(path, os.W_OK):
        raise PermissionError(f"No write permission for file: {path}")
    if check_parent and not os.access(path.parent, os.W_OK):
        raise PermissionError(f"No write permission for directory: {path.parent}")

def _verify_file_creation(path: Path) -> None:
    """Verify we can create/write to a file, raising PermissionError if not."""
    try:
        # Try to open file for writing
        with open(path, 'a') as f:
            f.write("")
    except (IOError, OSError) as e:
        if e.errno in (errno.EACCES, errno.EPERM):
            raise PermissionError(f"Cannot write to file: {path}")
        raise

def _verify_file_rotation(log_file: Path) -> None:
    """Verify we can rotate the log file, raising PermissionError if not."""
    if not log_file.exists():
        return
    
    # Check if we can write to both the file and its parent directory
    if not os.access(log_file, os.W_OK):
        raise PermissionError(f"No write permission for file: {log_file}")
    if not os.access(log_file.parent, os.W_OK):
        raise PermissionError(f"No write permission for directory: {log_file.parent}")
    
    # Try to open the file to verify we can actually write to it
    try:
        with open(log_file, 'a') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                f.write("")
                f.flush()
                os.fsync(f.fileno())
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except (IOError, OSError) as e:
        if e.errno in (errno.EACCES, errno.EPERM):
            raise PermissionError(f"Cannot write to log file: {log_file}")
        raise

def _reinit_logger_after_fork():
    """Reinitialize logger after fork to ensure proper file handles."""
    global _logger_pid, logger
    current_pid = os.getpid()
    if _logger_pid is not None and _logger_pid != current_pid:
        # Get debug output settings from existing handlers
        debug_stdout = False
        if logger.handlers:
            for handler in logger.handlers:
                if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                    debug_stdout = True
                    break
        
        if debug_stdout:
            sys.stdout.write(f"DEBUG - Fork detected: Reinitializing logger for PID {current_pid}\n")
            sys.stdout.flush()
        
        # Get a fresh logger instance
        logger = logging.getLogger("touchfs")
        
        if _file_handler:
            try:
                # Close existing handler
                _file_handler.close()
                logger.removeHandler(_file_handler)
                if debug_stdout:
                    sys.stdout.write("DEBUG - Closed and removed existing file handler\n")
                    sys.stdout.flush()
            except Exception as e:
                sys.stdout.write(f"WARNING - Error closing file handler: {str(e)}\n")
                sys.stdout.flush()
        
        # Setup new handler with same debug output setting
        setup_logging(debug_stdout=debug_stdout)
        _logger_pid = current_pid

class ImmediateFileHandler(logging.FileHandler):
    """A FileHandler that flushes immediately after each write with file locking."""
    _warning_counter = 0  # Class-level counter for warnings
    _initial_warnings = 5  # Show first N warnings
    _warning_threshold = 10  # Then show every Nth warning
    _threshold_message_shown = False  # Track if we've shown the threshold message
    
    def __init__(self, filename, mode='a', encoding=None, delay=False, debug_stdout=False):
        """Initialize the handler with verification."""
        self.debug_stdout = debug_stdout
        # Check write permission before initializing
        path = Path(filename)
        _check_file_writable(path, check_parent=True)  # Need parent dir writable for rotation
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
        except (IOError, OSError) as e:
            if e.errno in (errno.EACCES, errno.EPERM):
                if self.debug_stdout:
                    sys.stdout.write(f"ERROR - File handler permission denied for {self.baseFilename}\n")
                    sys.stdout.flush()
                raise PermissionError(f"Cannot write to log file {self.baseFilename}: Permission denied")
            error_msg = f"Cannot access log file {self.baseFilename}: {str(e)}"
            if self.debug_stdout:
                sys.stdout.write(f"ERROR - File handler IO error: {error_msg}\n")
                sys.stdout.flush()
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Cannot access log file {self.baseFilename}: {str(e)}"
            if self.debug_stdout:
                sys.stdout.write(f"ERROR - File handler unexpected error: {error_msg}\n")
                sys.stdout.flush()
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
                    ImmediateFileHandler._warning_counter += 1
                    should_warn = False
                    
                    if ImmediateFileHandler._warning_counter <= ImmediateFileHandler._initial_warnings:
                        should_warn = True
                    elif not ImmediateFileHandler._threshold_message_shown:
                        should_warn = True
                        ImmediateFileHandler._threshold_message_shown = True
                        warning_msg = f"Reducing write verification warnings frequency - will now show every {ImmediateFileHandler._warning_threshold}th warning ({error_context})"
                    elif ImmediateFileHandler._warning_counter % ImmediateFileHandler._warning_threshold == 0:
                        should_warn = True
                        
                    if should_warn:
                        warning_msg = warning_msg if ImmediateFileHandler._threshold_message_shown else f"Write verification warning - file size did not increase ({error_context})"
                        if self.debug_stdout:
                            sys.stdout.write(f"WARNING - File handler write verification: {warning_msg}\n")
                            sys.stdout.flush()
            finally:
                fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN)
                
        except (IOError, OSError) as e:
            if e.errno in (errno.EACCES, errno.EPERM):
                error_msg = f"Permission denied: {self.baseFilename}"
                if self.debug_stdout:
                    sys.stdout.write(f"ERROR - File handler permission denied: {error_msg}\n")
                    sys.stdout.flush()
                raise PermissionError(error_msg)
            error_msg = f"Logging failed ({error_context}): {str(e)}"
            if self.debug_stdout:
                sys.stdout.write(f"ERROR - File handler IO error: {error_msg}\n")
                sys.stdout.flush()
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Logging failed ({error_context}): {str(e)}"
            if self.debug_stdout:
                sys.stdout.write(f"ERROR - File handler unexpected error: {error_msg}\n")
                sys.stdout.flush()
            raise RuntimeError(error_msg)

def setup_logging(force_new: bool = False, test_tag: Optional[str] = None, debug_stdout: bool = False) -> logging.Logger:
    """Setup logging with full details at DEBUG level. Logs are rotated (cleared)
    for each new invocation to ensure clean logs that can be accessed through
    the proc plugin.
    
    The function performs the following steps:
    1. Creates log directory if it doesn't exist
    2. Rotates existing log file with incremented suffix
    3. Sets up new log file with proper permissions
    4. Validates ability to write to new log file
    
    Args:
        force_new: Force creation of new logger instance
        test_tag: Optional tag for test runs
        debug_stdout: Enable debug output to stdout (used in foreground mode)
        
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
        if debug_stdout:
            sys.stdout.write(f"DEBUG - Fork detected: Old PID {_logger_pid}, New PID {current_pid}\n")
            sys.stdout.flush()
    
    # Create or get logger with error handling
    try:
        # Get a fresh logger instance
        global logger
        logger = logging.getLogger("touchfs")
        
        # Store current PID
        _logger_pid = current_pid
        
        # Configure logger with error handling
        try:
            logger.setLevel(logging.DEBUG)
            # Remove any existing handlers to prevent duplicates
            logger.handlers.clear()
            # Ensure logger propagates and isn't disabled by parent loggers
            logger.propagate = True
            logging.getLogger().setLevel(logging.DEBUG)  # Set root logger to DEBUG
        except Exception as e:
            if debug_stdout:
                sys.stdout.write(f"WARNING - Logger configuration error: {str(e)}\n")
                sys.stdout.flush()
            # Continue since these are non-critical operations
    except Exception as e:
        if debug_stdout:
            sys.stdout.write(f"ERROR - Failed to initialize logger: {str(e)}\n")
            sys.stdout.flush()
        raise RuntimeError(f"Failed to initialize logger: {str(e)}")

    # Setup detailed console handler for stdout if debug_stdout is enabled
    if debug_stdout:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter(
            '%(filename)s:%(lineno)d - %(levelname)s - %(message)s'
        ))
        logger.addHandler(console_handler)

    # Force flush after each log
    # Add immediate flush handler to force flush after each log
    for handler in logger.handlers:
        handler.setFormatter(logging.Formatter('%(filename)s:%(lineno)d - %(levelname)s - %(message)s'))

    # Try system log directory first
    global system_log_dir
    if not system_log_dir:
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
                    if debug_stdout:
                        sys.stdout.write(f"INFO - Log setup: Using system log file {log_file}\n")
                        sys.stdout.flush()
                else:
                    # Try creating the file to verify write access
                    try:
                        _verify_file_creation(log_file)
                        if debug_stdout:
                            sys.stdout.write(f"INFO - Log setup: Created system log file {log_file}\n")
                            sys.stdout.flush()
                    except:
                        raise PermissionError("Cannot write to system log file")
            else:
                raise PermissionError("No write permission for system log directory")
        except Exception as e:
            if debug_stdout:
                sys.stdout.write(f"WARNING - Log setup: System log failed, falling back to home directory: {str(e)}\n")
                sys.stdout.flush()
            raise

    except Exception:
        # Fall back to home directory
        log_dir = os.path.dirname(home_log_file)
        log_file = Path(home_log_file)
        if debug_stdout:
            sys.stdout.write(f"INFO - Log setup: Using home directory log file {log_file}\n")
            sys.stdout.flush()
    
    # Verify we can rotate the log file if it exists
    _verify_file_rotation(log_file)
        
    # Setup detailed formatter for file logging
    detailed_formatter = logging.Formatter('%(filename)s:%(lineno)d - %(levelname)s - %(message)s')
    
    # Rotate existing log if it exists
    if log_file.exists():
        try:
            # Read existing content in case we need to restore it
            with open(log_file, 'r') as f:
                original_content = f.read()
            
            # Find next available suffix number in the current directory
            parent_dir = log_file.parent
            suffix = 1
            while (parent_dir / f"touchfs.log.{suffix}").exists():
                suffix += 1
            
            # Rename existing log file with suffix
            backup_path = parent_dir / f"touchfs.log.{suffix}"
            log_file.rename(backup_path)
            
            # Verify backup was created
            if not backup_path.exists():
                if debug_stdout:
                    sys.stdout.write(f"ERROR - Log rotation: Failed to create backup file {backup_path}\n")
                    sys.stdout.flush()
                raise RuntimeError("Failed to create backup log file")
        except (IOError, OSError) as e:
            if e.errno in (errno.EACCES, errno.EPERM):
                error_msg = f"Permission denied: {log_file}"
                if debug_stdout:
                    sys.stdout.write(f"ERROR - Log rotation: Permission denied for {log_file}\n")
                    sys.stdout.flush()
                raise PermissionError(error_msg)
            error_msg = f"Failed to rotate log file: {str(e)}"
            if debug_stdout:
                sys.stdout.write(f"ERROR - Log rotation: {error_msg}\n")
                sys.stdout.flush()
            # If rotation fails, try to restore original content
            try:
                with open(log_file, 'w') as f:
                    f.write(original_content)
            except Exception as restore_error:
                error_msg = f"Failed to rotate log AND restore original: {str(restore_error)}"
                if debug_stdout:
                    sys.stdout.write(f"ERROR - Log rotation: {error_msg}\n")
                    sys.stdout.flush()
                raise RuntimeError(error_msg)
            raise RuntimeError(error_msg)
    
    # Setup file handler for single log file with immediate flush in append mode
    try:
        file_handler = ImmediateFileHandler(
            str(log_file),  # Convert Path to string
            mode='a',
            debug_stdout=debug_stdout
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # Test write to new log file with robust error handling
        try:
            test_record = logging.LogRecord(
                "touchfs", logging.INFO, __file__, 0,
                "Logger initialized with rotation", (), None
            )
            if debug_stdout:
                sys.stdout.write("DEBUG - Attempting test write to log file\n")
                sys.stdout.flush()
            
            file_handler.emit(test_record)
            
            # Verify the write actually occurred
            if not os.path.exists(log_file):
                error_msg = f"Log file does not exist after test write: {log_file}"
                if debug_stdout:
                    sys.stdout.write(f"ERROR - Log initialization: {error_msg}\n")
                    sys.stdout.flush()
                raise RuntimeError(error_msg)
            
            if os.path.getsize(log_file) == 0:
                error_msg = f"Log file is empty after test write: {log_file}"
                if debug_stdout:
                    sys.stdout.write(f"ERROR - Log initialization: {error_msg}\n")
                    sys.stdout.flush()
                raise RuntimeError(error_msg)
                
            if debug_stdout:
                sys.stdout.write("DEBUG - Test write successful\n")
                sys.stdout.flush()
                
        except Exception as e:
            error_msg = f"Test write failed: {str(e)}"
            if debug_stdout:
                sys.stdout.write(f"ERROR - Log initialization: {error_msg}\n")
                sys.stdout.flush()
            raise RuntimeError(error_msg)
        
        # Add handler to logger
        logger.addHandler(file_handler)
        
        # Store handler in global to prevent garbage collection
        global _file_handler
        _file_handler = file_handler
        
        return logger
        
    except Exception as e:
        error_msg = f"Failed to setup/test file handler: {str(e)}"
        if debug_stdout:
            sys.stdout.write(f"ERROR - Log initialization: {error_msg}\n")
            sys.stdout.flush()
        if isinstance(e, PermissionError):
            raise
        raise RuntimeError(error_msg)
