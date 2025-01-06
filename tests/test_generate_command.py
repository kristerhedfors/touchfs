"""Tests for generate command functionality."""
import os
import subprocess
import pytest
from pathlib import Path
import json
import logging

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

def test_generate_without_parents(temp_dir, monkeypatch):
    """Test that generate fails without --parents when parent dir missing."""
    test_file = temp_dir / "nested" / "dir" / "new_file.txt"
    assert not test_file.exists()
    assert not test_file.parent.exists()
    
    result = subprocess.run(['python', '-m', 'touchfs', 'generate', str(test_file)],
                          capture_output=True,
                          text=True)
    
    assert result.returncode == 0  # Still returns 0 like touch
    assert not test_file.exists()  # File should not be created
    assert "Use --parents/-p to create parent directories" in result.stderr

def test_generate_with_parents(temp_dir):
    """Test that generate creates parent directories with --parents."""
    test_file = temp_dir / "nested" / "dir" / "new_file.txt"
    assert not test_file.exists()
    assert not test_file.parent.exists()
    
    result = subprocess.run(['python', '-m', 'touchfs', 'generate', '--parents', str(test_file)],
                          capture_output=True,
                          text=True)
    
    assert result.returncode == 0
    assert test_file.exists()
    assert test_file.parent.exists()
    assert 'Successfully created' in result.stderr

def test_generate_multiple_with_parents(temp_dir):
    """Test generating multiple files with --parents."""
    test_files = [
        temp_dir / "dir1" / "file1.txt",
        temp_dir / "dir2" / "nested" / "file2.txt"
    ]
    
    for file in test_files:
        assert not file.exists()
        assert not file.parent.exists()
    
    result = subprocess.run(['python', '-m', 'touchfs', 'generate', '--parents'] + [str(f) for f in test_files],
                          capture_output=True,
                          text=True)
    
    assert result.returncode == 0
    for file in test_files:
        assert file.exists()
        assert file.parent.exists()
        assert str(file) in result.stderr

def test_non_touchfs_path(temp_dir):
    """Test that non-touchfs paths are created with warning."""
    test_file = temp_dir / "test.txt"
    
    result = subprocess.run(['python', '-m', 'touchfs', 'generate', str(test_file)],
                          capture_output=True,
                          text=True)
    
    assert result.returncode == 0
    assert test_file.exists()
    assert 'not within a TouchFS filesystem' in result.stderr

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

def test_debug_logging(temp_dir):
    """Test debug logging."""
    test_file = temp_dir / "nested" / "test.txt"
    
    result = subprocess.run(['python', '-m', 'touchfs', 'generate', '--debug-stdout', '--force', '--parents', str(test_file)],
                          capture_output=True,
                          text=True)
    
    assert 'TouchFS Generate Command Started' in result.stdout
