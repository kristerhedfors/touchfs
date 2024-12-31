import os
import sys
import logging
import shutil
import pytest
from pathlib import Path
from touchfs.config.logger import setup_logging

def verify_log_file(path: Path, should_exist: bool = True, min_size: int = 0) -> None:
    """Verify log file exists and has content."""
    if should_exist:
        assert path.exists(), f"Log file {path} does not exist"
        size = path.stat().st_size
        assert size >= min_size, f"Log file {path} is too small: {size} bytes"
    else:
        assert not path.exists(), f"Log file {path} exists when it should not"

@pytest.fixture(autouse=True)
def _reset_logger():
    """Reset logger state before each test."""
    import touchfs.config.logger
    touchfs.config.logger._file_handler = None
    touchfs.config.logger._logger_pid = None
    touchfs.config.logger.system_log_dir = None
    yield

def test_log_rotation(caplog, tmp_path):
    """Test log file rotation and error handling"""
    # 1. Create and verify log directory
    log_dir = tmp_path / "touchfs"
    log_dir.mkdir(parents=True, exist_ok=True)
    assert log_dir.exists(), "Log directory was not created"
    assert log_dir.is_dir(), "Log directory is not a directory"
    
    # 2. Setup log path and capture
    log_path = log_dir / "touchfs.log"
    caplog.set_level(logging.INFO)
    
    # 3. Create and verify initial log file
    with open(log_path, 'w') as f:
        f.write("Initial content\n")
    verify_log_file(log_path, should_exist=True, min_size=len("Initial content\n"))
    initial_size = log_path.stat().st_size
    
    # 4. Configure and verify logger setup
    import touchfs.config.logger
    touchfs.config.logger.system_log_dir = str(log_dir)
    assert touchfs.config.logger.system_log_dir == str(log_dir), "Logger directory not set correctly"
    
    # 5. Create initial log file with content
    logger = setup_logging()
    assert logger is not None, "Logger not created"
    logger.info("Initial test message")
    verify_log_file(log_path, should_exist=True, min_size=initial_size)
    first_log_size = log_path.stat().st_size
    assert first_log_size > initial_size, "Log file size did not increase after logging"
    
    # 6. Trigger and verify rotation
    logger = setup_logging()
    assert logger is not None, "Logger not created after rotation"
    logger.info("Message after rotation")
    
    # Verify rotation occurred
    verify_log_file(log_path, should_exist=True, min_size=1)
    rotated_files = sorted(list(log_dir.glob("touchfs.log.*")))  # Sort to ensure consistent order
    assert len(rotated_files) == 2, "Expected two rotated files"
    
    # Verify first rotated file (touchfs.log.1) contains initial content
    with open(rotated_files[0], 'r') as f:
        first_rotated_content = f.read()
    assert "Initial content" in first_rotated_content, "Initial content not found in first rotated file"
    
    # Verify second rotated file (touchfs.log.2) contains first logged message
    with open(rotated_files[1], 'r') as f:
        second_rotated_content = f.read()
    assert "Initial test message" in second_rotated_content, "First logged message not found in second rotated file"
    assert rotated_files[1].stat().st_size == first_log_size, "Second rotated file size doesn't match original"
    
    # Verify current log file contains latest message
    with open(log_path, 'r') as f:
        current_content = f.read()
    assert "Message after rotation" in current_content, "Latest message not found in current log file"
    
    # 7. Test write verification
    logger = setup_logging()
    assert logger is not None, "Logger not created after permission restore"
    logger.info("Test message")
    verify_log_file(log_path, should_exist=True, min_size=1)
    final_size = log_path.stat().st_size
    assert final_size > 0, "Final log file is empty"
    
    # 9. Cleanup and verify
    rotated_files = list(log_dir.glob("touchfs.log.*"))
    for f in rotated_files:
        try:
            f.unlink()
            assert not f.exists(), f"Failed to delete rotated file: {f}"
        except Exception as e:
            pytest.fail(f"Failed to cleanup rotated file {f}: {str(e)}")
    
    # Verify all rotated files were cleaned up
    remaining_files = list(log_dir.glob("touchfs.log.*"))
    assert len(remaining_files) == 0, f"Rotated files remain after cleanup: {remaining_files}"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
