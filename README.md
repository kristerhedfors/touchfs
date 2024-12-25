# LLMFS - LLM-powered Memory Filesystem

LLMFS is a memory filesystem that can generate filesystem structures using OpenAI's GPT models. It allows you to mount a virtual filesystem and optionally generate its structure based on natural language prompts.

## Features

- In-memory filesystem with JSON serialization
- OpenAI-powered filesystem structure generation
- Content generation for files on first read
- Extended attribute (xattr) support
- Symlink support
- Debug logging capabilities
- Plugin system for dynamic content generation

## Plugin System


LLMFS features a powerful plugin system that enables custom file content generation at read-time. This allows developers to create specialized file types whose content is dynamically generated based on custom logic.

#### Plugin Architecture

The plugin system is built around a few key components:

1. **ContentGenerator Protocol**: Defines the interface for all content generators
2. **BaseContentGenerator**: Abstract base class providing common functionality
3. **PluginRegistry**: Manages plugin registration and overlay files
4. **OverlayFile**: Represents virtual files created by plugins

```python
from typing import List, Dict
from llmfs.models.filesystem import FileNode
from llmfs.content.plugins.base import BaseContentGenerator

class CustomPlugin(BaseContentGenerator):
    def generator_name(self) -> str:
        return "custom"
        
    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        # Custom logic to generate file content
        return "Generated content based on filesystem context"
```

#### Built-in Plugins

1. **ReadmeGenerator**: Automatically generates filesystem documentation
```python
# Creates a dynamic README with filesystem structure visualization
overlay = OverlayFile("/README.llmfs", {"generator": "readme"})
```

2. **DefaultGenerator**: OpenAI-powered content generation
```python
# Uses GPT-4 to generate context-aware content
completion = client.beta.chat.completions.parse(
    model="gpt-4o-2024-08-06",
    messages=[...],
    response_format=GeneratedContent
)
```

For detailed plugin documentation and examples, see [Plugin System Documentation](llmfs/content/plugins/README.md).

#### Key Features

1. **Protocol-based Interface**: Clear contract for implementing content generators
2. **Context-aware Generation**: Access to filesystem context for intelligent content creation
3. **Lazy Evaluation**: Content generated only when files are read
4. **Extended Attributes**: Rich metadata support through xattrs
5. **Automatic Registration**: Simple plugin discovery and registration
6. **Overlay Files**: Support for virtual files created by plugins

## How It Works

LLMFS leverages FUSE (Filesystem in USErspace) to create a virtual filesystem that can be mounted anywhere in your Linux system. Here's a technical overview of how it works:

### FUSE Architecture

FUSE is a Linux kernel module that allows non-privileged users to create their own file systems without editing kernel code. It provides a bridge between the kernel's VFS (Virtual File System) layer and userspace filesystem implementations.

Key components:
1. **Kernel Module**: The FUSE kernel module (`fuse.ko`) that handles the kernel-side operations
2. **Userspace Library**: `libfuse` that provides the API for implementing filesystems
3. **Filesystem Implementation**: Your userspace program (in this case, LLMFS) that defines how the filesystem behaves

```
User Programs (ls, cat, etc.)
           ↓
    VFS (Kernel Space)
           ↓
     FUSE Kernel Module
           ↓
     FUSE Userspace Lib
           ↓
         LLMFS
```

### LLMFS Implementation

LLMFS implements the FUSE interface to provide:

1. **Virtual File Operations**
   - File operations are intercepted by FUSE
   - LLMFS handles them in userspace
   - No actual files are written to disk

2. **Memory Management**
   - Files and directories are stored in memory
   - State can be persisted to JSON
   - Efficient for dynamic content generation

3. **LLM Integration**
   - OpenAI API calls for content generation
   - Context-aware file creation
   - Intelligent structure generation

4. **Plugin Architecture**
   - Custom content generators
   - Dynamic file overlays
   - Extended attribute support

### Performance Considerations

Since LLMFS operates in userspace:
- Additional context switches between kernel and userspace
- Slightly higher latency than native filesystems
- Ideal for development and prototyping
- Memory-bound rather than I/O-bound

### Security Model

FUSE provides several security features:
- Non-privileged user mounting
- Mount namespace isolation
- Permission checking
- User ID mapping

## Installation

```bash
pip install llmfs
```

## Usage

### Basic Usage

```python
from llmfs import LLMFS

# Create a new filesystem
fs = LLMFS()

# Create some files and directories
fs.mkdir("/projects")
fs.write("/projects/hello.py", "print('Hello, World!')")

# Read file content
content = fs.read("/projects/hello.py")
print(content)  # prints: print('Hello, World!')

# Save filesystem state
fs.save("my_filesystem.json")

# Load existing filesystem
fs = LLMFS.load("my_filesystem.json")
```

### OpenAI Integration

```python
from llmfs import LLMFS

# Initialize with OpenAI
fs = LLMFS(use_openai=True)

# Generate filesystem structure from prompt
fs.generate_structure("""
Create a Python project structure for a web scraping tool with:
- Separate modules for different scraping strategies
- Data storage handling
- Rate limiting and retry logic
- CLI interface
""")

# Files will be created with appropriate structure and content
print(fs.list("/"))
```

### Extended Attributes

```python
from llmfs import LLMFS

fs = LLMFS()

# Set extended attributes
fs.write("/config.json", "{}")
fs.setxattr("/config.json", "version", "1.0")
fs.setxattr("/config.json", "environment", "development")

# Get extended attributes
version = fs.getxattr("/config.json", "version")
print(version)  # prints: 1.0

# List all extended attributes
attrs = fs.listxattr("/config.json")
print(attrs)  # prints: ["version", "environment"]
```

### Symlinks

```python
from llmfs import LLMFS

fs = LLMFS()

# Create some files and directories
fs.mkdir("/data")
fs.write("/data/config.json", "{}")

# Create symlink
fs.symlink("/data/config.json", "/config.json")

# Access through symlink
content = fs.read("/config.json")  # Reads /data/config.json
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
