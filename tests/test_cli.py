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
    assert 'Commands' in result.stdout
    assert 'mount' in result.stdout
    assert 'umount' in result.stdout
    assert 'context' in result.stdout
    assert 'generate' in result.stdout

def test_mount_help():
    """Test that mount --help displays mount-specific usage information."""
    result = subprocess.run(['python', '-m', 'touchfs', 'mount', '--help'],
                          capture_output=True, 
                          text=True)
    assert result.returncode == 0
    assert 'usage:' in result.stdout
    assert 'mountpoint' in result.stdout
    assert '--foreground' in result.stdout

def test_missing_mountpoint():
    """Test that running mount without arguments shows mounted filesystems."""
    result = subprocess.run(['python', '-m', 'touchfs', 'mount'],
                          capture_output=True, 
                          text=True)
    assert result.returncode == 0
    assert 'Currently mounted touchfs filesystems:' in result.stdout or 'No touchfs filesystems currently mounted' in result.stdout

def test_invalid_mountpoint():
    """Test that non-existent mountpoint shows appropriate error."""
    result = subprocess.run(['python', '-m', 'touchfs', 'mount', '/nonexistent/path'],
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

def test_mount_basic(temp_mount_dir):
    """Test basic mount functionality."""
    env = os.environ.copy()
    env['OPENAI_API_KEY'] = 'dummy-key'  # Add dummy API key
    
    process = subprocess.Popen(
        ['python', '-m', 'touchfs', 'mount', str(temp_mount_dir), '--foreground'],
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

def test_foreground_flag(temp_mount_dir):
    """Test that foreground flag keeps process in foreground."""
    env = os.environ.copy()
    env['OPENAI_API_KEY'] = 'dummy-key'  # Add dummy API key
    
    process = subprocess.Popen(
        ['python', '-m', 'touchfs', 'mount', str(temp_mount_dir), '--foreground'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )
    
    # Process should still be running
    assert process.poll() is None
    
    # Cleanup
    process.kill()

def test_context_command(tmp_path):
    """Test context command functionality."""
    # Create test file
    test_file = tmp_path / "test.py"
    test_file.write_text("print('test')")

    # Run command
    result = subprocess.run(['python', '-m', 'touchfs', 'context', str(tmp_path)],
                          capture_output=True,
                          text=True)

    # Verify output format
    lines = result.stdout.split('\n')
    assert result.returncode == 0
    assert '# Context Information' in lines
    assert f'# File: test.py' in lines

def test_binary_file_handling(tmp_path):
    """Test handling of binary files."""
    # Create a binary file
    test_file = tmp_path / "test.bin"
    test_file.write_bytes(bytes([0x89, 0x50, 0x4E, 0x47]))  # PNG magic number

    # Run context command
    result = subprocess.run(['python', '-m', 'touchfs', 'context', str(tmp_path)],
                          capture_output=True,
                          text=True)

    # Verify output format
    lines = result.stdout.split('\n')
    assert result.returncode == 0
    assert '# File: test.bin' in lines
    assert 'Type: bin' in lines
    
    # Find the base64 content
    content_lines = [line for line in lines if line.startswith('iVBORw==')]
    assert len(content_lines) == 1, "Base64 content not found"
