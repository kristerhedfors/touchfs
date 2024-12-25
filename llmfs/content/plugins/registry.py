"""Plugin registry for managing content generators."""
from typing import Dict, Optional
from ...models.filesystem import FileNode
from .base import ContentGenerator
from .default import DefaultGenerator
from .readme import ReadmeGenerator

class PluginRegistry:
    """Registry for content generator plugins."""
    
    _instance = None
    _generators: Dict[str, ContentGenerator] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Register built-in generators
            cls._instance.register_generator(ReadmeGenerator())
            cls._instance.register_generator(DefaultGenerator())
        return cls._instance
    
    def register_generator(self, generator: ContentGenerator) -> None:
        """Register a new content generator.
        
        Args:
            generator: ContentGenerator instance to register
        """
        if hasattr(generator, 'generator_name'):
            name = generator.generator_name()
        else:
            name = generator.__class__.__name__.lower()
        self._generators[name] = generator
    
    def get_generator(self, path: str, node: FileNode) -> Optional[ContentGenerator]:
        """Get the appropriate generator for a file.
        
        Args:
            path: Path of the file to generate content for
            node: FileNode instance containing file metadata
            
        Returns:
            ContentGenerator if one is found that can handle the file, None otherwise
        """
        for generator in self._generators.values():
            if generator.can_handle(path, node):
                return generator
        return None
