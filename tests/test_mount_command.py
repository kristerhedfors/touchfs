"""Tests for mount command functionality."""
import os
import subprocess
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from touchfs.cli.mount import mount_main, get_mounted_touchfs

def test_help_output():
    """Test that --help displays usage information."""
    result = subprocess.run(['python', '-m', 'touchfs', 'mount', '--help'],
                          capture_output=True, 
                          text=True)
    assert result.returncode == 0
    assert 'usage:' in result.stdout
    assert 'mountpoint' in result.stdout
    assert '--foreground' in result.stdout
    assert '--filesystem-generation-prompt' in result.stdout
    assert 'Mount a touchfs filesystem' in result.stdout

def test_list_mounted():
    """Test that running mount without arguments lists mounted filesystems."""
    result = subprocess.run(['python', '-m', 'touchfs', 'mount'],
                          capture_output=True, 
                          text=True,
                          env=dict(os.environ, TOUCHFS_FSNAME="touchfs"))
    assert result.returncode == 0
    assert any(msg in result.stdout for msg in [
        'Currently mounted touchfs filesystems:',
        'No touchfs filesystems currently mounted'
    ])

def test_nonexistent_mountpoint():
    """Test mounting to non-existent directory fails."""
    with tempfile.TemporaryDirectory(prefix='touchfs_test_') as base_dir:
        nonexistent = os.path.join(base_dir, "nonexistent")
        result = subprocess.run(['python', '-m', 'touchfs', 'mount', nonexistent],
                              capture_output=True,
                              text=True)
        assert result.returncode != 0
        assert "No such file or directory" in result.stderr

@patch('touchfs.cli.mount.cli.FUSE')
@patch('touchfs.cli.mount.cli.Memory')
def test_mount_with_prompt(mock_memory, mock_fuse, tmp_path):
    """Test mounting with filesystem generation prompt."""
    mount_point = tmp_path / "workspace"
    mount_point.mkdir()
    
    # Mock filesystem generation
    mock_memory_instance = MagicMock()
    mock_memory.return_value = mock_memory_instance
    
    # Call mount_main directly with filesystem generation prompt
    result = mount_main(
        mountpoint=str(mount_point),
        filesystem_generation_prompt="Create a simple project with src and docs directories",
        yes=True  # Auto-confirm to avoid interactive prompt
    )
    
    assert result == 0
    mock_memory.assert_called_once()
    mock_fuse.assert_called_once()

@patch('touchfs.cli.mount.cli.FUSE')
@patch('touchfs.cli.mount.cli.Memory')
def test_mount_options(mock_memory, mock_fuse, tmp_path):
    """Test various mount options."""
    mount_point = tmp_path / "workspace"
    mount_point.mkdir()
    
    # Mock filesystem components
    mock_memory_instance = MagicMock()
    mock_memory.return_value = mock_memory_instance
    
    # Call mount_main with various options
    result = mount_main(
        mountpoint=str(mount_point),
        allow_other=True,
        allow_root=True,
        nothreads=True,
        nonempty=True
    )
    
    assert result == 0
    mock_memory.assert_called_once()
    # Verify FUSE options
    _, _, kwargs = mock_fuse.mock_calls[0]
    assert kwargs['allow_other'] is True
    assert kwargs['allow_root'] is True
    assert kwargs['nothreads'] is True
    assert kwargs['nonempty'] is True

def test_mount_logging(tmp_path):
    """Test mount command logging setup."""
    mount_point = tmp_path / "workspace"
    mount_point.mkdir()
    
    with patch('touchfs.cli.mount.cli.setup_logging') as mock_setup_logging:
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger
        
        with patch('touchfs.cli.mount.cli.FUSE'), \
             patch('touchfs.cli.mount.cli.Memory'):
            
            result = mount_main(
                mountpoint=str(mount_point),
                foreground=True
            )
            
            assert result == 0
            mock_setup_logging.assert_called_once()
            mock_logger.debug.assert_any_call("==== TouchFS Debug Logging Started ====")

if __name__ == '__main__':
    pytest.main([__file__])
