# TouchFS Architecture

TouchFS integrates language model capabilities with the filesystem layer.

## Technical Overview

TouchFS uses FUSE (Filesystem in USErspace):

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

3. **File Marking**:
   - Initial filesystem: All files marked automatically
   - New files: Require explicit touch command
   - Manual: Use setfattr for existing files

## Plugin System

Built-in plugins:

1. **DefaultGenerator**
   - Uses OpenAI for content generation
   - Uses hierarchical prompts

2. **ModelPlugin**
   - Sets model via model.default
   - Accepts JSON or model name
   - Default: gpt-4o-2024-08-06

3. **PromptPlugin & ModelPlugin**
   - Hierarchical lookup:
     1. `.touchfs/<name>` in current directory
     2. `.touchfs/<name>.default` in current directory
     3. Steps 1-2 in parent directories
     4. Root `.touchfs/<name>.default` proc file
   - Uses first non-empty file found

4. **ImageGenerator**
   - Uses OpenAI DALL-E API
   - Supports .jpg, .jpeg, .png
   - Generates image prompts

5. **LogSymlinkPlugin**
   - Creates .touchfs/log -> /var/log/touchfs/touchfs.log
   - Uses file locking
   - Rotates logs

6. **TreeGenerator**
   - Shows filesystem tree
   - Lists generator assignments
   - Shows configuration

7. **ReadmeGenerator**
   - Creates .touchfs readme
   - Shows filesystem structure
   - Shows generation status

8. **CacheControlPlugin**
   - Controls cache via proc-like files
   - Toggles global caching
   - Tracks cache metrics

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
   touchfs_context .
   
   # Set token limit
   touchfs_context . --max-tokens 4000
   
   # Exclude files
   touchfs_context . --exclude "*.pyc" --exclude "*/__pycache__/*"
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
