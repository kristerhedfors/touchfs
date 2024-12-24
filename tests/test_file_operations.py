import os
import pytest

def test_file_operations(mounted_fs_foreground):
    """Test file creation, writing, reading, and attributes."""
    # Create test directory and file
    test_dir = os.path.join(mounted_fs_foreground, "testdir")
    os.mkdir(test_dir)
    test_file = os.path.join(test_dir, "test.txt")
    
    # Write content
    test_content = "Hello, World!\n"
    with open(test_file, "w") as f:
        f.write(test_content)
    
    # Verify content
    with open(test_file, "r") as f:
        content = f.read()
    assert content == test_content
    
    # Check file attributes
    stat = os.stat(test_file)
    assert stat.st_mode & 0o777 == 0o644
    assert stat.st_size == len(test_content)
def test_file_modification(mounted_fs_foreground):
    """Test file content modification."""
    test_file = os.path.join(mounted_fs_foreground, "test.txt")
    
    # Initial content
    initial_content = "Initial content\n"
    with open(test_file, "w") as f:
        f.write(initial_content)
    
    # Modified content
    modified_content = "Modified content\n"
    with open(test_file, "w") as f:
        f.write(modified_content)
    
    # Verify modification
    with open(test_file, "r") as f:
        content = f.read()
    assert content == modified_content
    
    # Check updated file size
    stat = os.stat(test_file)
    assert stat.st_size == len(modified_content)
def test_file_deletion(mounted_fs_foreground):
    """Test file deletion."""
    # Create and then delete a file
    test_file = os.path.join(mounted_fs_foreground, "delete_me.txt")
    with open(test_file, "w") as f:
        f.write("Temporary content\n")
    
    assert os.path.exists(test_file)
    os.unlink(test_file)
    assert not os.path.exists(test_file)
