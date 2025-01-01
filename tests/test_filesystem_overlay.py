"""Tests for filesystem overlay functionality."""
import os
import pytest
import tempfile
import shutil
from pathlib import Path

from touchfs.core.memory import Memory
from touchfs.models.filesystem import FileNode

@pytest.fixture
def overlay_dir():
    """Create a temporary directory with some test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some test files and directories
        base_dir = Path(tmpdir)
        
        # Create a text file
        (base_dir / "test.txt").write_text("overlay test content")
        
        # Create a directory with files
        test_dir = base_dir / "testdir"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("file 1 content")
        (test_dir / "file2.txt").write_text("file 2 content")
        
        yield tmpdir

@pytest.fixture
def memory_fs(overlay_dir):
    """Create a Memory filesystem instance with overlay."""
    return Memory(initial_data=None, mount_point="/mnt/test", overlay_path=overlay_dir)

def test_overlay_file_reading(memory_fs):
    """Test reading files from overlay."""
    # Get overlay file node
    node = memory_fs["/test.txt"]
    assert node is not None
    assert node["type"] == "file"
    assert "overlay_path" in node
    
    # Read content through file operations
    content = memory_fs.file_ops.read("/test.txt", 1024, 0, 0)
    assert content == b"overlay test content"

def test_overlay_directory_listing(memory_fs):
    """Test directory listing with overlay."""
    # List root directory
    entries = memory_fs.dir_ops.readdir("/", 0)
    assert "test.txt" in entries
    assert "testdir" in entries
    
    # List subdirectory
    entries = memory_fs.dir_ops.readdir("/testdir", 0)
    assert "file1.txt" in entries
    assert "file2.txt" in entries

def test_overlay_file_modification(memory_fs):
    """Test modifying overlay files."""
    # Write to overlay file (should create copy in memory)
    new_content = b"modified content"
    fd = memory_fs.file_ops.open("/test.txt", os.O_RDWR)
    written = memory_fs.file_ops.write("/test.txt", new_content, 0, fd)
    assert written == len(new_content)
    
    # Read back the modified content
    content = memory_fs.file_ops.read("/test.txt", 1024, 0, fd)
    assert content == new_content
    
    # Original overlay file should be unchanged
    with open(os.path.join(memory_fs.overlay_path, "test.txt"), "r") as f:
        assert f.read() == "overlay test content"

def test_overlay_directory_operations(memory_fs):
    """Test directory operations with overlay."""
    # Should be able to create new directory even if exists in overlay
    memory_fs.dir_ops.mkdir("/testdir", 0o755)
    
    # Should see both overlay and memory files in directory
    entries = memory_fs.dir_ops.readdir("/testdir", 0)
    assert "file1.txt" in entries  # from overlay
    assert "file2.txt" in entries  # from overlay
    
    # Should not be able to remove directory that exists in overlay
    memory_fs.dir_ops.rmdir("/testdir")  # should return silently
    assert memory_fs["/testdir"] is not None  # directory should still exist

def test_overlay_new_files(memory_fs):
    """Test creating new files alongside overlay files."""
    # Create new file in root
    memory_fs.file_ops.create("/newfile.txt", 0o644)
    
    # Should see both overlay and new files
    entries = memory_fs.dir_ops.readdir("/", 0)
    assert "test.txt" in entries      # from overlay
    assert "newfile.txt" in entries   # new file
    
    # Create new file in overlay directory
    memory_fs.file_ops.create("/testdir/newfile.txt", 0o644)
    entries = memory_fs.dir_ops.readdir("/testdir", 0)
    assert "file1.txt" in entries     # from overlay
    assert "newfile.txt" in entries   # new file

def test_overlay_file_attributes(memory_fs):
    """Test that overlay file attributes are preserved."""
    node = memory_fs["/test.txt"]
    assert node is not None
    
    # Basic attributes should be present
    attrs = node["attrs"]
    assert "st_mode" in attrs
    assert "st_size" in attrs
    assert "st_mtime" in attrs
    
    # Size should match overlay file
    overlay_size = os.path.getsize(os.path.join(memory_fs.overlay_path, "test.txt"))
    assert int(attrs["st_size"]) == overlay_size
