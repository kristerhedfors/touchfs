"""Basic mount/unmount test for touchfs."""
import os
import tempfile
import subprocess
import time
import pytest
from pathlib import Path
from touchfs.config.logger import setup_logging
from touchfs.cli.mount_command import get_mounted_touchfs


def test_list_mounted_filesystems():
    """Test listing mounted touchfs filesystems."""
    # Create a unique temporary mount point
    with tempfile.TemporaryDirectory(prefix='touchfs_test_') as mount_point:
        try:
            # Start the filesystem in a separate process
            mount_process = subprocess.Popen(
                ['python', '-c', f'from touchfs.cli.touchfs_cli import main; main()', 'mount', mount_point, '--foreground'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=dict(os.environ, TOUCHFS_FSNAME="touchfs")
            )
            
            # Give it a moment to mount
            time.sleep(2)
            
            # Check if mount point is listed
            mounted = get_mounted_touchfs()
            assert mount_point in mounted, f"Mount point {mount_point} not found in mounted filesystems"
            
            # Test the mount command with no arguments
            result = subprocess.run(
                ['python', '-c', 'from touchfs.cli.touchfs_cli import main; main()', 'mount'],
                capture_output=True,
                text=True,
                env=dict(os.environ, TOUCHFS_FSNAME="touchfs")
            )
            assert mount_point in result.stdout, f"Mount point {mount_point} not found in mount command output"
            
        finally:
            # Cleanup: Unmount the filesystem
            subprocess.run(['fusermount', '-u', mount_point], check=True)
            mount_process.terminate()
            mount_process.wait()

def test_basic_mount_operations(caplog):
    """Test basic mounting, file operations, and unmounting of touchfs."""
    # Setup logging
    logger = setup_logging()
    
    # Create a unique temporary mount point
    with tempfile.TemporaryDirectory(prefix='touchfs_test_') as mount_point:
        try:
            # Start the filesystem in a separate process using touchfs mount command
            mount_process = subprocess.Popen(
                ['python', '-c', f'from touchfs.cli.touchfs_cli import main; main()', 'mount', mount_point, '--foreground'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=dict(os.environ, TOUCHFS_FSNAME="touchfs")
            )
            
            # Give it a moment to mount
            time.sleep(2)
            
            # Check if mount was successful by checking mount point exists
            assert os.path.exists(mount_point), "Mount point does not exist"
            
            # Do a simple operation - touch a file
            test_file = Path(mount_point) / "test.txt"
            test_file.touch()
            
            # Verify the file exists
            assert test_file.exists(), "Test file was not created"
            
            # Check logs
            log_path = "/var/log/touchfs/touchfs.log"
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    log_content = f.read()
                print(f"Log contents:\n{log_content}")
            
        finally:
            # Cleanup: Unmount the filesystem
            subprocess.run(['fusermount', '-u', mount_point], check=True)
            mount_process.terminate()
            mount_process.wait()

if __name__ == '__main__':
    pytest.main([__file__])
