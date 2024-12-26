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
    log_dir = tmp_path / "llmfs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "llmfs.log"
    log_file.write_text("Initial log content\n")
    return log_file

def test_generate_reads_full_content(file_node):
    """Test that generate returns full log content."""
    log_content = "Log entry 1\nLog entry 2\n"
    
    with patch('pathlib.Path.exists') as mock_exists, \
         patch('builtins.open', mock_open(read_data=log_content)):
        mock_exists.return_value = True
        
        plugin = LogPlugin()
        result = plugin.generate("", file_node, {})
        
        assert result == log_content

def test_generate_handles_missing_file(file_node):
    """Test error handling when log file is missing."""
    with patch('pathlib.Path.exists') as mock_exists:
        mock_exists.return_value = False
        plugin = LogPlugin()
        result = plugin.generate("", file_node, {})
        assert "No logs available - log file not found" in result

def test_generate_handles_empty_file(file_node):
    """Test handling of empty log file."""
    with patch('pathlib.Path.exists') as mock_exists, \
         patch('builtins.open', mock_open(read_data="")):
        mock_exists.return_value = True
        
        plugin = LogPlugin()
        result = plugin.generate("", file_node, {})
        assert "No logs available - log file is empty" in result

def test_read_returns_correct_chunk(file_node):
    """Test that read returns correct chunk of content."""
    log_content = "Line 1\nLine 2\nLine 3\n"
    
    with patch('pathlib.Path.exists') as mock_exists, \
         patch('builtins.open', mock_open(read_data=log_content)):
        mock_exists.return_value = True
        
        plugin = LogPlugin()
        # Read second line only
        chunk = plugin.read("", 6, 7)  # "Line 2" starts at offset 7
        assert chunk == b"Line 2"
