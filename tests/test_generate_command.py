"""Tests for generate command functionality."""
import os
import subprocess
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from pydantic import BaseModel

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
    assert 'Generate content for files' in result.stdout

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

def test_generate_without_parents(temp_dir):
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

class MockResponse:
    """Mock OpenAI API response."""
    class Message:
        class ParsedContent:
            def __init__(self, content):
                self.content = content
        def __init__(self, content):
            self.parsed = self.ParsedContent(content)
    class Choice:
        def __init__(self, content):
            self.message = MockResponse.Message(content)
    def __init__(self, content):
        self.choices = [self.Choice(content)]

@pytest.fixture
def mock_openai():
    """Mock OpenAI client for testing."""
    with patch('touchfs.content.plugins.default.get_openai_client') as mock:
        client = MagicMock()
        client.beta.chat.completions.parse.return_value = MockResponse("Test generated content")
        mock.return_value = client
        yield mock

def test_generate_with_parents(temp_dir, mock_openai):
    """Test that generate creates parent directories and generates content with --parents."""
    test_file = temp_dir / "nested" / "dir" / "new_file.txt"
    assert not test_file.exists()
    assert not test_file.parent.exists()
    
    # Get the mocked client
    client = mock_openai.return_value
    
    # Call generate_main directly instead of using subprocess
    from touchfs.cli.generate_command import generate_main
    result = generate_main(
        files=[str(test_file)],
        parents=True,
        force=True,
        debug_stdout=True,
        openai_client=client
    )
    
    assert result == 0
    assert test_file.exists()
    assert test_file.parent.exists()
    
    # Verify content was written
    content = test_file.read_text()
    assert content == "Test generated content"

def test_generate_multiple_with_parents(temp_dir, mock_openai):
    """Test generating content for multiple files with --parents."""
    test_files = [
        temp_dir / "dir1" / "file1.txt",
        temp_dir / "dir2" / "nested" / "file2.txt"
    ]
    
    for file in test_files:
        assert not file.exists()
        assert not file.parent.exists()
    
    # Get the mocked client
    client = mock_openai.return_value
    
    # Call generate_main directly
    from touchfs.cli.generate_command import generate_main
    result = generate_main(
        files=[str(f) for f in test_files],
        parents=True,
        force=True,
        debug_stdout=True,
        openai_client=client
    )
    
    assert result == 0
    for file in test_files:
        assert file.exists()
        assert file.parent.exists()
        
        # Verify content was written
        content = file.read_text()
        assert content == "Test generated content"

def test_generate_with_context(temp_dir, mock_openai):
    """Test content generation uses context from surrounding files."""
    # Create a context file
    context_file = temp_dir / "context.txt"
    context_file.write_text("Context information")
    
    # Create test file
    test_file = temp_dir / "test.txt"
    
    # Get the mocked client
    client = mock_openai.return_value
    
    # Call generate_main directly
    from touchfs.cli.generate_command import generate_main
    result = generate_main(
        files=[str(test_file)],
        force=True,
        debug_stdout=True,
        openai_client=client
    )
    
    assert result == 0
    assert test_file.exists()
    
    # Verify content was written
    content = test_file.read_text()
    assert content == "Test generated content"
    
    # Verify context was used in API call
    mock_client = mock_openai.return_value
    call_args = mock_client.beta.chat.completions.parse.call_args
    messages = call_args[1]['messages']
    assert any('context.txt' in str(msg).lower() for msg in messages)

def test_generate_handles_api_error(temp_dir, mock_openai):
    """Test handling of API errors during generation."""
    test_file = temp_dir / "test.txt"
    
    # Make API call raise an error
    mock_client = mock_openai.return_value
    mock_client.beta.chat.completions.parse.side_effect = Exception("API Error")
    
    result = subprocess.run(['python', '-m', 'touchfs', 'generate', '--force', str(test_file)],
                          capture_output=True,
                          text=True,
                          env={**os.environ, 'OPENAI_API_KEY': 'test-key'})
    
    assert result.returncode == 0  # Still returns 0 like touch
    assert test_file.exists()  # File is created but empty
    assert 'Error generating content' in result.stderr
    
    # Verify file is empty
    content = test_file.read_text()
    assert content == ""

def test_debug_logging(temp_dir, mock_openai):
    """Test debug logging."""
    test_file = temp_dir / "test.txt"
    
    # Get the mocked client
    client = mock_openai.return_value
    
    # Call generate_main directly
    from touchfs.cli.generate_command import generate_main
    result = generate_main(
        files=[str(test_file)],
        force=True,
        debug_stdout=True,
        openai_client=client
    )
    
    assert result == 0
    assert test_file.exists()
    content = test_file.read_text()
    assert content == "Test generated content"
