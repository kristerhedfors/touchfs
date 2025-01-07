"""Tests for context module and CLI command."""
import os
import json
import tempfile
import subprocess
from pathlib import Path
import pytest
from touchfs.core.context import ContextBuilder, build_context

def test_token_counting():
    """Test token counting functionality."""
    builder = ContextBuilder(max_tokens=100)
    
    # Basic token count test
    text = "Hello world"  # Should be 2 tokens
    assert builder.count_tokens(text) == 2
    
    # Test token limit check
    assert not builder.would_exceed_token_limit(text)
    builder.current_tokens = 99
    assert builder.would_exceed_token_limit(text)

def test_file_ordering(tmp_path):
    """Test file ordering with __init__ and __main__ files."""
    # Create test files
    files = {
        '__init__.py': 'init content',
        '__main__.py': 'main content',
        'utils.py': 'utils content',
        'core/__init__.py': 'core init',
        'core/module.py': 'module content'
    }
    
    for path, content in files.items():
        file_path = tmp_path / path
        file_path.parent.mkdir(exist_ok=True)
        file_path.write_text(content)
    
    # Generate context
    context = build_context(str(tmp_path), max_tokens=1000)
    
    # Split context into lines for analysis
    lines = context.split('\n')
    
    # Find file entries and their order
    file_entries = []
    for i, line in enumerate(lines):
        if line.startswith('# File: '):
            file_entries.append(line[8:])  # Remove "# File: " prefix
    
    # Print actual order for debugging
    print("\nActual file order:")
    for path in file_entries:
        print(path)
        
    # Check ordering
    assert file_entries[0] == '__init__.py', f"First file should be __init__.py, got {file_entries[0]}"
    assert file_entries[1] == '__main__.py', f"Second file should be __main__.py, got {file_entries[1]}"
    assert file_entries[-1] in ('utils.py', 'core/module.py'), f"Last file should be a regular file, got {file_entries[-1]}"

def test_token_limit_respect(tmp_path):
    """Test that token limits are respected."""
    # Create a file with known token count
    test_file = tmp_path / "test.py"
    test_file.write_text("word " * 1000)  # Each "word " is about 1 token
    
    # Generate context with low token limit
    context = build_context(str(tmp_path), max_tokens=50)
    
    # Count tokens in result
    builder = ContextBuilder()
    assert builder.count_tokens(context) <= 50

def test_context_formatting(tmp_path):
    """Test context output formatting."""
    test_file = tmp_path / "test.py"
    content = "def hello():\n    print('world')"
    test_file.write_text(content)
    
    context = build_context(str(tmp_path))
    lines = context.split('\n')
    
    # Check header information
    assert '# Context Information' in lines
    
    # Check file content formatting
    assert f'# File: {test_file.name}' in lines
    assert 'Type: py' in lines
    
    # Find content between triple backticks
    content_start = lines.index('```') + 1
    content_end = lines[content_start:].index('```') + content_start
    actual_content = '\n'.join(lines[content_start:content_end])
    
    assert actual_content == content

def test_exclude_patterns(tmp_path):
    """Test file exclusion patterns."""
    # Create test files
    (tmp_path / "include.py").write_text("include")
    (tmp_path / "exclude.pyc").write_text("exclude")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__/cache.py").write_text("cache")
    
    context = build_context(str(tmp_path))
    lines = context.split('\n')
    
    # Get file entries
    file_entries = [line[8:] for line in lines if line.startswith('# File: ')]
    
    # Check exclusions
    assert any("include.py" in entry for entry in file_entries)
    assert not any("exclude.pyc" in entry for entry in file_entries)
    assert not any("cache.py" in entry for entry in file_entries)

def test_cli_command(tmp_path):
    """Test CLI command functionality."""
    # Create test file
    test_file = tmp_path / "test.py"
    test_file.write_text("print('test')")
    
    # Run command
    result = subprocess.run(['python', '-m', 'touchfs', 'context', str(tmp_path)],
                          capture_output=True,
                          text=True)
    
    # Verify output format
    lines = result.stdout.split('\n')
    assert result.returncode == 0
    assert '# Context Information' in lines
    assert f'# File: {test_file.name}' in lines
    assert 'Type: py' in lines
    
    # Check content between backticks
    content_start = lines.index('```') + 1
    content_end = lines[content_start:].index('```') + content_start
    actual_content = lines[content_start:content_end][0]
    assert actual_content == "print('test')"

def test_cli_invalid_directory():
    """Test CLI command with invalid directory."""
    result = subprocess.run(['python', '-m', 'touchfs', 'context', '/nonexistent/path'],
                          capture_output=True,
                          text=True)
    
    assert result.returncode == 1
    assert "Error: Directory" in result.stderr

def test_cli_max_tokens(tmp_path):
    """Test CLI command with max tokens argument."""
    # Create file with known content
    test_file = tmp_path / "test.py"
    test_file.write_text("word " * 1000)
    
    # Run with low token limit
    result = subprocess.run(['python', '-m', 'touchfs', 'context', str(tmp_path), '--max-tokens', '50'],
                          capture_output=True,
                          text=True)
    
    # Verify output respects token limit
    builder = ContextBuilder()
    assert builder.count_tokens(result.stdout) <= 50

def test_binary_file_handling(tmp_path):
    """Test that binary files are ignored during context building."""
    # Create a binary file
    test_file = tmp_path / "test.bin"
    test_file.write_bytes(bytes([0x89, 0x50, 0x4E, 0x47]))  # PNG magic number
    
    # Create a text file to verify context still works
    text_file = tmp_path / "test.txt"
    text_file.write_text("test content")
    
    # Generate context
    context = build_context(str(tmp_path))
    lines = context.split('\n')
    
    # Verify binary file is not included
    assert not any('test.bin' in line for line in lines)
    
    # Verify text file is included
    assert any('test.txt' in line for line in lines)

def test_include_patterns(tmp_path):
    """Test include patterns functionality."""
    # Create test files with different extensions
    (tmp_path / "test.py").write_text("python content")
    (tmp_path / "test.js").write_text("javascript content")
    (tmp_path / "test.txt").write_text("text content")
    
    # Generate context with include patterns
    context = build_context(
        str(tmp_path),
        include_patterns=["*.py", "*.js"]  # Only include .py and .js files
    )
    lines = context.split('\n')
    
    # Get file entries
    file_entries = [line[8:] for line in lines if line.startswith('# File: ')]
    
    # Verify only specified patterns are included
    assert any("test.py" in entry for entry in file_entries), "Python file should be included"
    assert any("test.js" in entry for entry in file_entries), "JavaScript file should be included"
    assert not any("test.txt" in entry for entry in file_entries), "Text file should not be included"
