import os
import pytest
from pathlib import Path

def test_directory_operations(mounted_fs_foreground):
    """Test directory creation and listing."""
    # Create test directory
    test_dir = os.path.join(mounted_fs_foreground, "testdir")
    os.mkdir(test_dir)
    
    # Verify directory exists
    assert os.path.exists(test_dir)
    assert os.path.isdir(test_dir)
    
    # Check directory permissions
    stat = os.stat(test_dir)
    assert stat.st_mode & 0o777 == 0o755
    
    # Check directory listing
    contents = os.listdir(mounted_fs_foreground)
    assert "testdir" in contents
    assert "fs.json" in contents
def test_directory_deletion(mounted_fs_foreground):
    """Test directory deletion."""
    # Create and then delete an empty directory
    test_dir = os.path.join(mounted_fs_foreground, "empty_dir")
    os.mkdir(test_dir)
    
    assert os.path.exists(test_dir)
    os.rmdir(test_dir)
    assert not os.path.exists(test_dir)
def test_nested_directory_structure(mounted_fs_foreground):
    """Test creating and navigating nested directory structure."""
    # Create nested structure
    path = Path(mounted_fs_foreground)
    nested_dir = path / "dir1" / "dir2" / "dir3"
    nested_dir.mkdir(parents=True)
    
    # Create a file in the nested directory
    test_file = nested_dir / "test.txt"
    test_content = "Nested file content\n"
    test_file.write_text(test_content)
    
    # Verify structure
    assert nested_dir.exists()
    assert test_file.exists()
    assert test_file.read_text() == test_content
    
    # Test directory listing at each level
    assert "dir1" in os.listdir(mounted_fs_foreground)
    assert "dir2" in os.listdir(path / "dir1")
    assert "dir3" in os.listdir(path / "dir1" / "dir2")
    assert "test.txt" in os.listdir(nested_dir)
