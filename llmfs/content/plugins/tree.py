"""Tree generator that creates a structured, greppable filesystem tree visualization."""
from typing import Dict, List
from ...models.filesystem import FileNode
from .proc import ProcPlugin

class TreeGenerator(ProcPlugin):
    """Generator that creates a structured tree visualization in .llmfs directory."""
    
    def generator_name(self) -> str:
        return "tree"
    
    def get_proc_path(self) -> str:
        return "tree"
    
    def _build_tree(self, path: str, structure: Dict[str, FileNode], indent: str = "") -> List[str]:
        """Build a tree representation of the filesystem structure."""
        result = []
        
        children = structure[path].children or {}
        sorted_names = sorted(children.keys())
        
        for i, name in enumerate(sorted_names):
            child_path = children[name]
            child_node = structure[child_path]
            is_last = i == len(sorted_names) - 1
            
            # Choose the appropriate symbols
            prefix = "└── " if is_last else "├── "
            child_indent = indent + ("    " if is_last else "│   ")
            
            # Determine generator info
            generator = child_node.xattrs.get("generator", "default") if child_node.xattrs else "default"
            generator_info = f" [generator:{generator}]"
            
            # Add this node with generation status
            result.append(f"{indent}{prefix}{name}{generator_info}")
            
            # Recursively add children if this is a directory
            if child_node.type == "directory":
                result.extend(self._build_tree(child_path, structure, child_indent))
        
        return result
    
    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        """Generate a structured tree visualization of the filesystem."""
        tree_lines = self._build_tree("/", fs_structure)
        
        # Add header
        header = """# Filesystem Tree Structure
# Files are marked with [generator:name] to indicate which plugin generates their content
"""
        return header + "\n".join(tree_lines)
