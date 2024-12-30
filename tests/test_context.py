"""Tests for context module and CLI command."""
import os
import tempfile
from pathlib import Path
import pytest
from llmfs.core.context import ContextBuilder, build_context
from llmfs.cli.context_command import main as context_main

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
    
    # Verify ordering
    lines = context.split('\n')
    file_order = [line for line in lines if line.startswith('# File:')]
    
    # Print actual order for debugging
    print("\nActual file order:")
    for line in file_order:
        print(line)
        
    # Get relative paths for easier assertions
    rel_paths = [str(Path(line.replace('# File: ', '').strip()).relative_to(tmp_path)) 
                for line in file_order]
    print("\nRelative paths:")
    for path in rel_paths:
        print(path)
        
    # Check ordering
    assert rel_paths[0] == '__init__.py', f"First file should be __init__.py, got {rel_paths[0]}"
    assert rel_paths[1] == '__main__.py', f"Second file should be __main__.py, got {rel_paths[1]}"
    assert rel_paths[-1] in ('utils.py', 'core/module.py'), f"Last file should be a regular file, got {rel_paths[-1]}"

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
    
    # Check formatting
    assert f"# File: {test_file}" in context
    assert "```" in context
    assert content in context

def test_exclude_patterns(tmp_path):
    """Test file exclusion patterns."""
    # Create test files
    (tmp_path / "include.py").write_text("include")
    (tmp_path / "exclude.pyc").write_text("exclude")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__/cache.py").write_text("cache")
    
    context = build_context(str(tmp_path))
    
    # Check exclusions
    assert "include.py" in context
    assert "exclude.pyc" not in context
    assert "cache.py" not in context

def test_cli_command(tmp_path, capsys):
    """Test CLI command functionality."""
    # Create test file
    test_file = tmp_path / "test.py"
    test_file.write_text("print('test')")
    
    # Run command
    exit_code = context_main(directory=str(tmp_path))
    captured = capsys.readouterr()
    
    # Verify output
    assert exit_code == 0
    assert "# File:" in captured.out
    assert "print('test')" in captured.out

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
