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
def test_file_with_none_content(mounted_fs_foreground):
    """Test file size calculation when content is None."""
    test_file = os.path.join(mounted_fs_foreground, "test.txt")
    
    # Create file with no content (content will be None internally)
    with open(test_file, "w") as f:
        pass
    
    # Verify file exists and has size 0
    assert os.path.exists(test_file)
    stat = os.stat(test_file)
    assert stat.st_size == 0

def test_file_deletion(mounted_fs_foreground):
    """Test file deletion."""
    # Create and then delete a file
    test_file = os.path.join(mounted_fs_foreground, "delete_me.txt")
    with open(test_file, "w") as f:
        f.write("Temporary content\n")
    
    assert os.path.exists(test_file)
    os.unlink(test_file)
    assert not os.path.exists(test_file)

def test_file_creation_nonexistent_directory(mounted_fs_foreground):
    """Test file creation in non-existent directory."""
    test_file = os.path.join(mounted_fs_foreground, "nonexistent", "test.txt")
    
    # Attempt to create file in non-existent directory
    with pytest.raises(FileNotFoundError) as excinfo:
        with open(test_file, "w") as f:
            f.write("This should fail\n")
    
    # Verify error message
    assert "No such file or directory" in str(excinfo.value)
    # Verify file was not created
    assert not os.path.exists(test_file)

def test_file_creation_nested_nonexistent_directory(mounted_fs_foreground):
    """Test file creation in nested non-existent directory."""
    # Create first level directory
    os.makedirs(os.path.join(mounted_fs_foreground, "dir1"))
    
    # Try to create file in non-existent nested directory
    test_file = os.path.join(mounted_fs_foreground, "dir1", "nonexistent", "test.txt")
    
    with pytest.raises(FileNotFoundError) as excinfo:
        with open(test_file, "w") as f:
            f.write("This should fail\n")
    
    # Verify error message
    assert "No such file or directory" in str(excinfo.value)
    # Verify file was not created
    assert not os.path.exists(test_file)

def test_file_creation_in_file(mounted_fs_foreground):
    """Test file creation inside an existing file (should fail)."""
    # Create a file first
    existing_file = os.path.join(mounted_fs_foreground, "existing.txt")
    with open(existing_file, "w") as f:
        f.write("I am a file\n")
    
    # Try to create file inside the existing file
    test_file = os.path.join(existing_file, "test.txt")
    
    with pytest.raises(NotADirectoryError) as excinfo:
        with open(test_file, "w") as f:
            f.write("This should fail\n")
    
    # Verify error message
    assert "Not a directory" in str(excinfo.value)
    # Verify file was not created
    assert not os.path.exists(test_file)
