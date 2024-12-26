# LLMFS Plugin System

The LLMFS plugin system provides a flexible way to generate dynamic content for files in the virtual filesystem. This document explains how plugins work and how to create new ones.

## Architecture

The plugin system consists of several key components:

1. **ContentGenerator Protocol** - Defines the interface that all plugins must implement
2. **BaseContentGenerator** - Abstract base class providing common functionality
3. **ProcPlugin** - Specialized base class for auto-generated overlay files
4. **PluginRegistry** - Manages plugin registration and overlay files
5. **OverlayFile** - Represents virtual files created by plugins

### Core Interfaces

Every plugin must implement these key methods:

```python
def generator_name(self) -> str:
    """Return the unique name of this generator."""
    
def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
    """Generate content for a file."""
```

## Plugin Types

### 1. Base Plugins

The `BaseContentGenerator` class provides basic plugin functionality. Use this when you need complete control over file handling and overlay creation.

```python
from .base import BaseContentGenerator

class MyPlugin(BaseContentGenerator):
    def generator_name(self) -> str:
        return "myplugin"
        
    def get_overlay_files(self) -> List[OverlayFile]:
        """Optional: Provide static overlay files"""
        return []
        
    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        return "Generated content for " + path
```

### 2. Proc Plugins

The `ProcPlugin` class is designed for plugins that provide auto-generated overlay files in the `.llmfs` directory, similar to Linux's `/proc` filesystem. These plugins create virtual files whose contents are generated on-demand and reflect the current system state.

```python
from .proc import ProcPlugin

class MyProcPlugin(ProcPlugin):
    def generator_name(self) -> str:
        return "myproc"
        
    def get_proc_path(self) -> str:
        """Define where the overlay file appears in .llmfs"""
        return "myfile"  # Creates .llmfs/myfile
        
    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        return "Auto-generated content"
```

Key features of ProcPlugins:
- Automatically creates an overlay file in `.llmfs`
- Handles path resolution and file matching
- Content is generated on-demand when the file is read
- Perfect for system state reflection and dynamic configuration

## Real-World Examples

### 1. Config Plugin

The `ConfigPlugin` demonstrates a ProcPlugin that handles hierarchical configuration:

```python
class ConfigPlugin(ProcPlugin):
    def generator_name(self) -> str:
        return "config"
        
    def get_proc_path(self) -> str:
        return "config"  # Creates .llmfs/config
    
    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        # Get parent configuration
        parent_config = self._get_parent_config(path, fs_structure)
        
        if node.content:
            # Merge new config with parent
            new_config = self._load_yaml(node.content)
            if new_config and self._validate_config(new_config):
                return yaml.dump(self._merge_configs(parent_config, new_config))
        
        return yaml.dump(parent_config)
```

Key features:
- Hierarchical configuration inheritance
- YAML validation and merging
- Support for both global and per-directory configs

### 2. README Generator

The `ReadmeGenerator` shows how a ProcPlugin can create filesystem documentation:

```python
class ReadmeGenerator(ProcPlugin):
    def generator_name(self) -> str:
        return "readme"
        
    def get_proc_path(self) -> str:
        return "README"  # Creates .llmfs/README
    
    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        # Generates a tree visualization of the filesystem
        tree_lines = self._build_tree("/", fs_structure)
        return "\n".join(tree_lines)
```

Key features:
- Auto-generates filesystem documentation
- Updates dynamically as filesystem changes
- Includes file generation status

### 3. Default Generator

The `DefaultGenerator` shows a base plugin that integrates with external APIs:

```python
class DefaultGenerator(BaseContentGenerator):
    def can_handle(self, path: str, node: FileNode) -> bool:
        """Handles any file without a specific generator"""
        return (node.xattrs is None or 
                "generator" not in node.xattrs or 
                node.xattrs.get("generator") == self.generator_name())
    
    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        # Uses OpenAI to generate context-aware content
        client = get_openai_client()
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[...],
            response_format=GeneratedContent
        )
        return completion.choices[0].message.parsed.content
```

## Best Practices

1. **Choosing Plugin Type**
   - Use `ProcPlugin` for auto-generated files in `.llmfs`
   - Use `BaseContentGenerator` for more complex scenarios
   - Consider whether content reflects system state

2. **Naming and Registration**
   - Use clear, descriptive names for your plugins
   - Register plugins through the PluginRegistry
   - Implement `generator_name()` to return a unique identifier

3. **Content Generation**
   - Consider the full filesystem context
   - Include proper error handling
   - Use type hints and docstrings
   - Make content generation deterministic when possible

4. **Performance**
   - Cache results when appropriate
   - Minimize filesystem operations
   - Handle large files efficiently

## Plugin Registration

Plugins are automatically registered when the PluginRegistry is initialized:

```python
registry = PluginRegistry(root)
registry.register_generator(MyPlugin())
```

The registry handles:
- Plugin management
- Overlay file initialization
- File handler resolution
