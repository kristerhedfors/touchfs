# LLMFS - LLM-powered Memory Filesystem

LLMFS is a FUSE-based memory filesystem backed by JSON that can generate filesystem structures using OpenAI's GPT models. It allows you to mount a virtual filesystem and optionally generate its structure based on natural language prompts.

## Features

- In-memory filesystem with JSON serialization
- OpenAI-powered filesystem structure generation
- FUSE implementation with full filesystem operations support
- Pydantic models for data validation
- Extended attribute (xattr) support
- Symlink support

## Installation

1. Install system dependencies (Ubuntu/Debian):
```bash
sudo apt-get install python3-pip fuse
```

2. Install the package:
```bash
pip install .
```

## Usage

### Basic Usage

1. Create a mount point:
```bash
mkdir /tmp/llmfs
```

2. Mount an empty filesystem:
```bash
llmfs /tmp/llmfs
```

### LLM-Generated Filesystem

You can generate filesystem structure using natural language prompts in three ways:

1. Using environment variable:
```bash
export LLMFS_PROMPT="Create a python project structure with tests"
llmfs /tmp/llmfs
```

2. Using command line argument:
```bash
llmfs /tmp/llmfs "Create a web development project with HTML, CSS, and JavaScript files"
```

3. Using a prompt file:
```bash
echo "Create a data science project with notebooks and data folders" > prompt.txt
llmfs /tmp/llmfs prompt.txt
```

### Examples

1. Structured Output with GPT-4:
```python
from pydantic import BaseModel
from openai import OpenAI
from typing import List

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
assert isinstance(project.name, str)
assert isinstance(project.directories, list)
assert isinstance(project.files, list)
assert isinstance(project.description, str)
```

2. Generate a Python project structure:
```python
import os
from llmfs.llmfs import Memory, generate_filesystem

# Generate filesystem structure
prompt = "Create a Python project with src directory, tests, and documentation"
fs_data = generate_filesystem(prompt)

# Create filesystem instance
fs = Memory(fs_data["data"])

# Access generated structure
root_children = fs._root._data["/"]["children"]
assert "src" in root_children
assert "tests" in root_children
assert "docs" in root_children
```

3. Manual filesystem operations:
```python
from llmfs.llmfs import Memory

# Create filesystem instance
fs = Memory()

# Create a directory
fs.mkdir("/mydir", 0o755)

# Create and write to a file
fd = fs.create("/mydir/hello.txt", 0o644)
fs.write("/mydir/hello.txt", b"Hello, World!", 0, fd)

# Read file content
content = fs.read("/mydir/hello.txt", 1024, 0, fd)
assert content.decode('utf-8') == "Hello, World!"

# Create a symlink
fs.symlink("/mydir/link", "hello.txt")

# List directory contents
entries = fs.readdir("/mydir", None)
assert sorted(entries) == ['.', '..', 'hello.txt', 'link']
```

4. Working with extended attributes:
```python
from llmfs.llmfs import Memory

# Create filesystem instance
fs = Memory()

# Create a file
fd = fs.create("/metadata.txt", 0o644)

# Set extended attributes
fs.setxattr("/metadata.txt", "user.author", "John Doe", None)
fs.setxattr("/metadata.txt", "user.version", "1.0", None)

# Get extended attribute
author = fs.getxattr("/metadata.txt", "user.author")
assert author == "John Doe"

# List extended attributes
xattrs = fs.listxattr("/metadata.txt")
assert sorted(xattrs) == ["user.author", "user.version"]
```

## Requirements

- Python >= 3.6
- FUSE
- OpenAI API key (for LLM-powered generation)
- Dependencies:
  - fusepy
  - openai>=1.0.0
  - pydantic>=2.0.0

## Environment Variables

- `OPENAI_API_KEY`: Required for LLM-powered filesystem generation
- `LLMFS_PROMPT`: Optional prompt for filesystem generation

## Notes

- The filesystem is in-memory and changes are not persisted across mounts
- The filesystem structure is serialized to a special file `/fs.json`
- When using LLM generation, ensure your OpenAI API key is set in the environment
- The mounted filesystem supports all standard operations (create, read, write, delete, etc.)

## License

MIT License
