"""Tests for the log plugin."""
import os
from pathlib import Path
import pytest
from unittest.mock import mock_open, patch, MagicMock

from llmfs.content.plugins.log import LogPlugin
from llmfs.models.filesystem import FileNode, FileAttrs

@pytest.fixture
def log_plugin():
    return LogPlugin()

@pytest.fixture
def file_node():
    return FileNode(
        type="file",
        attrs=FileAttrs(st_mode="0644")
    )

@pytest.fixture
def mock_log_file(tmp_path):
    log_file = tmp_path / "llmfs.log"
    log_file.write_text("Initial log content\n")
    return log_file

def test_initial_offset_capture(log_plugin):
    """Test that the plugin captures initial log file size."""
    with patch('pathlib.Path.exists') as mock_exists, \
         patch('os.path.getsize') as mock_getsize:
        mock_exists.return_value = True
        mock_getsize.return_value = 100
        
        offset = log_plugin._get_initial_offset()
        assert offset == 100
        mock_exists.assert_called_once()
        mock_getsize.assert_called_once()

def test_initial_offset_no_file(log_plugin):
    """Test offset handling when log file doesn't exist."""
    with patch('pathlib.Path.exists') as mock_exists:
        mock_exists.return_value = False
        offset = log_plugin._get_initial_offset()
        assert offset == 0

def test_generate_reads_from_offset(file_node):
    """Test that generate only returns content after the offset."""
    initial_content = "Old logs\n"
    new_content = "New logs\n"
    
    # Create a custom mock file object that simulates seek behavior
    class MockFile:
        def __init__(self):
            self.content = initial_content + new_content
            self.position = 0
            
        def seek(self, position):
            self.position = position
            
        def read(self):
            return self.content[self.position:]
            
        def __enter__(self):
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
            
    mock_file = MockFile()
    
    with patch('pathlib.Path.exists') as mock_exists, \
         patch('os.path.getsize') as mock_getsize, \
         patch('builtins.open', return_value=mock_file):
        mock_exists.return_value = True
        mock_getsize.return_value = len(initial_content)
        
        plugin = LogPlugin()
        result = plugin.generate("", file_node, {})
        
        assert result == new_content
        assert mock_file.position == len(initial_content)

def test_generate_handles_missing_file(file_node):
    """Test error handling when log file is missing."""
    with patch('pathlib.Path.exists') as mock_exists:
        mock_exists.return_value = False
        plugin = LogPlugin()
        result = plugin.generate("", file_node, {})
        assert "No logs available" in result

def test_generate_handles_read_error(file_node):
    """Test error handling when reading log file fails."""
    with patch('pathlib.Path.exists') as mock_exists, \
         patch('builtins.open') as mock_open:
        mock_exists.return_value = True
        mock_open.side_effect = IOError("Read error")
        
        plugin = LogPlugin()
        result = plugin.generate("", file_node, {})
        assert "Error reading logs" in result
