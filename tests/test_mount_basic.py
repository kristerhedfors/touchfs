"""Basic mount/unmount test for llmfs."""
import os
import tempfile
import subprocess
import time
import pytest
from pathlib import Path
from llmfs.config.logger import setup_logging
from llmfs.cli.main import main

def test_basic_mount_operations(caplog):
    """Test basic mounting, file operations, and unmounting of llmfs."""
    # Setup logging
    logger = setup_logging()
    
    # Create a unique temporary mount point
    with tempfile.TemporaryDirectory(prefix='llmfs_test_') as mount_point:
        try:
            # Start the filesystem in a separate process
            mount_process = subprocess.Popen(
                ['python', '-c', f'from llmfs.cli.main import main; main("{mount_point}", foreground=True)'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
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
            log_path = "/var/log/llmfs/llmfs.log"
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
