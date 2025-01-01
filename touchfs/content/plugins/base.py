"""Base classes and protocols for content generators."""
from abc import ABC, abstractmethod
from typing import Dict, List, Protocol
from stat import S_IFREG, S_IFLNK
from ...models.filesystem import FileNode

class OverlayNode:
    """Base class for overlay nodes."""
    def __init__(self, path: str, xattrs: Dict[str, str] = None):
        self.path = path
        self.content = ""
        self.xattrs = xattrs or {}

class OverlayFile(OverlayNode):
    """Represents a virtual file created by a plugin."""
    def __init__(self, path: str, xattrs: Dict[str, str] = None):
        super().__init__(path, xattrs)
        self.type = "file"
        self.attrs = {
            "st_mode": str(S_IFREG | 0o644),  # Regular file with 644 permissions
            "st_size": "0"
        }

class OverlaySymlink(OverlayNode):
    """Represents a virtual symlink created by a plugin."""
    def __init__(self, path: str, target: str, xattrs: Dict[str, str] = None):
        super().__init__(path, xattrs)
        self.type = "symlink"
        self.content = target  # For symlinks, content is the target path
        self.attrs = {
            "st_mode": str(S_IFLNK | 0o777),  # Symlink with 777 permissions
        }

class ContentGenerator(Protocol):
    """Protocol defining the interface for content generators."""
    
    def get_overlay_files(self) -> List[OverlayNode]:
        """Get list of overlay files and symlinks this generator provides.
        
        Returns:
            List[OverlayNode]: List of virtual files/symlinks to overlay on the filesystem
        """
        ...
    
    def can_handle(self, path: str, node: FileNode) -> bool:
        """Check if this generator can handle the given file.
        
        Args:
            path: Absolute path of the file
            node: FileNode instance containing file metadata
            
        Returns:
            bool: True if this generator can handle the file
        """
        ...
    
    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        """Generate content for a file.
        
        Args:
            path: Absolute path of the file
            node: FileNode instance containing file metadata
            fs_structure: Complete filesystem structure
            
        Returns:
            str: Generated content for the file
        """
        ...
    
    def get_prompt(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        """Get the generation prompt for this file.
        
        Args:
            path: Absolute path of the file
            node: FileNode instance containing file metadata
            fs_structure: Complete filesystem structure
            
        Returns:
            str: Prompt that would be used to generate content
        """
        ...

class BaseContentGenerator(ABC):
    """Base class for content generators providing common functionality."""
    
    def __init__(self):
        self.base = None  # Will be set by registry
    
    def get_overlay_files(self) -> List[OverlayNode]:
        """Default implementation returns no overlay nodes."""
        return []
    
    def can_handle(self, path: str, node: FileNode) -> bool:
        """Default implementation checks for generator xattr."""
        return node.xattrs is not None and node.xattrs.get("generator") == self.generator_name()
    
    @abstractmethod
    def generator_name(self) -> str:
        """Return the unique name of this generator."""
        pass
    
    @abstractmethod
    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        """Generate content for a file."""
        pass
        
    def get_prompt(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        """Get the generation prompt for this file. Default implementation returns empty string."""
        return ""
