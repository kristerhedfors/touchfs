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
- Hierarchical configuration through `.llmfs/config` files

## Configuration

LLMFS uses a hierarchical configuration system that allows for flexible customization of behavior. Here's how it works:

### Default Configuration

The default configuration is defined within the LLMFS Python package and includes settings like:

```yaml
generation:
    model: gpt-4o-2024-08-06  # OpenAI model to use
    temperature: 0.7          # Generation temperature
    max_tokens: 2000         # Maximum tokens per generation

logging:
    level: info              # Logging level (debug, info, warning, error)
    file_logging: true       # Enable file logging
    log_file: /var/log/llmfs/llmfs.log

plugins:
    readme:
        enabled: true        # Enable README generation
        template: default    # README template to use
    config:
        enabled: true        # Enable config plugin
        validate_schema: true # Validate config files
```

### Runtime Configuration

When an LLMFS filesystem is mounted, a `.llmfs/config` file is automatically generated in its root directory. This file represents the current running configuration, initially based on the default settings from the Python package.

### Hierarchical Override System

The configuration system follows a hierarchical model where:

1. **Base Configuration**: Starts with defaults from the Python package
2. **Root Configuration**: Generated `.llmfs/config` in filesystem root
3. **Directory Configuration**: Optional `.llmfs/config` files in subdirectories
4. **Inheritance**: Configurations merge up the directory tree
5. **Override Priority**: Child configurations take precedence over parent settings

For example, in this structure:
```
/mounted-fs/
├── .llmfs/config           # Generated root config
├── projects/
│   ├── .llmfs/config       # Optional override for projects/
│   └── webapp/
│       └── .llmfs/config   # Optional override for webapp/
```

Any manually created `.llmfs/config` files in subdirectories will override their parent directory's settings while inheriting unspecified values. This allows for fine-grained control over LLMFS behavior at different levels of your filesystem hierarchy - for example, using different OpenAI models or logging settings for specific projects.

## Plugin System

LLMFS features a powerful plugin system that enables custom file content generation at read-time. This allows developers to create specialized file types whose content is dynamically generated based on custom logic.

### Plugin Categories

1. **System Configuration Plugins**
   - Logging level control
   - Model selection
   - Configuration management
   - System prompts

2. **Content Generation Plugins**
   - Generation parameters (temperature, tokens)
   - Default content generation
   - Custom content generators

3. **Filesystem Plugins**
   - Filesystem documentation
   - Tree visualization
   - System logs access

### Plugin Architecture

The plugin system is built around these key components:

1. **ContentGenerator Protocol**: Defines the interface for all content generators
2. **BaseContentGenerator**: Abstract base class providing common functionality
3. **ProcPlugin**: Base class for auto-generated overlay files
4. **PluginRegistry**: Manages plugin registration and overlay files
5. **OverlayFile**: Represents virtual files created by plugins

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

### Built-in Plugins

1. **DefaultGenerator**: Primary content generator using OpenAI
   - Context-aware content generation
   - Uses hierarchical prompt system
   - Temperature 0.2 for consistent output

2. **ModelPlugin**: Controls model selection
   - Manages model.default in .llmfs
   - Supports JSON or raw model name
   - Default: gpt-4o-2024-08-06

3. **PromptPlugin**: Manages system prompts
   - Provides prompt.default in .llmfs
   - Supports custom prompts per directory
   - Includes best practices templates

4. **LogPlugin**: System log access
   - Exposes /var/log/llmfs/llmfs.log
   - Real-time log viewing
   - Error handling for missing logs

5. **TreeGenerator**: Filesystem visualization
   - Structured tree view
   - Shows generator assignments
   - Greppable output format

6. **ReadmeGenerator**: Documentation generator
   - Dynamic README in .llmfs
   - Shows filesystem structure
   - Includes generation status

The .llmfs directory contains auto-generated files:

```
.llmfs/
├── model.default    # Selected LLM model
├── prompt.default   # System prompt template
├── README          # Filesystem documentation
├── tree            # Filesystem tree visualization
└── log             # System logs access
```

For detailed plugin documentation and examples, see [Plugin System Documentation](llmfs/content/plugins/README.md).

### Key Features

1. **Protocol-based Interface**: Clear contract for implementing content generators
2. **Context-aware Generation**: Access to filesystem context for intelligent content creation
3. **Lazy Evaluation**: Content generated only when files are read
4. **Extended Attributes**: Rich metadata support through xattrs
5. **Automatic Registration**: Simple plugin discovery and registration
6. **Overlay Files**: Support for virtual files created by plugins
7. **Hierarchical Configuration**: Plugin settings can be overridden at directory level
8. **Dynamic Documentation**: Auto-generated filesystem documentation
9. **System State Access**: Virtual files expose runtime information

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
