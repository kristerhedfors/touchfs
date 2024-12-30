"""Test helper classes and utilities."""
from touchfs.content.plugins.base import BaseContentGenerator
from touchfs.models.filesystem import FileNode

class MockGenerator(BaseContentGenerator):
    """Mock content generator that returns predictable content."""
    
    def generator_name(self) -> str:
        return "mock"
        
    def can_handle(self, path: str, node: FileNode) -> bool:
        """Handle any file that has generate_content xattr."""
        return bool(node.xattrs and node.xattrs.get("generate_content"))
    
    def generate(self, path: str, node: FileNode, fs_structure: dict) -> str:
        """Generate mock content based on the file path."""
        return f"Mock content for {path}"
