import os
import pytest

def test_fs_json_exists_foreground(mounted_fs_foreground):
    """Test that fs.json is created and readable."""
    fs_json_path = os.path.join(mounted_fs_foreground, "fs.json")
    assert os.path.exists(fs_json_path)
    assert os.path.isfile(fs_json_path)
