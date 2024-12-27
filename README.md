# 🌳 LLMFS - LLM-powered Memory Filesystem

LLMFS is an intelligent memory filesystem that generates content using OpenAI's GPT models. It combines the flexibility of in-memory storage with AI-powered content generation to create dynamic, context-aware filesystems.

## ✨ Key Features

- In-memory filesystem with JSON serialization
- OpenAI-powered content generation
- Dynamic file content generation on first read
- Extended attribute (xattr) support
- Symlink support
- Plugin system for custom content generation

## 🚀 Getting Started

### Installation

```bash
pip install llmfs
```

### Quick Start

Let's create a Python project structure using LLMFS:

```bash
# Mount a new filesystem
llmfs ~/python_project --prompt "Create a modern Python project with tests and CI"

# Explore the generated structure
cd ~/python_project
ls -la

# You'll see a complete project structure:
src/
tests/
.github/workflows/
requirements.txt
setup.py
README.md
```

Every file is generated on-demand with context-aware content. Try reading any file:
```bash
cat src/main.py        # View the main implementation
cat tests/test_main.py # View corresponding tests
cat setup.py          # View project configuration
```

### Customizing Your Environment

When you mount an LLMFS filesystem, you'll find a `.llmfs` directory that helps you control and monitor the system:

```bash
# View the current filesystem structure
cat .llmfs/tree

# Read the auto-generated documentation
cat .llmfs/README

# Monitor system logs
tail -f .llmfs/log

# Change the AI model (must support structured output)
echo "gpt-4o-2024-08-06" > .llmfs/model.default

# Customize generation prompts
echo "Focus on security best practices" > .llmfs/prompt.default
```

### Improving Performance

LLMFS includes a caching system to speed up repeated operations:

```bash
# Enable caching
echo 1 > .llmfs/cache_enabled

# Monitor cache performance
watch -n1 cat .llmfs/cache_stats

# Clear cache if needed
echo 1 > .llmfs/cache_clear
```

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `LLMFS_PROMPT`: Default generation prompt
- `LLMFS_CACHE_FOLDER`: Custom cache location (default: ~/.llmfs.cache)

### Fun Examples: Creating Different Project Types

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
     │   ├── model.default  # Project-wide model (gpt-4o-2024-08-06)
     │   └── prompt.default # Project-wide prompt
     ├── src/
     │   ├── .llmfs/
     │   │   ├── model     # Override model if needed
     │   │   └── prompt    # Override prompt for src/
     │   └── components/
     │       └── .llmfs/
     │           ├── model # Specific model settings
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
