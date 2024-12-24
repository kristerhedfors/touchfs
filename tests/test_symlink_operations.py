import os
import pytest

def test_symlink_operations(mounted_fs_foreground):
    """Test symlink creation and access."""
    # Create test file
    test_file = os.path.join(mounted_fs_foreground, "target.txt")
    test_content = "Target content\n"
    with open(test_file, "w") as f:
        f.write(test_content)
    
    # Create symlink
    link_path = os.path.join(mounted_fs_foreground, "link.txt")
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
