"""Tree generator that creates a structured, greppable filesystem tree visualization."""
from typing import Dict, List
from ...models.filesystem import FileNode
from .proc import ProcPlugin
from ...config.settings import find_nearest_prompt_file

class TreeGenerator(ProcPlugin):
    """Generator that creates a structured tree visualization in .llmfs directory."""
    
    def generator_name(self) -> str:
        return "tree"
    
    def get_proc_path(self) -> str:
        return "tree"
    
    def _calculate_max_width(self, path: str, structure: Dict[str, FileNode], indent: str = "") -> int:
        """Calculate the maximum width needed for the tree structure."""
        max_width = len(indent)
        
        children = structure[path].children or {}
        names = list(children.keys())
        
        for i, name in enumerate(names):
            child_path = children[name]
            child_node = structure[child_path]
            is_last = i == len(names) - 1
            
            prefix = "└── " if is_last else "├── "
            child_indent = indent + ("    " if is_last else "│   ")
            
            # Calculate width for this line
            line_width = len(indent) + len(prefix) + len(name)
            max_width = max(max_width, line_width)
            
            # Recursively check children if this is a directory
            if child_node.type == "directory":
                child_width = self._calculate_max_width(child_path, structure, child_indent)
                max_width = max(max_width, child_width)
        
        return max_width

    def _build_tree(self, path: str, structure: Dict[str, FileNode], indent: str = "", max_width: int = 0) -> List[str]:
        """Build a tree representation of the filesystem structure."""
        result = []
        
        children = structure[path].children or {}
        names = list(children.keys())
        
        for i, name in enumerate(names):
            child_path = children[name]
            child_node = structure[child_path]
            is_last = i == len(names) - 1
            
            # Choose the appropriate symbols
            prefix = "└── " if is_last else "├── "
            child_indent = indent + ("    " if is_last else "│   ")
            
            # Build the base line
            base_line = f"{indent}{prefix}{name}"
            
            # Add generator info in aligned column
            generator_info = ""
            if child_node.type == "file":
                generator = None
                if child_node.xattrs:
                    if "generator" in child_node.xattrs:
                        generator = child_node.xattrs["generator"]
                    elif child_node.xattrs.get("touched") == "true":
                        generator = "default"
                
                if generator:
                    padding = " " * (max_width - len(base_line) + 2)
                    generator_info = f"{padding}🔄 {generator}"
            
            # Add this node
            result.append(f"{base_line}{generator_info}")
            
            # Recursively add children if this is a directory
            if child_node.type == "directory":
                result.extend(self._build_tree(child_path, structure, child_indent, max_width))
        
        return result
    
    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        """Generate a structured tree visualization of the filesystem."""
        # Add header
        header = """# Filesystem Tree Structure
# Files marked with 🔄 will be generated on next read
#
# File Tree                                    Generator
"""
        # Calculate max width for alignment
        max_width = self._calculate_max_width("/", fs_structure)
        max_width = max(max_width, 50)  # Ensure minimum width for readability
        
        # Start with root directory
        root_node = fs_structure["/"]
        tree_lines = ["/"]  # Add root directory
        tree_lines.extend(self._build_tree("/", fs_structure, max_width=max_width))
        
        return header + "\n".join(tree_lines) + "\n"
