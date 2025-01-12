"""Tests for generate command functionality."""
import os
import json
import subprocess
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from pydantic import BaseModel
from touchfs.models.filesystem import GeneratedContent, ContentMetadata
from touchfs.models.filesystem_list import FilesystemList
from touchfs.content.filesystem_generator import FilesystemResponse

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
    assert '--no-content' in result.stdout
    assert 'Create parent directories' in result.stdout
    assert 'Generate content for files' in result.stdout
    assert 'Create empty files without generating content' in result.stdout

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
    
    result = subprocess.run(['python', '-m', 'touchfs', 'generate', '--force', str(test_file)],
                          capture_output=True,
                          text=True)
    
    assert result.returncode != 0  # Should fail when parent directory missing
    assert not test_file.exists()  # File should not be created
    assert "Use --parents/-p to create parent directories" in result.stderr

class MockContentResponse:
    """Mock OpenAI API response for content generation."""
    class Message:
        def __init__(self, content):
            self.content = content
            self.parsed = GeneratedContent(
                content="Test generated content",
                metadata=ContentMetadata(file_type="text")
            )
    class Choice:
        def __init__(self, content):
            self.message = MockContentResponse.Message(content)
    def __init__(self, content):
        self.choices = [self.Choice(content)]

class MockFilesystemResponse:
    """Mock OpenAI API response for filesystem generation."""
    class Message:
        def __init__(self, files):
            self.parsed = FilesystemResponse(files=files)
    class Choice:
        def __init__(self, files):
            self.message = MockFilesystemResponse.Message(files)
    def __init__(self, files):
        self.choices = [self.Choice(files)]

@pytest.fixture
def mock_openai():
    """Mock OpenAI client for testing."""
    with patch('touchfs.content.generator.get_openai_client') as mock:
        client = MagicMock()
        # Mock for content generation
        # Set up content generation mock
        client.beta.chat.completions.parse.return_value = MockContentResponse("Test generated content")
        
        mock.return_value = client
        yield mock

def test_generate_with_parents(temp_dir, mock_openai, capsys):
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
        debug_stdout=True
    )
    
    assert result == 0
    assert test_file.exists()
    assert test_file.parent.exists()
    
    # Verify content was written
    content = test_file.read_text()
    assert content == "Test generated content"
    
    # Verify file info output
    captured = capsys.readouterr()
    assert str(test_file) in captured.out
    assert "chars" in captured.out
    assert "lines" in captured.out
    assert "s" in captured.out  # Time in seconds

def test_generate_with_no_content(temp_dir, mock_openai, capsys):
    """Test that generate creates empty files with --no-content flag."""
    test_file = temp_dir / "test.txt"
    
    # Call generate_main directly
    from touchfs.cli.generate_command import generate_main
    result = generate_main(
        files=[str(test_file)],
        force=True,
        debug_stdout=True,
        no_content=True
    )
    
    assert result == 0
    assert test_file.exists()
    
    # Verify file is empty
    content = test_file.read_text()
    assert content == ""
    
    # Verify output message
    captured = capsys.readouterr()
    assert f"Created empty file: {test_file}" in captured.out

def test_generate_filesystem_with_content(temp_dir, mock_openai, capsys):
    """Test filesystem generation with content by default."""
    target_dir = temp_dir / "project"
    
    # Set up mocks
    client = mock_openai.return_value
    # First call for filesystem generation - test file type relationships
    client.beta.chat.completions.parse.side_effect = [
        MockFilesystemResponse([
            "src/main.py",              # Python file
            "src/utils.py",             # Related Python file
            "web/index.html",           # HTML file
            "web/styles.css",           # Related CSS file
            "package.json",             # Config for JS/TS files
            "docs/README.md"            # Documentation
        ]),  # First call returns filesystem with related files
        *[MockContentResponse("Test generated content") for _ in range(6)]  # Content for each file
    ]
    
    # Call generate_main
    from touchfs.cli.generate_command import generate_main
    result = generate_main(
        files=[str(target_dir)],
        filesystem_generation_prompt="Create a test project",
        force=True,
        debug_stdout=True,
        yes=True  # Skip confirmation prompt
    )
    
    assert result == 0
    
    # Verify files were created with proper relationships
    assert (target_dir / "src" / "main.py").exists()
    assert (target_dir / "src" / "utils.py").exists()  # Related Python file
    assert (target_dir / "web" / "index.html").exists()
    assert (target_dir / "web" / "styles.css").exists()  # Related CSS file
    assert (target_dir / "package.json").exists()  # Config file
    assert (target_dir / "docs" / "README.md").exists()
    
    # Verify content was generated for all files
    for file in [
        "src/main.py", "src/utils.py", "web/index.html", 
        "web/styles.css", "package.json", "docs/README.md"
    ]:
        content = (target_dir / file).read_text()
        assert content == "Test generated content"
    
    # Verify tree structure output
    captured = capsys.readouterr()
    assert "Generated Filesystem Structure:" in captured.out
    # Check tree formatting
    assert "├── src/" in captured.out or "└── src/" in captured.out
    assert "│   ├── main.py" in captured.out or "│   └── main.py" in captured.out
    assert "│   └── utils.py" in captured.out or "│   ├── utils.py" in captured.out
    assert "├── web/" in captured.out or "└── web/" in captured.out
    assert "│   ├── index.html" in captured.out or "│   └── index.html" in captured.out
    assert "│   └── styles.css" in captured.out or "│   ├── styles.css" in captured.out
    assert "├── package.json" in captured.out or "└── package.json" in captured.out
    assert "├── docs/" in captured.out or "└── docs/" in captured.out
    # Verify generation info
    assert "chars" in captured.out
    assert "lines" in captured.out
    assert "s" in captured.out  # Time in seconds

def test_generate_filesystem_with_no_content(temp_dir, mock_openai, capsys):
    """Test filesystem generation with --no-content flag."""
    target_dir = temp_dir / "project"
    
    # Set up mocks
    client = mock_openai.return_value
    # Only need filesystem response for no_content test
    client.beta.chat.completions.parse.return_value = MockFilesystemResponse(["file.txt", "src/main.py"])
    
    # Call generate_main
    from touchfs.cli.generate_command import generate_main
    result = generate_main(
        files=[str(target_dir)],
        filesystem_generation_prompt="Create a test project",
        force=True,
        debug_stdout=True,
        no_content=True,
        yes=True  # Skip confirmation prompt
    )
    
    assert result == 0
    
    # Verify files were created
    test_file = target_dir / "file.txt"
    assert test_file.exists()
    main_file = target_dir / "src" / "main.py"
    assert main_file.exists()
    
    # Verify files are empty
    assert test_file.read_text() == ""
    assert main_file.read_text() == ""
    
    # Verify output message
    captured = capsys.readouterr()
    assert f"Created empty file: {test_file}" in captured.out
    assert f"Created empty file: {main_file}" in captured.out

def test_generate_multiple_with_parents(temp_dir, mock_openai, capsys):
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
        debug_stdout=True
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
        debug_stdout=True
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
        debug_stdout=True
    )
    
    assert result == 0
    assert test_file.exists()
    content = test_file.read_text()
    assert content == "Test generated content"
