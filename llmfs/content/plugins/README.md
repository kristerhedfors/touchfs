# LLMFS Plugin System

The LLMFS plugin system provides a flexible way to generate dynamic content for files in the virtual filesystem. This document explains how plugins work and how to create new ones.

## Architecture

The plugin system consists of several key components:

1. **ContentGenerator Protocol** - Defines the interface that all plugins must implement
2. **BaseContentGenerator** - Abstract base class providing common functionality
3. **PluginRegistry** - Manages plugin registration and overlay files
4. **OverlayFile** - Represents virtual files created by plugins

### Core Interfaces

Every plugin must implement these key methods:

```python
def get_overlay_files() -> List[OverlayFile]:
    """Get list of overlay files this generator provides."""
    
def can_handle(self, path: str, node: FileNode) -> bool:
    """Check if this generator can handle the given file."""
    
def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
    """Generate content for a file."""
```

## Creating a Plugin

To create a new plugin:

1. Create a new class that inherits from `BaseContentGenerator`
2. Implement the required methods
3. Register the plugin with `PluginRegistry`

Here's a minimal example:

```python
from .base import BaseContentGenerator

class MyPlugin(BaseContentGenerator):
    def generator_name(self) -> str:
        return "myplugin"
        
    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        return "Generated content for " + path
```

## Real-World Examples

### 1. README Generator

The `ReadmeGenerator` plugin demonstrates how to create filesystem documentation:

```python
class ReadmeGenerator(BaseContentGenerator):
    def get_overlay_files(self) -> List[OverlayFile]:
        """Creates a README in .llmfs directory"""
        overlay = OverlayFile("/.llmfs/README", {"generator": "readme"})
        return [overlay]
    
    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        # Generates a tree visualization of the filesystem
        tree_lines = self._build_tree("/", fs_structure)
        return "\n".join(tree_lines)
```

Key features:
- Creates an overlay file automatically
- Generates dynamic content based on current filesystem state
- Uses custom metadata through xattrs

### 2. Config Plugin

The `ConfigPlugin` handles hierarchical configuration through `.llmfs/config` files:

```python
class ConfigPlugin(BaseContentGenerator):
    def can_handle(self, path: str, node: FileNode) -> bool:
        """Handles .llmfs/config files"""
        return path.endswith("/.llmfs/config") or path == "/config/config"
    
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
- Default configuration at /config/config

### 3. Default Generator

The `DefaultGenerator` shows how to integrate with external APIs (OpenAI):

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

Key features:
- Fallback handler for files without specific generators
- Integrates with external APIs
- Uses structured output parsing
- Includes error handling and logging

## Best Practices

1. **Naming and Registration**
   - Use clear, descriptive names for your plugins
   - Register plugins through the PluginRegistry
   - Implement `generator_name()` to return a unique identifier

2. **Overlay Files**
   - Use overlay files for static virtual files
   - Include appropriate metadata in xattrs
   - Ensure paths don't conflict with other plugins

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
