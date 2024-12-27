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

3. **PromptPlugin & ModelPlugin**
   - Both plugins use the same hierarchical lookup pattern:
     1. `.llmfs/<name>` in current directory (e.g., prompt or model)
     2. `.llmfs/<name>.default` in current directory
     3. Repeat steps 1-2 in each parent directory
     4. Root `.llmfs/<name>.default` proc file
   - First non-empty file found in this chain is used
   - Allows for increasingly specific settings deeper in the directory tree
   - Supports both raw text and JSON input formats
   - Example:
     ```
     project/
     ├── .llmfs/
     │   ├── model.default  # Project-wide model (e.g., gpt-4)
     │   └── prompt.default # Project-wide prompt
     ├── src/
     │   ├── .llmfs/
     │   │   ├── model     # Override model for src/ (e.g., gpt-3.5-turbo)
     │   │   └── prompt    # Override prompt for src/
     │   └── components/
     │       └── .llmfs/
     │           ├── model # Specific model for components
     │           └── prompt # Specific prompt for components
     ```
   - Empty files are skipped in the lookup chain
   - Detailed debug logging of lookup process

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

7. **CacheControlPlugin**
   - Provides cache control through proc-like files in .llmfs/
   - Enables/disables caching globally via cache_enabled
   - Monitors cache performance via cache_stats
   - Manages cache content via cache_clear and cache_list
   - Real-time cache statistics tracking
   - Example usage:
     ```bash
     # Enable/disable caching
     echo 1 > .llmfs/cache_enabled
     echo 0 > .llmfs/cache_enabled
     
     # Monitor cache performance
     watch -n1 cat .llmfs/cache_stats
     
     # Clear cache when needed
     echo 1 > .llmfs/cache_clear
     
     # List cached content
     cat .llmfs/cache_list
     ```

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

### Caching System

LLMFS includes a robust caching system to improve performance and reduce API calls:

1. **Cache Control Files**
   Located in the `.llmfs` directory:
   ```
   .llmfs/
   ├── cache_enabled   # Write 0/1 to disable/enable caching
   ├── cache_stats     # Read-only cache statistics
   ├── cache_clear     # Write 1 to clear cache
   └── cache_list      # List of cached request hashes
   ```

2. **Enabling/Disabling Cache**
   ```bash
   # Enable caching
   echo 1 > .llmfs/cache_enabled
   
   # Disable caching
   echo 0 > .llmfs/cache_enabled
   
   # Check current status
   cat .llmfs/cache_enabled
   ```

3. **Cache Statistics**
   Monitor cache performance:
   ```bash
   cat .llmfs/cache_stats
   # Output:
   # Hits: 42
   # Misses: 7
   # Size: 128000 bytes
   # Enabled: True
   ```

4. **Managing Cache**
   ```bash
   # Clear all cached content
   echo 1 > .llmfs/cache_clear
   
   # List cached requests
   cat .llmfs/cache_list
   ```

5. **Cache Location**
   - Default: `~/.llmfs.cache/`
   - Override with `LLMFS_CACHE_FOLDER` environment variable

6. **What Gets Cached**
   - Filesystem structure generation results
   - Individual file content generation
   - Each cache entry is keyed by a hash of the request parameters
   - Cache entries are JSON files containing the generated content

7. **Cache Behavior**
   - Cache is checked before making API calls
   - Cache hits return immediately with stored content
   - Cache misses trigger normal content generation
   - Generated content is automatically cached if caching is enabled
   - Cache settings have immediate global effect
   - Cache statistics track hits and misses for performance monitoring

### Performance Considerations

- Operates in userspace via FUSE
- Memory-bound rather than I/O-bound
- Ideal for development and prototyping
- Caching significantly reduces API calls and improves response times

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.
