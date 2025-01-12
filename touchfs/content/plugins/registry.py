"""Plugin registry for managing content generators."""
import os
from typing import Dict, Optional, List
from ...models.filesystem import FileNode
from ... import config
from .base import ContentGenerator, ProcNode
from .default import DefaultGenerator
from .readme import ReadmeGenerator
from .tree import TreeGenerator
from .prompt import PromptPlugin
from .model import ModelPlugin
from .log_symlink import LogSymlinkPlugin
from .cache_control import CacheControlPlugin
from .image import ImageGenerator  # Import from refactored module
from .touch_detector import TouchDetectorPlugin

def _proc_to_node(proc: ProcNode) -> Dict:
    """Convert a ProcNode to a node dictionary."""
    return {
        "type": proc.type,
        "content": proc.content,
        "attrs": proc.attrs,
        "xattrs": proc.xattrs
    }

class PluginRegistry:
    """Registry for content generator plugins."""
    
    def __init__(self, root=None, proc_path=None):
        """Initialize the registry with optional root filesystem and proc path."""
        self._generators: Dict[str, ContentGenerator] = {}
        self._root = root
        self._proc_path = proc_path
        
        # Register built-in generators
        generators = [
            ReadmeGenerator(),
            DefaultGenerator(),
            TreeGenerator(),
            PromptPlugin(),
            ModelPlugin(),
            LogSymlinkPlugin(),
            CacheControlPlugin(),
            ImageGenerator(),
            TouchDetectorPlugin()
        ]
        
        # Set base instance and register each generator
        for generator in generators:
            if hasattr(generator, 'base'):
                # Use the existing root instance instead of creating a new one
                generator.base = self._root
            self.register_generator(generator)
        
        # Initialize proc files if root is provided
        if root:
            self._initialize_proc_files()
    
    def _initialize_proc_files(self) -> None:
        """Initialize proc files from all registered generators."""
        for generator in self._generators.values():
            proc_files = generator.get_proc_files()
            for proc_file in proc_files:
                # Add proc file to filesystem
                dirname = os.path.dirname(proc_file.path)
                basename = os.path.basename(proc_file.path)
                
                # Ensure all parent directories exist
                current_path = "/"
                if dirname != "/":
                    parts = dirname.split("/")[1:]  # Skip empty string before first /
                    for part in parts:
                        current_path = os.path.join(current_path, part)
                        if current_path not in self._root._data:
                            self._root._data[current_path] = {
                                "type": "directory",
                                "children": {},
                                "attrs": {"st_mode": "16877"}  # 755 permissions
                            }
                            parent_dir = os.path.dirname(current_path)
                            if parent_dir != current_path:  # Avoid self-reference for root
                                self._root._data[parent_dir]["children"][part] = current_path
                
                # Add file to filesystem
                self._root._data[proc_file.path] = _proc_to_node(proc_file)
                self._root._data[dirname]["children"][basename] = proc_file.path
    
    def register_generator(self, generator: ContentGenerator) -> None:
        """Register a new content generator.
        
        Args:
            generator: ContentGenerator instance to register
        """
        if hasattr(generator, 'generator_name'):
            name = generator.generator_name()
        else:
            name = generator.__class__.__name__.lower()
            
        # Set base instance if not already set
        if hasattr(generator, 'base') and generator.base is None:
            generator.base = self._root
            
        self._generators[name] = generator
        
        # Initialize proc files for the new generator if we have a root
        if self._root and generator.get_proc_files():
            proc_files = generator.get_proc_files()
            for proc_file in proc_files:
                # Add proc file to filesystem
                dirname = os.path.dirname(proc_file.path)
                basename = os.path.basename(proc_file.path)
                
                # Ensure all parent directories exist
                current_path = "/"
                if dirname != "/":
                    parts = dirname.split("/")[1:]  # Skip empty string before first /
                    for part in parts:
                        current_path = os.path.join(current_path, part)
                        if current_path not in self._root._data:
                            self._root._data[current_path] = {
                                "type": "directory",
                                "children": {},
                                "attrs": {"st_mode": "16877"}  # 755 permissions
                            }
                            parent_dir = os.path.dirname(current_path)
                            if parent_dir != current_path:  # Avoid self-reference for root
                                self._root._data[parent_dir]["children"][part] = current_path
                
                # Add file to filesystem
                self._root._data[proc_file.path] = _proc_to_node(proc_file)
                self._root._data[dirname]["children"][basename] = proc_file.path
    
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
