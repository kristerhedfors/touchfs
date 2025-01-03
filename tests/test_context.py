"""Tests for context module and CLI command."""
import os
import json
import tempfile
from pathlib import Path
import pytest
from touchfs.core.context import ContextBuilder, build_context
from touchfs.cli.context_command import main as context_main

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
    assert any('Total Files: 1' in line for line in lines)
    assert any('Token Count:' in line for line in lines)
    assert any('Token Limit:' in line for line in lines)
    
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

def test_cli_command(tmp_path, capsys):
    """Test CLI command functionality."""
    # Create test file
    test_file = tmp_path / "test.py"
    test_file.write_text("print('test')")
    
    # Run command
    exit_code = context_main(directory=str(tmp_path))
    captured = capsys.readouterr()
    
    # Verify output format
    lines = captured.out.split('\n')
    assert exit_code == 0
    assert '# Context Information' in lines
    assert any('Total Files: 1' in line for line in lines)
    assert f'# File: {test_file.name}' in lines
    assert 'Type: py' in lines
    
    # Check content between backticks
    content_start = lines.index('```') + 1
    content_end = lines[content_start:].index('```') + content_start
    actual_content = lines[content_start:content_end][0]
    assert actual_content == "print('test')"

def test_cli_invalid_directory(capsys):
    """Test CLI command with invalid directory."""
    exit_code = context_main(directory="/nonexistent/path")
    captured = capsys.readouterr()
    
    assert exit_code == 1
    assert "Error: Directory" in captured.err

def test_cli_max_tokens(tmp_path, capsys):
    """Test CLI command with max tokens argument."""
    # Create file with known content
    test_file = tmp_path / "test.py"
    test_file.write_text("word " * 1000)
    
    # Run with low token limit
    exit_code = context_main(directory=str(tmp_path), max_tokens=50)
    captured = capsys.readouterr()
    
    # Verify output respects token limit
    builder = ContextBuilder()
    assert builder.count_tokens(captured.out) <= 50
