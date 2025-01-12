# TouchFS Architecture

TouchFS integrates language model capabilities with the filesystem layer.

## Technical Overview

## Configuration System

TouchFS uses a hierarchical configuration system that supports both file-based configuration and environment variables:

### Model Configuration

The model configuration determines which language model is used for generation. It can be set through:

1. **Environment Variable**:
   ```bash
   export TOUCHFS_DEFAULT_MODEL="gpt-4o-2024-08-06"
   ```

2. **Configuration Files** (in order of precedence):
   - `.model` in current directory
   - `.model` in overlay path (if mounted with --overlay)
   - `.touchfs/model_default` in root directory
   - System default (gpt-4o-2024-08-06)

Files can contain either:
- Simple model name: `gpt-4o-2024-08-06`
- JSON configuration:
  ```json
  {
    "model": "gpt-4o-2024-08-06",
    "temperature": 0.7,
    "max_tokens": 4000
  }
  ```

### Prompt Configuration

Prompts control how content is generated. They can be set through:

1. **Environment Variable**:
   ```bash
   export TOUCHFS_DEFAULT_PROMPT="Write modern TypeScript code"
   ```

2. **Command Line**:
   ```bash
   touchfs mount workspace -p "Write modern TypeScript code"
   ```

3. **Configuration Files** (in order of precedence):
   - `.prompt` in current directory
   - `.prompt` in overlay path (if mounted with --overlay)
   - `.touchfs/prompt_default` in root directory
   - System default prompt

Files can contain either:
- Simple prompt text
- JSON configuration:
  ```json
  {
    "prompt": "Write modern TypeScript code",
    "style": "comprehensive",
    "format": "documentation-first"
  }
  ```

### Configuration Inheritance

Configuration uses a single `.touchfs` directory at the root of the mounted filesystem, with additional configuration possible through `.prompt` and `.model` files:

1. **Search Order**:
   ```
   .prompt (or .model) in current directory
   ↓
   overlay_path/.prompt (or .model) (if --overlay used)
   ↓
   .touchfs/prompt_default (or model_default) in root
   ↓
   environment variables
   ↓
   system defaults
   ```

2. **Configuration Structure**:
   - `.touchfs` directory exists only in filesystem root
   - `.prompt` and `.model` files can exist in any directory or overlay
   - Configuration from root `.touchfs` applies to all subdirectories
   - CLI arguments override file configurations
   - Environment variables override file configurations but not CLI args
   - Example:
     ```
     /workspace/.touchfs/prompt_default  # Root configuration
     /workspace/project1/.prompt         # Project-specific override
     /workspace/project2/.model          # Project-specific model
     ```

3. **Overlay Mounts**:
   When mounting with --overlay:
   - Only `.prompt` and `.model` files from overlay are considered
   - Allows existing projects to maintain their configuration


> **⚠️ Platform Support:** TouchFS currently only supports Linux systems. While macOS support might be possible with macFUSE in the future, this integration has not been implemented yet.

TouchFS uses FUSE (Filesystem in USErspace) on Linux:

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

### Mount/Unmount Operations

TouchFS provides two ways to unmount a filesystem:

1. Using the mount command with -u flag:
   ```bash
   touchfs mount -u /path/to/mount
   ```

2. Using the dedicated umount command:
   ```bash
   touchfs umount /path/to/mount [--force] [--debug]
   ```

The -u flag on `touchfs mount` is recommended as it handles busy mount points automatically. For more control over the unmount process, use `touchfs umount` with its additional options.

## Content Generation

Content generation rules:

1. **Generation Trigger**: Content generates when:
   - File has `generate_content` extended attribute (xattr)
   - File is empty (0 bytes)
   - During size calculation (stat) operations

2. **File Safety**:
   - No overwrites of existing content
   - Generation only on marked empty files
   - Clear file marking state

3. **File Marking and Generation**:
   - Initial filesystem: All files marked automatically
   - New files: Two approaches:
     1. Use `touchfs touch` to mark files for later generation (sets xattr)
     2. Use `touchfs generate` to directly generate content
   - Manual: Use setfattr for existing files
   - Generation methods:
     1. Mount-based: Files marked with xattr generate content when accessed
     2. Direct: Using generate command for immediate content generation

