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

## Installation

[Rest of existing README content remains unchanged...]
