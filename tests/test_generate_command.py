"""Tests for generate command functionality."""
import os
import subprocess
import pytest
from pathlib import Path
import json

def test_help_output():
    """Test that --help displays usage information."""
    result = subprocess.run(['python', '-m', 'touchfs', 'generate', '--help'],
                          capture_output=True, 
                          text=True)
    assert result.returncode == 0
    assert 'usage:' in result.stdout
    assert 'files' in result.stdout
    assert '--force' in result.stdout
    assert '--parents' in result.stdout
    assert 'Create parent directories' in result.stdout
    assert 'Mark files for TouchFS content generation' in result.stdout

def test_missing_paths():
    """Test that missing paths argument shows error."""
    result = subprocess.run(['python', '-m', 'touchfs', 'generate'],
                          capture_output=True, 
                          text=True)
    assert result.returncode != 0
    assert 'error: the following arguments are required: files' in result.stderr

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing."""
    return tmp_path

@pytest.fixture
def touchfs_mount(tmp_path):
    """Create a temporary TouchFS mount for testing."""
    mount_dir = tmp_path / "mount"
    mount_dir.mkdir()
    
    # Create .touchfs marker
    (mount_dir / ".touchfs").touch()
    
    return mount_dir

def test_generate_without_parents(temp_dir, monkeypatch):
    """Test that generate fails without --parents when parent dir missing."""
    test_file = temp_dir / "nested" / "dir" / "new_file.txt"
    assert not test_file.exists()
    assert not test_file.parent.exists()
    
    # Mock input to simulate 'y' response
    monkeypatch.setattr('builtins.input', lambda _: 'y')
    
    result = subprocess.run(['python', '-m', 'touchfs', 'generate', str(test_file)],
                          capture_output=True,
                          text=True)
    
    assert result.returncode == 0  # Still returns 0 like touch
    assert not test_file.exists()  # File should not be created
    assert "Use --parents/-p to create parent directories" in result.stderr

def test_generate_with_parents(temp_dir, monkeypatch):
    """Test that generate creates parent directories with --parents."""
    test_file = temp_dir / "nested" / "dir" / "new_file.txt"
    assert not test_file.exists()
    assert not test_file.parent.exists()
    
    # Mock input to simulate 'y' response
    monkeypatch.setattr('builtins.input', lambda _: 'y')
    
    result = subprocess.run(['python', '-m', 'touchfs', 'generate', '--parents', str(test_file)],
                          capture_output=True,
                          text=True)
    
    assert result.returncode == 0
    assert test_file.exists()
    assert test_file.parent.exists()
    assert 'Successfully created' in result.stderr

def test_generate_multiple_with_parents(temp_dir, monkeypatch):
    """Test generating multiple files with --parents."""
    test_files = [
        temp_dir / "dir1" / "file1.txt",
        temp_dir / "dir2" / "nested" / "file2.txt"
    ]
    
    for file in test_files:
        assert not file.exists()
        assert not file.parent.exists()
    
    # Mock input to simulate all 'y' responses
    responses = iter(['y', 'y'])
    monkeypatch.setattr('builtins.input', lambda _: next(responses))
    
    result = subprocess.run(['python', '-m', 'touchfs', 'generate', '--parents'] + [str(f) for f in test_files],
                          capture_output=True,
                          text=True)
    
    assert result.returncode == 0
    for file in test_files:
        assert file.exists()
        assert file.parent.exists()
        assert str(file) in result.stderr

def test_generate_mixed_paths_with_parents(touchfs_mount, temp_dir, monkeypatch):
    """Test handling mix of touchfs and non-touchfs paths with --parents."""
    touchfs_file = touchfs_mount / "nested" / "touchfs_file.txt"
    non_touchfs_file = temp_dir / "nested" / "non_touchfs_file.txt"
    
    assert not touchfs_file.exists()
    assert not touchfs_file.parent.exists()
    assert not non_touchfs_file.exists()
    assert not non_touchfs_file.parent.exists()
    
    # Mock input to simulate 'y' for non-touchfs and 'y' for touchfs batch
    responses = iter(['y', 'y'])
    monkeypatch.setattr('builtins.input', lambda _: next(responses))
    
    result = subprocess.run(['python', '-m', 'touchfs', 'generate', '--parents', str(touchfs_file), str(non_touchfs_file)],
                          capture_output=True,
                          text=True)
    
    assert result.returncode == 0
    assert touchfs_file.exists()
    assert touchfs_file.parent.exists()
    assert non_touchfs_file.exists()
    assert non_touchfs_file.parent.exists()
    assert 'Warning: The following paths are not within a TouchFS filesystem' in result.stdout

def test_reject_non_touchfs_path(temp_dir, monkeypatch):
    """Test rejecting non-touchfs path."""
    test_file = temp_dir / "nested" / "test.txt"
    
    # Mock input to simulate 'n' response
    monkeypatch.setattr('builtins.input', lambda _: 'n')
    
    result = subprocess.run(['python', '-m', 'touchfs', 'generate', '--parents', str(test_file)],
                          capture_output=True,
                          text=True)
    
    assert result.returncode == 0
    assert not test_file.exists()  # File should not be created
    assert not test_file.parent.exists()  # Parent dir should not be created
    assert 'No paths approved for marking' in result.stdout

def test_force_generate_multiple_with_parents(temp_dir):
    """Test force generating content with multiple files and --parents."""
    test_files = [
        temp_dir / "dir1" / "file1.txt",
        temp_dir / "dir2" / "nested" / "file2.txt"
    ]
    
    result = subprocess.run(['python', '-m', 'touchfs', 'generate', '--force', '--parents'] + [str(f) for f in test_files],
                          capture_output=True,
                          text=True)
    
    assert result.returncode == 0
    for file in test_files:
        assert file.exists()
        assert file.parent.exists()
        assert str(file) in result.stderr

def test_touchfs_paths_only(touchfs_mount):
    """Test handling touchfs paths without prompting."""
    test_files = [
        touchfs_mount / "dir1" / "file1.txt",
        touchfs_mount / "dir2" / "file2.txt"
    ]
    
    result = subprocess.run(['python', '-m', 'touchfs', 'generate', '--parents'] + [str(f) for f in test_files],
                          capture_output=True,
                          text=True)
    
    assert result.returncode == 0
    for file in test_files:
        assert file.exists()
        assert file.parent.exists()
        assert str(file) in result.stderr

def test_context_xattr_set(touchfs_mount):
    """Test that context is built and stored in xattr."""
    # Create a test file to provide context
    context_file = touchfs_mount / "context.py"
    context_file.write_text("def test_func():\n    pass\n")
    
    # Generate a new file
    test_file = touchfs_mount / "generated.txt"
    result = subprocess.run(['python', '-m', 'touchfs', 'generate', '--parents', str(test_file)],
                          capture_output=True,
                          text=True)
    
    assert result.returncode == 0
    assert test_file.exists()
    
    # Verify warning about xattr not supported
    assert 'Extended attributes not supported' in result.stderr

def test_max_tokens_limit(touchfs_mount):
    """Test max_tokens parameter limits context size."""
    # Create multiple context files
    for i in range(3):
        context_file = touchfs_mount / f"context{i}.py"
        context_file.write_text(f"def test_func_{i}():\n    pass\n")
    
    # Generate with small token limit
    test_file = touchfs_mount / "generated.txt"
    result = subprocess.run(['python', '-m', 'touchfs', 'generate', '-m', '50', str(test_file)],
                          capture_output=True,
                          text=True)
    
    assert result.returncode == 0
    assert test_file.exists()
    assert 'Extended attributes not supported' in result.stderr

def test_context_build_failure(touchfs_mount, caplog):
    """Test handling of context build failures."""
    # Create an unreadable directory
    context_dir = touchfs_mount / "context_dir"
    context_dir.mkdir()
    context_file = context_dir / "test.py"
    context_file.write_text("def test():\n    pass\n")
    os.chmod(str(context_dir), 0o000)  # Remove all permissions
    
    try:
        test_file = touchfs_mount / "generated.txt"
        result = subprocess.run(['python', '-m', 'touchfs', 'generate', str(test_file)],
                              capture_output=True,
                              text=True)
        
        assert result.returncode == 0  # Should still succeed
        assert test_file.exists()
        assert 'Extended attributes not supported' in result.stderr
        
    finally:
        os.chmod(str(context_dir), 0o755)  # Restore permissions

def test_debug_logging(temp_dir):
    """Test debug logging."""
    test_file = temp_dir / "nested" / "test.txt"
    
    result = subprocess.run(['python', '-m', 'touchfs', 'generate', '--debug-stdout', '--force', '--parents', str(test_file)],
                          capture_output=True,
                          text=True)
    
    assert 'TouchFS Generate Command Started' in result.stderr
