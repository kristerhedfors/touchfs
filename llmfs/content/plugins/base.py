"""Base classes and protocols for content generators."""
from abc import ABC, abstractmethod
from typing import Dict, List, Protocol
from stat import S_IFREG
from ...models.filesystem import FileNode

class OverlayFile:
    """Represents a virtual file created by a plugin."""
    def __init__(self, path: str, xattrs: Dict[str, str] = None):
        self.path = path
        self.type = "file"
        self.content = ""
        self.attrs = {
            "st_mode": str(S_IFREG | 0o644),  # Regular file with 644 permissions
            "st_size": "0"
        }
        self.xattrs = xattrs or {}

class ContentGenerator(Protocol):
    """Protocol defining the interface for content generators."""
    
    def get_overlay_files(self) -> List[OverlayFile]:
        """Get list of overlay files this generator provides.
        
        Returns:
            List[OverlayFile]: List of virtual files to overlay on the filesystem
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

class BaseContentGenerator(ABC):
    """Base class for content generators providing common functionality."""
    
    def get_overlay_files(self) -> List[OverlayFile]:
        """Default implementation returns no overlay files."""
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