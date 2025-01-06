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
                # Include both tag-specific lines and filesystem lines
                if tag in line or "filesystem" in line or "Creating file:" in line:
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
        
    Raises:
        pytest.Failed: If mount operation fails
    """
    import sys
    
    # Generate unique tag for this mount operation
    tag = f"test_mount_{os.urandom(4).hex()}"
    
    # Pass tag through environment variable
    env = os.environ.copy()
    env.update({
        'TOUCHFS_TEST_TAG': tag,
        'TOUCHFS_FSNAME': 'touchfs'
    })
    # Use sys.executable to get correct Python interpreter
    mount_process = subprocess.Popen(
        [sys.executable, '-c', f'from touchfs.cli.touchfs_cli import main; main()', 'mount', mount_point, '--foreground'],  # --foreground (-f) enables debug output
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )
    
    # Wait for mount with timeout
    start_time = time.time()
    timeout = 5  # seconds
    while time.time() - start_time < timeout:
        if os.path.exists(mount_point) and os.path.ismount(mount_point):
            break
        time.sleep(0.1)
        
        # Check if process failed
        if mount_process.poll() is not None:
            stdout, stderr = mount_process.communicate()
            pytest.fail(f"Mount process failed: {stderr.decode()}")
    else:
        mount_process.terminate()
        pytest.fail(f"Timeout waiting for mount at {mount_point}")
        
    return mount_process, tag

def verify_mount_in_logs(log_lines: list[str], tag: str) -> None:
    """Verify that the mount operation is recorded in logs.
    
    Args:
        log_lines: List of log lines to check
        tag: Operation tag to look for
        
    Raises:
        pytest.Failed: If mount verification fails
    """
    # Look for both mount initiation and completion
    mount_start = False
    mount_success = False
    
    for line in log_lines:
        if tag not in line and "filesystem" not in line:
            continue
        if "Mounting filesystem" in line:
            mount_start = True
        if "filesystem initializing in FUSE process" in line:
            mount_success = True
            
    if not mount_start:
        pytest.fail(f"No mount operation found in logs for tag {tag}")
    if not mount_success:
        pytest.fail(f"Filesystem initialization not found in logs for tag {tag}")

def test_mounted_operations():
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
            
            # 4. Verify mount in logs and filesystem
            touchfs_dir = Path(mount_point) / ".touchfs"
            assert touchfs_dir.is_dir(), ".touchfs directory not found in mounted filesystem"
            
            # Give some time for mount to complete and logs to be written
            max_attempts = 10
            for _ in range(max_attempts):
                initial_logs = get_log_section(tag)
                try:
                    verify_mount_in_logs(initial_logs, tag)
                    break
                except Exception:  # Catch any exception from pytest.fail()
                    if _ == max_attempts - 1:  # On last attempt
                        # Print all logs for debugging
                        print("\nAll logs for tag:", tag)
                        for line in initial_logs:
                            print(line)
                        raise  # Re-raise the exception
                    time.sleep(0.5)
            
            # 5. Perform test-specific operations
            test_file = Path(mount_point) / "test.txt"
            test_file.touch()
            assert test_file.exists(), "Test file was not created"
            
            # 6. Verify operations in logs
            # Give some time for file creation logs to be written
            max_attempts = 10
            for _ in range(max_attempts):
                operation_logs = get_log_section(tag)
                file_created = False
                for line in operation_logs:
                    if "Creating file:" in line and "test.txt" in line:
                        file_created = True
                        break
                if file_created:
                    break
                if _ == max_attempts - 1:  # On last attempt
                    # Print all logs for debugging
                    print("\nAll logs for tag:", tag)
                    for line in operation_logs:
                        print(line)
                time.sleep(0.5)
            
            assert file_created, "File creation not found in logs"
            
        finally:
            # 7. Cleanup
            subprocess.run(['fusermount', '-u', mount_point], check=True)
            mount_process.terminate()
            mount_process.wait()

if __name__ == '__main__':
    pytest.main([__file__])
