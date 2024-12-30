import os
import time
import pytest
import subprocess
import tempfile
from touchfs.config.logger import setup_logging

@pytest.fixture(scope="session", autouse=True)
def setup_test_logging():
    """Initialize logging before any tests run."""
    setup_logging()

@pytest.fixture(scope="function")
def mount_point():
    """Create a temporary directory for mounting the filesystem."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture(scope="function")
def mounted_fs(mount_point):
    """Mount the filesystem and yield the mount point."""
    # Start the filesystem process
    process = subprocess.Popen(
        ["python3", "-m", "touchfs", mount_point],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        env=dict(os.environ, TOUCHFS_PROMPT="empty", OPENAI_API_KEY="dummy")  # Provide empty prompt and dummy API key
    )
    
    # Wait for filesystem to be mounted and check for errors
    time.sleep(2)
    
    # Check if process is still running
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        raise RuntimeError(f"Failed to mount filesystem:\nstdout: {stdout}\nstderr: {stderr}")
    
    # Verify mount point is accessible
    try:
        os.listdir(mount_point)
    except Exception as e:
        process.terminate()
        process.wait()
        raise RuntimeError(f"Mount point not accessible: {e}")
    
    try:
        yield mount_point
    finally:
        # Cleanup: Unmount filesystem and terminate process
        subprocess.run(["fusermount", "-u", mount_point])
        process.terminate()
        process.wait()

@pytest.fixture(scope="function")
def mounted_fs_foreground(mount_point):
    """Mount the filesystem in foreground mode and yield the mount point."""
    # Start the filesystem process
    process = subprocess.Popen(
        ["python3", "-m", "touchfs", mount_point, "-f"],  # Added foreground flag
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        env=dict(os.environ, TOUCHFS_PROMPT="empty", OPENAI_API_KEY="dummy")
    )
    
    # Wait for filesystem to be mounted and check for errors
    time.sleep(2)
    
    # Check if process is still running
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        raise RuntimeError(f"Failed to mount filesystem:\nstdout: {stdout}\nstderr: {stderr}")
    
    # Verify mount point is accessible
    try:
        os.listdir(mount_point)
    except Exception as e:
        process.terminate()
        process.wait()
        raise RuntimeError(f"Mount point not accessible: {e}")
    
    try:
        yield mount_point
    finally:
        # Cleanup: Unmount filesystem and terminate process
        subprocess.run(["fusermount", "-u", mount_point])
        process.terminate()
        process.wait()

@pytest.fixture(scope="function")
def mounted_fs_debug(mount_point):
    """Mount the filesystem in debug mode and yield the mount point."""
    # Start the filesystem process
    process = subprocess.Popen(
        ["python3", "-m", "touchfs", mount_point, "-f", "--debug"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        env=dict(os.environ, TOUCHFS_PROMPT="empty", OPENAI_API_KEY="dummy")
    )
    
    # Wait for filesystem to be mounted and check for errors
    time.sleep(2)
    
    # Check if process is still running
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        raise RuntimeError(f"Failed to mount filesystem:\nstdout: {stdout}\nstderr: {stderr}")
    
    # Verify mount point is accessible
    try:
        os.listdir(mount_point)
    except Exception as e:
        process.terminate()
        process.wait()
        raise RuntimeError(f"Mount point not accessible: {e}")
    
    try:
        yield mount_point, process  # Also yield process to check debug output
    finally:
        # Cleanup: Unmount filesystem and terminate process
        subprocess.run(["fusermount", "-u", mount_point])
        process.terminate()
        process.wait()
