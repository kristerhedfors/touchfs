import os
import time
import pytest
import subprocess
import tempfile
from pathlib import Path

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
        ["llmfs", mount_point],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for filesystem to be mounted
    time.sleep(2)
    
    try:
        yield mount_point
    finally:
        # Cleanup: Unmount filesystem and terminate process
        subprocess.run(["fusermount", "-u", mount_point])
        process.terminate()
        process.wait()

def test_fs_json_exists(mounted_fs):
    """Test that fs.json is created and readable."""
    fs_json_path = os.path.join(mounted_fs, "fs.json")
    assert os.path.exists(fs_json_path)
    assert os.path.isfile(fs_json_path)

def test_directory_operations(mounted_fs):
    """Test directory creation and listing."""
    # Create test directory
    test_dir = os.path.join(mounted_fs, "testdir")
    os.mkdir(test_dir)
    
    # Verify directory exists
    assert os.path.exists(test_dir)
    assert os.path.isdir(test_dir)
    
    # Check directory permissions
    stat = os.stat(test_dir)
    assert stat.st_mode & 0o777 == 0o755
    
    # Check directory listing
    contents = os.listdir(mounted_fs)
    assert "testdir" in contents
    assert "fs.json" in contents

def test_file_operations(mounted_fs):
    """Test file creation, writing, reading, and attributes."""
    # Create test directory and file
    test_dir = os.path.join(mounted_fs, "testdir")
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

def test_file_modification(mounted_fs):
    """Test file content modification."""
    test_file = os.path.join(mounted_fs, "test.txt")
    
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

def test_symlink_operations(mounted_fs):
    """Test symlink creation and access."""
    # Create test file
    test_file = os.path.join(mounted_fs, "target.txt")
    test_content = "Target content\n"
    with open(test_file, "w") as f:
        f.write(test_content)
    
    # Create symlink
    link_path = os.path.join(mounted_fs, "link.txt")
    os.symlink("target.txt", link_path)
    
    # Verify symlink properties
    assert os.path.islink(link_path)
    assert os.readlink(link_path) == "target.txt"
    
    # Read through symlink
    with open(link_path, "r") as f:
        content = f.read()
    assert content == test_content
    
    # Modify through symlink
    new_content = "Modified through link\n"
    with open(link_path, "w") as f:
        f.write(new_content)
    
    # Verify modification in original file
    with open(test_file, "r") as f:
        content = f.read()
    assert content == new_content

def test_file_deletion(mounted_fs):
    """Test file deletion."""
    # Create and then delete a file
    test_file = os.path.join(mounted_fs, "delete_me.txt")
    with open(test_file, "w") as f:
        f.write("Temporary content\n")
    
    assert os.path.exists(test_file)
    os.unlink(test_file)
    assert not os.path.exists(test_file)

def test_directory_deletion(mounted_fs):
    """Test directory deletion."""
    # Create and then delete an empty directory
    test_dir = os.path.join(mounted_fs, "empty_dir")
    os.mkdir(test_dir)
    
    assert os.path.exists(test_dir)
    os.rmdir(test_dir)
    assert not os.path.exists(test_dir)

def test_nested_directory_structure(mounted_fs):
    """Test creating and navigating nested directory structure."""
    # Create nested structure
    path = Path(mounted_fs)
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
    assert "dir1" in os.listdir(mounted_fs)
    assert "dir2" in os.listdir(path / "dir1")
    assert "dir3" in os.listdir(path / "dir1" / "dir2")
    assert "test.txt" in os.listdir(nested_dir)
