# LLMFS - LLM-powered Memory Filesystem

LLMFS is a memory filesystem that can generate filesystem structures using OpenAI's GPT models. It allows you to mount a virtual filesystem and optionally generate its structure based on natural language prompts.

## Features

- In-memory filesystem with JSON serialization
- OpenAI-powered filesystem structure generation
- Content generation for files on first read
- Extended attribute (xattr) support
- Symlink support
- Debug logging capabilities

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

3. Mount with debug logging:
```bash
llmfs /tmp/llmfs --debug
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
llmfs /tmp/llmfs --prompt "Create a web development project with HTML, CSS, and JavaScript files"
```

3. Using a prompt file:
Create a file containing your prompt and pass its path as the prompt argument.

### Command Line Options

```
usage: llmfs <mountpoint> [--prompt PROMPT] [--foreground] [--debug]
   or: LLMFS_PROMPT="prompt" llmfs <mountpoint>

Arguments:
  mountpoint            Directory where the filesystem will be mounted
  --prompt PROMPT      Prompt for generating the filesystem structure
  --foreground, -f     Run in foreground (default: run in background)
  --debug             Enable debug logging
```

### Structured Output Example

The filesystem generator uses structured output for consistent filesystem creation:

```python
from pydantic import BaseModel
from openai import OpenAI
from typing import Dict, Any

class FilesystemStructure(BaseModel):
    data: Dict[str, Any]
    description: str

client = OpenAI()
completion = client.beta.chat.completions.parse(
    model="gpt-4o-2024-08-06",
    messages=[
        {"role": "system", "content": "Generate filesystem structure from the description."},
        {"role": "user", "content": "Create a web application project with frontend and backend directories"},
    ],
    response_format=FilesystemStructure,
)

fs_structure = completion.choices[0].message.parsed
```

### Python API Usage

```python
from llmfs.core.operations import Memory
from llmfs.content.generator import generate_filesystem

# Generate filesystem structure
prompt = "Create a Python project with src directory and tests"
fs_data = generate_filesystem(prompt)["data"]

# Create filesystem instance
fs = Memory(fs_data)

# Or create an empty filesystem
fs = Memory()

# The filesystem supports standard operations:
# - Creating files and directories
# - Reading and writing files
# - Creating symlinks
# - Managing extended attributes
# - Listing directory contents
```

## Special Features

### Dynamic Content Generation

Files are created with null content initially. On first read, if a file's content is null, LLMFS will automatically generate appropriate content based on:
- The file's path and name
- The overall filesystem structure
- The file's context within the project

### Filesystem State

- The filesystem is in-memory and changes are not persisted across mounts
- The current filesystem structure is serialized to a special file `/fs.json`
- All filesystem operations (create, read, write, delete, etc.) are supported

## Requirements

- Python >= 3.6
- FUSE
- OpenAI API key (for LLM-powered generation)
- Dependencies listed in requirements.txt

## Environment Variables

- `OPENAI_API_KEY`: Required for LLM-powered filesystem generation
- `LLMFS_PROMPT`: Optional prompt for filesystem generation

## License

MIT License
