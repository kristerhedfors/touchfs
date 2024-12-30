"""Template for live TouchFS mount testing with log verification.

This module serves as a template for tests that need to:
1. Mount a live TouchFS filesystem
2. Perform operations on the mounted filesystem
3. Verify operations through both filesystem checks and logs
4. Properly cleanup after testing

Key Features:
- Early log access verification
- Mount-specific log identification
- Safe log reading practices
- Proper cleanup and unmounting

Usage:
1. Copy this template for new mount-based tests
2. Implement specific test operations in the test function
3. Use the log verification utilities to check operation results
4. Follow the pattern of early and late log verification
"""
import os
import tempfile
import subprocess
import time
import pytest
from pathlib import Path
from typing import Optional, Tuple
from touchfs.config.logger import setup_logging

def get_log_section(tag: str, max_lines: int = 50) -> list[str]:
    """Safely read relevant log lines for the specific mount operation.
    
    Args:
        tag: Unique identifier for this mount operation
        max_lines: Maximum number of lines to read (default: 50)
        
    Returns:
        List of relevant log lines
    """
    log_path = "/var/log/touchfs/touchfs.log"
    relevant_lines = []
    
    try:
        with open(log_path, 'r') as f:
            for line in f:
                if tag in line:
                    relevant_lines.append(line.strip())
                    if len(relevant_lines) >= max_lines:
                        break
        return relevant_lines
    except Exception as e:
        pytest.fail(f"Failed to read logs: {e}")

def verify_log_access() -> None:
    """Verify that we can access and read the log file.
    
    Raises:
        pytest.Failed: If log access verification fails
    """
    log_path = "/var/log/touchfs/touchfs.log"
    if not os.path.exists(log_path):
        pytest.fail(f"Log file {log_path} does not exist")
    try:
        with open(log_path, 'r') as f:
            # Just try to read first line to verify access
            f.readline()
    except Exception as e:
        pytest.fail(f"Cannot read log file: {e}")

def mount_filesystem(mount_point: str) -> Tuple[subprocess.Popen, str]:
    """Mount the filesystem and return the process and operation tag.
    
    Args:
        mount_point: Directory where the filesystem should be mounted
        
    Returns:
        Tuple of (mount process, operation tag)
    """
    # Generate unique tag for this mount operation
    tag = f"test_mount_{os.urandom(4).hex()}"
    
    # Pass tag through environment variable
    env = os.environ.copy()
    env['TOUCHFS_TEST_TAG'] = tag
    
    mount_process = subprocess.Popen(
        ['python', '-c', f'from touchfs.cli.main import main; main("{mount_point}", foreground=True)'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )
    time.sleep(2)  # Give it time to mount
    
    if not os.path.exists(mount_point):
        mount_process.terminate()
        pytest.fail("Mount point does not exist after mount attempt")
        
    return mount_process, tag

def verify_mount_in_logs(log_lines: list[str], tag: str) -> None:
    """Verify that the mount operation is recorded in logs.
    
    Args:
        log_lines: List of log lines to check
        mount_point: Mount point to look for
        
    Raises:
        pytest.Failed: If mount verification fails
    """
    mount_messages = [line for line in log_lines if "Mounting filesystem" in line]
    if not mount_messages:
        pytest.fail(f"No mount operation found in logs for tag {tag}")

def test_mounted_operations(caplog):
    """Template test demonstrating proper mount testing pattern."""
    # 1. Early log access verification
    verify_log_access()
    
    # 2. Setup logging
    logger = setup_logging()
    
    # 3. Create mount point and mount filesystem
    with tempfile.TemporaryDirectory(prefix='touchfs_test_') as mount_point:
        try:
            # Mount filesystem with unique tag
            mount_process, tag = mount_filesystem(mount_point)
            
            # 4. Verify mount in logs
            initial_logs = get_log_section(tag)
            verify_mount_in_logs(initial_logs, tag)
            
            # 5. Perform test-specific operations
            test_file = Path(mount_point) / "test.txt"
            test_file.touch()
            assert test_file.exists(), "Test file was not created"
            
            # 6. Verify operations in logs
            operation_logs = get_log_section(tag)
            # Verify test-specific log entries
            file_created = False
            for line in operation_logs:
                if f"Creating file: /test.txt" in line:
                    file_created = True
                    break
            assert file_created, "File creation not found in logs"
            
        finally:
            # 7. Cleanup
            subprocess.run(['fusermount', '-u', mount_point], check=True)
            mount_process.terminate()
            mount_process.wait()

if __name__ == '__main__':
    pytest.main([__file__])
