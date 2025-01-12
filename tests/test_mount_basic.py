"""Basic tests for touchfs mount functionality."""
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from touchfs.config.logger import setup_logging
from touchfs.cli.mount import get_mounted_touchfs

def test_get_mounted_touchfs():
    """Test get_mounted_touchfs function with mocked proc files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        proc_dir = Path(tmp_dir) / "proc"
        proc_dir.mkdir()
        
        # Create mock /proc/mounts
        mounts_file = proc_dir / "mounts"
        mounts_content = """
rootfs / rootfs rw 0 0
touchfs /mnt/test1 fuse rw,nosuid,nodev 0 0
touchfs /mnt/test2 fuse rw,nosuid,nodev 0 0
"""
        mounts_file.write_text(mounts_content)
        
        # Create mock process directories
        pid1_dir = proc_dir / "1234"
        pid1_dir.mkdir()
        (pid1_dir / "mountinfo").write_text("/mnt/test1\n")
        (pid1_dir / "cmdline").write_text("python\0touchfs\0mount\0/mnt/test1\0")
        
        pid2_dir = proc_dir / "5678"
        pid2_dir.mkdir()
        (pid2_dir / "mountinfo").write_text("/mnt/test2\n")
        (pid2_dir / "cmdline").write_text("python\0touchfs\0mount\0/mnt/test2\0")
        
        # Mock os functions to use our test directory
        with patch('touchfs.cli.mount.utils.os.listdir', return_value=['1234', '5678']), \
             patch('touchfs.cli.mount.utils.open', create=True) as mock_open:
            
            def mock_open_file(path, *args, **kwargs):
                if path == '/proc/mounts':
                    return open(mounts_file, *args, **kwargs)
                elif path == '/proc/1234/mountinfo':
                    return open(pid1_dir / "mountinfo", *args, **kwargs)
                elif path == '/proc/1234/cmdline':
                    return open(pid1_dir / "cmdline", *args, **kwargs)
                elif path == '/proc/5678/mountinfo':
                    return open(pid2_dir / "mountinfo", *args, **kwargs)
                elif path == '/proc/5678/cmdline':
                    return open(pid2_dir / "cmdline", *args, **kwargs)
                raise FileNotFoundError(f"Mock file not found: {path}")
            
            mock_open.side_effect = mock_open_file
            
            # Test the function
            mounted = get_mounted_touchfs()
            assert len(mounted) == 2
            assert ('/mnt/test1', '1234', 'python touchfs mount /mnt/test1') in mounted
            assert ('/mnt/test2', '5678', 'python touchfs mount /mnt/test2') in mounted

def test_get_mounted_touchfs_no_mounts():
    """Test get_mounted_touchfs when no filesystems are mounted."""
    with patch('touchfs.cli.mount.utils.open', create=True) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = ""
        mounted = get_mounted_touchfs()
        assert len(mounted) == 0

def test_get_mounted_touchfs_error_handling():
    """Test get_mounted_touchfs error handling."""
    with patch('touchfs.cli.mount.utils.open', side_effect=IOError("Mock error")):
        mounted = get_mounted_touchfs()
        assert len(mounted) == 0

if __name__ == '__main__':
    pytest.main([__file__])
