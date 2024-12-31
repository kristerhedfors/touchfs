# TouchFS Architecture

TouchFS represents a sophisticated integration of large language model capabilities directly into the filesystem layer. This document details the technical architecture and implementation details of the system.

## 🔧 Technical Overview

TouchFS uses FUSE (Filesystem in USErspace) to create a virtual filesystem:

```
User Programs (ls, cat, etc.)
           ↓
    VFS (Kernel Space)
           ↓
     FUSE Kernel Module
           ↓
     FUSE Userspace Lib
           ↓
         TouchFS
```

## 🔄 Content Generation

TouchFS uses a safe and predictable content generation strategy:

1. **Generation Trigger**: Content is only generated when:
   - A file is marked with the `generate_content` extended attribute (xattr)
   - AND the file is empty (0 bytes)
   - This happens during size calculation (stat) operations

2. **Safety First**: This approach ensures:
   - No accidental overwrites of existing content
   - Predictable generation behavior
   - Clear separation between marked and unmarked files

3. **File Marking Methods**:
   - Initial filesystem generation: All created files are automatically marked
   - New files: Must be explicitly marked using the touch command
   - Manual marking: Can use setfattr to mark existing files

## 🔌 Plugin System

TouchFS includes several built-in plugins:

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
     1. `.touchfs/<name>` in current directory (e.g., prompt or model)
     2. `.touchfs/<name>.default` in current directory
     3. Repeat steps 1-2 in each parent directory
     4. Root `.touchfs/<name>.default` proc file
   - First non-empty file found in this chain is used
   - Allows for increasingly specific settings deeper in the directory tree

4. **ImageGenerator**
   - Creates images using OpenAI's DALL-E API
   - Supports .jpg, .jpeg, and .png formats
   - Intelligent prompt generation

5. **LogSymlinkPlugin**
   - Creates symlink at .touchfs/log pointing to /var/log/touchfs/touchfs.log
   - Atomic logging with file locking
   - Automatic log rotation

6. **TreeGenerator**
   - Structured tree visualization
   - Shows generator assignments and configuration

7. **ReadmeGenerator**
   - Dynamic readme in .touchfs
   - Shows filesystem structure
   - Includes generation status

8. **CacheControlPlugin**
   - Provides cache control through proc-like files
   - Enables/disables caching globally
   - Monitors cache performance

### Creating Custom Plugins

```python
from touchfs.content.plugins.base import BaseContentGenerator

class CustomPlugin(BaseContentGenerator):
    def generator_name(self) -> str:
        return "custom"
        
    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        return "Generated content based on filesystem context"
```

## 🔍 Context System

TouchFS includes a sophisticated context retrieval system that follows Model Context Protocol (MCP) principles:

### Context Generation

The system provides two main ways to work with context:

1. **Built-in Context Management**
   - Hierarchical context inheritance through filesystem structure
   - Automatic context collection during content generation
   - Token-aware content inclusion
   - Smart file ordering (e.g., __init__.py files first)

2. **Command Line Tool**
   ```bash
   # Generate context from current directory
   touchfs_context .
   
   # Specify maximum tokens
   touchfs_context . --max-tokens 4000
   
   # Exclude specific patterns
   touchfs_context . --exclude "*.pyc" --exclude "*/__pycache__/*"
   ```

### Context Features

- **Token Management**
  - Automatic token counting using tiktoken
  - Configurable token limits
  - Smart content truncation when limits are reached

- **MCP-Compliant Output**
  - Structured file content as resources
  - Rich metadata for each file
  - URI-based resource identification
  - Organized by module/directory structure

## 📝 Logging System

### Overview
TouchFS implements a robust logging system that provides detailed context for debugging, monitoring, and software engineering tasks. The logging system is designed to maintain a comprehensive history while preventing unbounded growth through automatic rotation.

### Log File Location
- Primary log file: `/var/log/touchfs/touchfs.log`
- Accessible via symlink: `/.touchfs/log` -> `/var/log/touchfs/touchfs.log`
- Rotated logs: `/var/log/touchfs/touchfs.log.{N}` where N is an incrementing number

### Log Rotation
- Automatic rotation occurs on each filesystem mount
- Previous log file is renamed with an incrementing suffix
- Ensures logs don't grow unbounded while preserving historical context
- Atomic operations with file locking prevent data loss during rotation

### Log Format
Each log entry contains rich contextual information:
```
timestamp - name - level - filename:line - function - process_id - thread_id - message
```

## 🔧 Caching System

TouchFS includes a robust caching system to improve performance and reduce API calls:

1. **Cache Control Files**
   Located in the `.touchfs` directory:
   ```
   .touchfs/
   ├── cache_enabled   # Write 0/1 to disable/enable caching
   ├── cache_stats     # Read-only cache statistics
   ├── cache_clear     # Write 1 to clear cache
   └── cache_list      # List of cached request hashes
   ```

2. **Cache Location**
   - Default: `~/.touchfs.cache/`
   - Override with `TOUCHFS_CACHE_FOLDER` environment variable

3. **Cache Behavior**
   - Cache is checked before making API calls
   - Cache hits return immediately with stored content
   - Cache misses trigger normal content generation
   - Generated content is automatically cached if caching is enabled
   - Cache settings have immediate global effect
   - Cache statistics track hits and misses for performance monitoring

## Performance Considerations

- Operates in userspace via FUSE
- Memory-bound rather than I/O-bound
- Ideal for development and prototyping
- Caching significantly reduces API calls and improves response times
