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

def test_log_rotation(caplog):
    """Test log file rotation and error handling"""
    log_dir = Path("/var/log/touchfs")
    log_path = log_dir / "touchfs.log"
    caplog.set_level(logging.INFO)
    
    # 1. Create initial log file with content
    logger = setup_logging()
    logger.info("Initial test message")
    verify_log_file(log_path, should_exist=True, min_size=1)
    
    # 2. Trigger rotation by setting up logging again
    logger = setup_logging()
    logger.info("Message after rotation")
    
    # 3. Verify rotation occurred
    verify_log_file(log_path, should_exist=True, min_size=1)
    rotated_files = list(log_dir.glob("touchfs.log.*"))
    assert len(rotated_files) > 0, "No rotated log files found"
    
    # 4. Test permission error handling
    original_mode = log_path.stat().st_mode
    try:
        log_path.chmod(0o444)  # Read-only
        with pytest.raises(PermissionError):
            setup_logging()
    finally:
        log_path.chmod(original_mode)
    
    # 5. Test write verification
    logger = setup_logging()
    logger.info("Test message")
    verify_log_file(log_path, should_exist=True, min_size=1)
    
    # Cleanup
    for f in log_dir.glob("touchfs.log.*"):
        try:
            f.unlink()
        except Exception as e:
            pytest.fail(f"Failed to cleanup rotated files: {str(e)}")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