## Plugin System

Built-in plugins:

1. **DefaultGenerator**
The primary content generation plugin that interfaces with OpenAI's API. It processes the filesystem context and prompt information to generate appropriate content for files. This plugin handles the core functionality of converting filesystem paths and context into meaningful content.

2. **ModelPlugin**
Controls which language model is used for generation. The model selection is configured through the root `.touchfs/model_default` file, which can contain either a raw model name or a JSON configuration. The default model is gpt-4o-2024-08-06. This plugin enables consistent model selection across the filesystem.

3. **ImageGenerator**
Handles the creation of image files using OpenAI's DALL-E API. When encountering supported image formats (.jpg, .jpeg, .png), this plugin automatically generates appropriate prompts and creates corresponding images. This enables automatic generation of contextually relevant images within your filesystem structure.

4. **LogSymlinkPlugin**
Creates and maintains a symlink from `.touchfs/log` to the system log file at `/var/log/touchfs/touchfs.log`. This plugin implements atomic logging with file locking and handles log rotation to prevent unbounded growth while preserving historical data. The symlink provides easy access to logs for debugging and monitoring.

5. **TreeGenerator**
Provides a visual representation of the filesystem structure. It displays the current state of files, their associated generators, and active configuration settings. This visualization helps understand how different parts of the filesystem are configured for content generation.

6. **ReadmeGenerator**
Creates and maintains a dynamic readme file in the `.touchfs` directory. This readme contains the current filesystem structure, generation status of files, and active configuration settings. It serves as a live documentation of the filesystem's current state.

7. **CacheControlPlugin**
Manages the content generation cache through proc-like files in `.touchfs`. These files allow enabling/disabling caching, viewing cache statistics, and clearing cached content. The plugin helps reduce API calls and improves response times by caching previously generated content.

### Plugin Implementation

```python
from touchfs.content.plugins.base import BaseContentGenerator

class CustomPlugin(BaseContentGenerator):
    def generator_name(self) -> str:
        return "custom"
        
    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        return "Generated content based on filesystem context"
```

## Context System

Context retrieval follows Model Context Protocol (MCP):

### Context Generation

Two context methods:

1. **Built-in Context**
   - Inherits through filesystem hierarchy
   - Collects during generation
   - Counts tokens
   - Orders files (__init__.py first)

2. **CLI Tool**
   ```bash
   # Generate from current directory
   touchfs context .
   
   # Set token limit
   touchfs context . --max-tokens 4000
   
   # Exclude files
   touchfs context . --exclude "*.pyc" --exclude "*/__pycache__/*"
   ```

### Context Features

- **Token Management**
  - Uses tiktoken for counting
  - Configurable limits
  - Truncates at limits

- **MCP Output**
  - Files as resources
  - File metadata
  - URI identifiers
  - Module/directory organization

## Logging System

### Core Components
- Main log: `/var/log/touchfs/touchfs.log`
- Symlink: `/.touchfs/log` -> `/var/log/touchfs/touchfs.log`
- Rotated: `/var/log/touchfs/touchfs.log.{N}`

### Log Rotation
- Rotates on filesystem mount
- Increments previous log suffix
- Uses file locking
- Prevents data loss during rotation

### Log Format
```
timestamp - name - level - filename:line - function - process_id - thread_id - message
```

## Caching System

Cache implementation:

1. **Control Files**
   ```
   .touchfs/
   ├── cache_enabled   # 0/1 toggle
   ├── cache_stats     # Statistics
   ├── cache_clear     # Clear trigger
   └── cache_list      # Cache entries
   ```

2. **Location**
   - Default: `~/.touchfs.cache/`
   - Override: `TOUCHFS_CACHE_FOLDER`

3. **Operation**
   - Checks cache before API calls
   - Returns cached content on hits
   - Generates on misses
   - Caches new content if enabled
   - Global settings
   - Tracks performance metrics

## Performance Notes

- FUSE userspace operation
- Memory-bound
- Development/prototyping usage
- Cache reduces API calls
