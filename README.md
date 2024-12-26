# 🌳 LLMFS - LLM-powered Memory Filesystem

LLMFS is an intelligent memory filesystem that generates content using OpenAI's GPT models. It combines the flexibility of in-memory storage with AI-powered content generation to create dynamic, context-aware filesystems.

## ✨ Key Features

- In-memory filesystem with JSON serialization
- OpenAI-powered content generation
- Dynamic file content generation on first read
- Extended attribute (xattr) support
- Symlink support
- Plugin system for custom content generation

## 📁 The .llmfs Directory

When mounting an LLMFS filesystem, a special `.llmfs` directory is created containing:

```
.llmfs/
├── model.default    # Selected LLM model configuration
├── prompt.default   # System prompt template
├── README          # Auto-generated filesystem documentation
├── tree            # Filesystem structure visualization
└── log            # System logs access
```

## 🚀 Installation

```bash
pip install llmfs
```

## 📖 Usage

### Basic Usage

Mount a new filesystem:
```bash
# Mount with a specific prompt
llmfs /path/to/mountpoint --prompt "Create a Python project structure"

# Mount with prompt from environment variable
LLMFS_PROMPT="Create a web application structure" llmfs /path/to/mountpoint

# Mount with prompt from file
llmfs /path/to/mountpoint --prompt /path/to/prompt.txt

# Mount an empty filesystem
llmfs /path/to/mountpoint
```

### Log Viewing

LLMFS logs are accessible through a symlink at .llmfs/log in the mount point which points to the current /var/log/llmfs/llmfs.log file:

```bash
# View logs using standard commands
tail -f .llmfs/log
cat .llmfs/log
less .llmfs/log

# Logs are automatically rotated for each invocation
# Previous logs are saved with incremented suffixes (e.g. llmfs.log.1, llmfs.log.2)
```

The logging system ensures atomic writes and consistent log ordering through file locking, making it safe for concurrent access and real-time monitoring.

Available options:
- `--prompt`: Specify generation prompt (can also use LLMFS_PROMPT env var or provide a prompt file)
- `--foreground`: Run in foreground (default: background)

### Environment Variables

- `LLMFS_PROMPT`: Filesystem generation prompt
- `OPENAI_API_KEY`: Your OpenAI API key (required)

### Fun Examples: Creating Different OS Structures

```bash
# Create a Windows 95 structure
llmfs win95_fs --prompt "Create an authentic Windows 95 filesystem structure with Program Files, Windows folder, and system files"

# Generated structure:
C:\
├── WINDOWS\
│   ├── SYSTEM\
│   └── COMMAND\
├── PROGRA~1\
└── AUTOEXEC.BAT

# Create a classic Unix system
llmfs unix_fs --prompt "Generate a classic Unix filesystem with standard directories and period-accurate system files"

# Generated structure:
/
├── bin/
├── etc/
├── usr/
│   └── local/
└── var/
```

## 🔌 Plugin System

LLMFS includes several built-in plugins:

1. **DefaultGenerator**
   - Primary content generator using OpenAI
   - Context-aware content generation
   - Uses hierarchical prompt system

2. **ModelPlugin**
   - Controls model selection via model.default
   - Supports JSON or raw model name
   - Default: gpt-4o-2024-08-06

3. **PromptPlugin**
   - Manages system prompts
   - Supports custom prompts per directory
   - Includes best practices templates

4. **LogSymlinkPlugin**
   - Creates symlink at .llmfs/log pointing to /var/log/llmfs/llmfs.log
   - Atomic logging with file locking for consistent output
   - Automatic log rotation with numbered suffixes (e.g. llmfs.log.1, llmfs.log.2)
   - Safe for concurrent access and real-time monitoring

5. **TreeGenerator**
   - Structured tree visualization
   - Shows generator assignments
   - Greppable output format

6. **ReadmeGenerator**
   - Dynamic README in .llmfs
   - Shows filesystem structure
   - Includes generation status

### Creating Custom Plugins

```python
from llmfs.content.plugins.base import BaseContentGenerator

class CustomPlugin(BaseContentGenerator):
    def generator_name(self) -> str:
        return "custom"
        
    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        return "Generated content based on filesystem context"
```

## 🔧 Technical Details

LLMFS uses FUSE (Filesystem in USErspace) to create a virtual filesystem:

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

### Key Components

1. **Memory Management**
   - In-memory file storage
   - JSON serialization support
   - Efficient content generation

2. **LLM Integration**
   - OpenAI API integration
   - Context-aware generation
   - Structured outputs using Pydantic

3. **Plugin Architecture**
   - Custom content generators
   - Dynamic file overlays
   - Extended attribute support

### Performance Considerations

- Operates in userspace via FUSE
- Memory-bound rather than I/O-bound
- Ideal for development and prototyping

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.
