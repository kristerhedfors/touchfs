"""JSON-based filesystem implementation."""
import json
import os
from typing import Dict, List, Optional, Any

class FileSystemEncoder(json.JSONEncoder):
    """Custom JSON encoder that excludes time, nlinks, and size attributes."""
    def default(self, obj):
        if isinstance(obj, dict) and "attrs" in obj:
            attrs = obj["attrs"].copy()
            # Remove time, nlinks, and size attributes if they exist
            for attr in ["st_ctime", "st_mtime", "st_atime", "st_nlink", "st_size"]:
                attrs.pop(attr, None)
            
            result = obj.copy()
            result["attrs"] = attrs
            
            # Handle bytes content
            if "content" in result and isinstance(result["content"], bytes):
                try:
                    result["content"] = result["content"].decode('utf-8')
                except UnicodeDecodeError:
                    result["content"] = ""  # Reset content if it can't be decoded
            
            return result
        elif isinstance(obj, bytes):
            try:
                return obj.decode('utf-8')
            except UnicodeDecodeError:
                return ""  # Return empty string if bytes can't be decoded
        return super().default(obj)

class JsonFS:
    """JSON-based filesystem implementation.
    
    This class manages the in-memory representation of the filesystem
    and handles serialization to JSON.
    """
    
    def __init__(self):
        """Initialize an empty filesystem with root directory."""
        self._data = {
            "/": {
                "type": "directory",
                "children": {},
                "attrs": {}
            }
        }
        self._str = ''

    def find(self, path: str) -> Optional[Dict[str, Any]]:
        """Find a node in the filesystem by path.
        
        Args:
            path: Absolute path to find
            
        Returns:
            Dict representing the node if found, None otherwise
        """
        if not path or path == '/':
            return self._data["/"]
            
        # Normalize path
        path = os.path.normpath(path)
        return self._data.get(path)

    def findall(self, path: str) -> List[Dict[str, Any]]:
        """Find all nodes matching a path pattern.
        
        Args:
            path: Path pattern to match (supports * wildcard)
            
        Returns:
            List of matching node dictionaries
        """
        if path == '/':
            return [self._data["/"]]
            
        path = os.path.normpath(path)
        if path.endswith('*'):
            base_path = os.path.dirname(path[:-1])
            if base_path in self._data and self._data[base_path]["type"] == "directory":
                return [self._data[os.path.join(base_path, child)] 
                       for child in self._data[base_path]["children"]]
        return []

    def update(self):
        """Re-serialize the entire tree to JSON string and return it."""
        self._str = json.dumps(self._data, indent=2, cls=FileSystemEncoder)
        return self._str  # Return for immediate use

    def __str__(self) -> str:
        """Return the JSON string representation of the filesystem."""
        if not self._str:  # Ensure we have a current serialization
            self.update()
        return self._str

    @property
    def data(self) -> Dict[str, Any]:
        """Get the raw filesystem data dictionary."""
        return self._data
