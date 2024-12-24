import os
import pytest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from llmfs.llmfs import Memory, generate_filesystem
from pydantic import BaseModel
from openai import OpenAI
from typing import List

def test_structured_output_gpt4():
    """Test example 1: Structured Output with GPT-4"""
    # Skip if no OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    class ProjectStructure(BaseModel):
        name: str
        directories: List[str]
        files: List[str]
        description: str

    client = OpenAI()
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "Extract project structure information from the description."},
            {"role": "user", "content": "Create a web application project with a frontend directory for React components, a backend directory for API endpoints, and include necessary configuration files."},
        ],
        response_format=ProjectStructure,
    )

    project = completion.choices[0].message.parsed
    
    # Verify structure
    assert isinstance(project, ProjectStructure)
    assert isinstance(project.name, str)
    assert isinstance(project.directories, list)
    assert isinstance(project.files, list)
    assert isinstance(project.description, str)
    
    # Verify content expectations
    assert any("frontend" in d.lower() for d in project.directories), "Frontend directory not found"
    assert any("backend" in d.lower() for d in project.directories), "Backend directory not found"
    assert any(f.endswith(('.json', '.js', '.ts', '.yaml', '.yml')) for f in project.files), "No configuration files found"

def test_generate_python_project():
    """Test example 2: Generate a Python project structure"""
    # Skip if no OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
        
    prompt = "Create a Python project with src directory, tests, and documentation"
    fs_data = generate_filesystem(prompt)
    
    fs = Memory(fs_data["data"])
    
    # Verify basic structure
    root_children = fs._root._data["/"]["children"]
    assert "src" in root_children
    assert "tests" in root_children
    assert "docs" in root_children

def test_manual_filesystem_operations():
    """Test example 3: Manual filesystem operations"""
    fs = Memory()
    
    # Test directory creation
    fs.mkdir("/mydir", 0o755)
    assert fs._root._data["/mydir"]["type"] == "directory"
    
    # Test file creation and writing
    fd = fs.create("/mydir/hello.txt", 0o644)
    fs.write("/mydir/hello.txt", b"Hello, World!", 0, fd)
    
    # Test file reading
    content = fs.read("/mydir/hello.txt", 1024, 0, fd)
    assert content.decode('utf-8') == "Hello, World!"
    
    # Test symlink creation
    fs.symlink("/mydir/link", "hello.txt")
    assert fs._root._data["/mydir/link"]["type"] == "symlink"
    
    # Test directory listing
    entries = fs.readdir("/mydir", None)
    assert sorted(entries) == ['.', '..', 'hello.txt', 'link']

def test_extended_attributes():
    """Test example 4: Working with extended attributes"""
    fs = Memory()
    
    # Test file creation
    fd = fs.create("/metadata.txt", 0o644)
    
    # Test setting xattrs
    fs.setxattr("/metadata.txt", "user.author", "John Doe", None)
    fs.setxattr("/metadata.txt", "user.version", "1.0", None)
    
    # Test getting xattr
    author = fs.getxattr("/metadata.txt", "user.author")
    assert author == "John Doe"
    
    # Test listing xattrs
    xattrs = fs.listxattr("/metadata.txt")
    assert sorted(xattrs) == ["user.author", "user.version"]

def test_basic_file_operations():
    """Test additional basic file operations"""
    fs = Memory()
    
    # Create and write to a file
    fd = fs.create("/test.txt", 0o644)
    fs.write("/test.txt", b"Initial content", 0, fd)
    
    # Read content
    content = fs.read("/test.txt", 1024, 0, fd)
    assert content.decode('utf-8') == "Initial content"
    
    # Truncate file
    fs.truncate("/test.txt", 7)
    content = fs.read("/test.txt", 1024, 0, fd)
    assert content.decode('utf-8') == "Initial"
    
    # Unlink (delete) file
    fs.unlink("/test.txt")
    with pytest.raises(KeyError):
        fs._root._data["/test.txt"]

def test_directory_operations():
    """Test additional directory operations"""
    fs = Memory()
    
    # Create nested directories
    fs.mkdir("/parent", 0o755)
    fs.mkdir("/parent/child", 0o755)
    
    # Verify structure
    assert fs._root._data["/parent"]["type"] == "directory"
    assert fs._root._data["/parent/child"]["type"] == "directory"
    
    # List parent directory
    entries = fs.readdir("/parent", None)
    assert sorted(entries) == ['.', '..', 'child']
    
    # Remove empty directory
    fs.rmdir("/parent/child")
    entries = fs.readdir("/parent", None)
    assert sorted(entries) == ['.', '..']
