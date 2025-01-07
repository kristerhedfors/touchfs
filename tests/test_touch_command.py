"""Tests for touch command functionality."""
import os
import subprocess
import pytest
from pathlib import Path
import json
import logging
from unittest.mock import patch, MagicMock
from touchfs.cli.touch_command import generate_filename_suggestions, display_menu

def test_help_output():
    """Test that --help displays usage information."""
    result = subprocess.run(['python', '-m', 'touchfs', 'touch', '--help'],
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
    result = subprocess.run(['python', '-m', 'touchfs', 'touch'],
                          capture_output=True, 
                          text=True)
    assert result.returncode != 0
    assert 'error: the following arguments are required: files' in result.stderr

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing."""
    return tmp_path

def test_touch_without_parents(temp_dir, monkeypatch):
    """Test that touch fails without --parents when parent dir missing."""
    test_file = temp_dir / "nested" / "dir" / "new_file.txt"
    assert not test_file.exists()
    assert not test_file.parent.exists()
    
    result = subprocess.run(['python', '-m', 'touchfs', 'touch', str(test_file)],
                          capture_output=True,
                          text=True)
    
    assert result.returncode == 0  # Still returns 0 like touch
    assert not test_file.exists()  # File should not be created
    assert "Use --parents/-p to create parent directories" in result.stderr

def test_touch_with_parents(temp_dir):
    """Test that touch creates parent directories with --parents."""
    test_file = temp_dir / "nested" / "dir" / "new_file.txt"
    assert not test_file.exists()
    assert not test_file.parent.exists()
    
    result = subprocess.run(['python', '-m', 'touchfs', 'touch', '--parents', str(test_file)],
                          capture_output=True,
                          text=True)
    
    assert result.returncode == 0
    assert test_file.exists()
    assert test_file.parent.exists()
    assert 'Successfully created' in result.stderr

def test_touch_multiple_with_parents(temp_dir):
    """Test marking multiple files with --parents."""
    test_files = [
        temp_dir / "dir1" / "file1.txt",
        temp_dir / "dir2" / "nested" / "file2.txt"
    ]
    
    for file in test_files:
        assert not file.exists()
        assert not file.parent.exists()
    
    result = subprocess.run(['python', '-m', 'touchfs', 'touch', '--parents'] + [str(f) for f in test_files],
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
    
    result = subprocess.run(['python', '-m', 'touchfs', 'touch', str(test_file)],
                          capture_output=True,
                          text=True)
    
    assert result.returncode == 0
    assert test_file.exists()
    assert 'not within a TouchFS filesystem' in result.stderr

def test_force_touch_multiple_with_parents(temp_dir):
    """Test force marking content with multiple files and --parents."""
    test_files = [
        temp_dir / "dir1" / "file1.txt",
        temp_dir / "dir2" / "nested" / "file2.txt"
    ]
    
    result = subprocess.run(['python', '-m', 'touchfs', 'touch', '--force', '--parents'] + [str(f) for f in test_files],
                          capture_output=True,
                          text=True)
    
    assert result.returncode == 0
    for file in test_files:
        assert file.exists()
        assert file.parent.exists()
        assert str(file) in result.stderr

def test_generate_filename_suggestions(temp_dir):
    """Test that filename suggestions are generated correctly."""
    # Create some existing files
    (temp_dir / "README.md").touch()
    (temp_dir / "existing.txt").touch()
    
    # Generate suggestions
    suggestions = generate_filename_suggestions(str(temp_dir))
    
    assert len(suggestions) == 10  # Should always return 10 suggestions
    assert "README.md" not in suggestions  # Should not include existing files
    assert all(isinstance(s, str) for s in suggestions)  # All suggestions should be strings
    assert len(set(suggestions)) == len(suggestions)  # All suggestions should be unique

@patch('touchfs.cli.touch_command.curses.wrapper')
def test_display_menu_single_selection(mock_wrapper, temp_dir):
    """Test menu display with single selection."""
    # Mock user selecting first item
    mock_wrapper.return_value = ([0], False)
    
    suggestions = ["file1.txt", "file2.txt", "file3.txt"]
    selected, regenerate = display_menu(suggestions, allow_multiple=False)
    
    assert selected == [0]
    assert not regenerate
    assert mock_wrapper.called

@patch('touchfs.cli.touch_command.curses.wrapper')
def test_display_menu_multiple_selection(mock_wrapper, temp_dir):
    """Test menu display with multiple selections."""
    # Mock user selecting multiple items
    mock_wrapper.return_value = ([0, 2], False)
    
    suggestions = ["file1.txt", "file2.txt", "file3.txt"]
    selected, regenerate = display_menu(suggestions, allow_multiple=True)
    
    assert selected == [0, 2]
    assert not regenerate
    assert mock_wrapper.called

@patch('touchfs.cli.touch_command.curses.wrapper')
def test_display_menu_cancel(mock_wrapper, temp_dir):
    """Test menu cancellation."""
    # Mock user cancelling
    mock_wrapper.return_value = (None, False)
    
    suggestions = ["file1.txt", "file2.txt", "file3.txt"]
    selected, regenerate = display_menu(suggestions)
    
    assert selected is None
    assert not regenerate
    assert mock_wrapper.called

@patch('touchfs.cli.touch_command.curses.wrapper')
def test_display_menu_regenerate(mock_wrapper, temp_dir):
    """Test menu regeneration."""
    # Mock user selecting items and pressing 'r'
    mock_wrapper.return_value = ([0, 1], True)
    
    suggestions = ["file1.txt", "file2.txt", "file3.txt"]
    selected, regenerate = display_menu(suggestions, allow_multiple=True)
    
    assert selected == [0, 1]
    assert regenerate
    assert mock_wrapper.called

def test_directory_only_argument(temp_dir):
    """Test handling of directory-only argument."""
    expected_file = "README.md"
    
    # Mock both the menu and suggestions
    with patch('touchfs.cli.touch_command.display_menu') as mock_menu, \
         patch('touchfs.cli.touch_command.generate_filename_suggestions') as mock_suggestions:
        # Setup mocks
        mock_suggestions.return_value = [expected_file, "other.txt"]
        mock_menu.return_value = ([0], False)  # Simulate selecting first suggestion, no regenerate
        
        # Call touch_main directly instead of using subprocess
        from touchfs.cli.touch_command import touch_main
        result = touch_main(
            files=[str(temp_dir)],
            force=True,  # Skip confirmation
            parents=True,  # Allow creating parent dirs if needed
            debug_stdout=True,
            max_tokens=None
        )
        
        # Verify mocks were called correctly
        mock_suggestions.assert_called_once()
        mock_menu.assert_called_once()
        
        assert result == 0
        # Verify the specific file was created
        expected_path = temp_dir / expected_file
        assert expected_path.is_file(), f"File not created at {expected_path}"

def test_debug_logging(temp_dir):
    """Test debug logging."""
    test_file = temp_dir / "nested" / "test.txt"
    
    result = subprocess.run(['python', '-m', 'touchfs', 'touch', '--debug-stdout', '--force', '--parents', str(test_file)],
                          capture_output=True,
                          text=True)
    
    assert 'TouchFS Touch Command Started' in result.stdout
