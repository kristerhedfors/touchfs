# LLMFS - LLM-powered Memory Filesystem

LLMFS is a memory filesystem that can generate filesystem structures using OpenAI's GPT models. It allows you to mount a virtual filesystem and optionally generate its structure based on natural language prompts.

## Features

- In-memory filesystem with JSON serialization
- OpenAI-powered filesystem structure generation
- Content generation for files on first read
- Extended attribute (xattr) support
- Symlink support
- Debug logging capabilities

## Upcoming Features

### Plugin Interface for Dynamic Content Generation

LLMFS will introduce a flexible plugin system that enables custom file content generation at read-time. This powerful feature will allow developers to create specialized file types whose content is dynamically generated based on custom logic.

#### Plugin Design Overview

```python
from typing import Protocol
from llmfs.models.filesystem import FileContent

class ContentGenerator(Protocol):
    def generate(self, path: str, context: dict) -> FileContent:
        """Generate content for a file at read-time.
        
        Args:
            path: File path within the filesystem
            context: Contextual information like filesystem structure,
                    metadata, and related file contents
        
        Returns:
            FileContent: Generated content for the file
        """
        ...

class ExampleGenerator(ContentGenerator):
    def generate(self, path: str, context: dict) -> FileContent:
        # Custom logic to generate file content
        return FileContent(
            content="Generated content based on custom logic",
            metadata={"generator": "example"}
        )
```

#### Key Design Features

1. **Protocol-based Interface**: Clear contract for implementing content generators
2. **Context-aware Generation**: Access to filesystem context for intelligent content creation
3. **Lazy Evaluation**: Content generated only when files are read
4. **Metadata Support**: Ability to attach metadata to generated content
5. **Plugin Registration**: Simple mechanism to register custom generators

#### Example Use Cases

1. **Database Views as Files**:
```python
class SQLViewGenerator(ContentGenerator):
    def generate(self, path: str, context: dict) -> FileContent:
        query_result = self.execute_query(path)
        return FileContent(content=query_result.to_csv())
```

2. **API Response Files**:
```python
class APIResponseGenerator(ContentGenerator):
    def generate(self, path: str, context: dict) -> FileContent:
        endpoint = self.path_to_endpoint(path)
        response = self.api_client.get(endpoint)
        return FileContent(content=response.json())
```

3. **Template-based Files**:
```python
class TemplateGenerator(ContentGenerator):
    def generate(self, path: str, context: dict) -> FileContent:
        template = self.load_template(path)
        return FileContent(
            content=template.render(context=context)
        )
```

## Installation

[Rest of existing README content remains unchanged...]
