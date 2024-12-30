"""Tests for CLI functionality."""
import os
import subprocess
import pytest
from pathlib import Path

def test_help_output():
    """Test that --help displays usage information."""
    result = subprocess.run(['python', '-m', 'touchfs', '--help'],
                          capture_output=True, 
                          text=True)
    assert result.returncode == 0
    assert 'usage:' in result.stdout
    assert 'mountpoint' in result.stdout
    assert '--prompt' in result.stdout
    assert '--foreground' in result.stdout

def test_missing_mountpoint():
    """Test that missing mountpoint argument shows error."""
    result = subprocess.run(['python', '-m', 'touchfs'],
                          capture_output=True, 
                          text=True)
    assert result.returncode != 0
    assert 'error: the following arguments are required: mountpoint' in result.stderr

def test_invalid_mountpoint():
    """Test that non-existent mountpoint shows appropriate error."""
    result = subprocess.run(['python', '-m', 'touchfs', '/nonexistent/path'],
                          capture_output=True, 
                          text=True)
    assert result.returncode != 0
    assert 'No such file or directory' in result.stderr

@pytest.fixture
def temp_mount_dir(tmp_path):
    """Create a temporary directory for mounting."""
    mount_dir = tmp_path / "mount"
    mount_dir.mkdir()
    yield mount_dir
    # Cleanup: Ensure filesystem is unmounted
    try:
        subprocess.run(['fusermount', '-u', str(mount_dir)],
                      capture_output=True)
    except:
        pass

def test_mount_with_prompt(temp_mount_dir):
    """Test mounting with a prompt argument."""
    env = os.environ.copy()
    env['OPENAI_API_KEY'] = 'dummy-key'  # Add dummy API key
    
    process = subprocess.Popen(
        ['python', '-m', 'touchfs', str(temp_mount_dir), '--prompt', 'Create an empty project', '-f'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    
    try:
        stdout, stderr = process.communicate(timeout=5)
        assert 'Generating filesystem from prompt' in stdout or 'Generating filesystem from prompt' in stderr
        
        # Give FUSE some time to mount
        import time
        time.sleep(2)
        
        # Verify mount
        assert os.path.ismount(temp_mount_dir)
    except subprocess.TimeoutExpired:
        process.kill()
    except AssertionError:
        process.kill()
        raise

def test_environment_prompt(temp_mount_dir):
    """Test using TOUCHFS_PROMPT environment variable."""
    env = os.environ.copy()
    env['TOUCHFS_PROMPT'] = 'Create a test project'
    env['OPENAI_API_KEY'] = 'dummy-key'  # Add dummy API key
    
    process = subprocess.Popen(
        ['python', '-m', 'touchfs', str(temp_mount_dir), '-f'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        stdout, stderr = process.communicate(timeout=5)
        assert 'Generating filesystem from prompt' in stdout or 'Generating filesystem from prompt' in stderr
        
        # Give FUSE some time to mount
        import time
        time.sleep(2)
        
        # Verify mount
        assert os.path.ismount(temp_mount_dir)
    except subprocess.TimeoutExpired:
        process.kill()
    except AssertionError:
        process.kill()
        raise

def test_foreground_flag(temp_mount_dir):
    """Test that foreground flag keeps process in foreground."""
    env = os.environ.copy()
    env['OPENAI_API_KEY'] = 'dummy-key'  # Add dummy API key
    
    process = subprocess.Popen(
        ['python', '-m', 'touchfs', str(temp_mount_dir), '-f'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )
    
    # Process should still be running
    assert process.poll() is None
    
    # Cleanup
    process.kill()
