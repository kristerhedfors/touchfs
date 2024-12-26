"""Base class and shared utilities for the Memory filesystem implementation."""
import os
import time
import logging
from errno import ENOENT
from stat import S_IFDIR, S_IFLNK, S_IFREG
from typing import Dict, Any, Optional
from fuse import FuseOSError

from ...content.generator import generate_file_content
from ..jsonfs import JsonFS
from ...config.logger import setup_logging


class MemoryBase:
    """Base class containing shared logic and utilities for the Memory filesystem."""

    def __init__(self, initial_data: Optional[Dict[str, Any]] = None):
        """Initialize the base memory filesystem."""
        self.logger = logging.getLogger("llmfs")
        self.logger.info("Initializing Memory filesystem (base).")
        self.fd = 0
        self._root = JsonFS()
        self._open_files: Dict[int, Dict[str, Any]] = {}

        # If there's initial data, use it
        if initial_data:
            self._root._data = initial_data
            # Ensure no 'None' content for files/symlinks
            for node in self._root._data.values():
                if node.get("type") in ["file", "symlink"] and node.get("content") is None:
                    node["content"] = ""
        else:
            # Initialize empty root directory
            self._root._data["/"]["attrs"] = {
                "st_mode": str(S_IFDIR | 0o755)
            }
            self._root.update()

        # Initialize and store plugin registry
        from ...content.plugins.registry import PluginRegistry
        self._plugin_registry = PluginRegistry(root=self._root)

    def __getitem__(self, path: str) -> Optional[Dict[str, Any]]:
        """Retrieve a filesystem node by path."""
        return self._root.find(path)

    def _split_path(self, path: str) -> tuple[str, str]:
        """Split a path into dirname and basename."""
        path = os.path.normpath(path)
        dirname = os.path.dirname(path)
        basename = os.path.basename(path)
        return (dirname, basename)

    def _get_default_times(self) -> Dict[str, str]:
        """Get default time attributes."""
        now = str(int(time.time()))
        return {
            "st_ctime": now,
            "st_mtime": now,
            "st_atime": now
        }

    def _get_nlink(self, node_type: str) -> str:
        """Get appropriate nlink value based on node type."""
        return "2" if node_type == "directory" else "1"

    def _get_size(self, node: Dict[str, Any]) -> int:
        """Calculate size based on node type and content."""
        if node["type"] == "directory":
            return 0

        # If this is a file with a 'generator' xattr, generate content if not already
        if node["type"] == "file" and node.get("xattrs", {}).get("generator"):
            try:
                self._root.update()
                fs_structure = self._root.data

                # If content is empty, generate
                content = node.get("content", "")
                if not content:
                    # We find the path that maps to this node in fs_structure
                    path_for_node = next(path_ for path_, n in fs_structure.items() if n == node)
                    # Create a deep copy of fs_structure to prevent modifying original
                    fs_structure_copy = {}
                    for k, v in fs_structure.items():
                        if isinstance(v, dict):
                            node_copy = {}
                            for nk, nv in v.items():
                                if nk == "attrs":
                                    # Special handling for attrs to match FileSystemEncoder behavior
                                    attrs_copy = nv.copy()
                                    for attr in ["st_ctime", "st_mtime", "st_atime", "st_nlink", "st_size"]:
                                        attrs_copy.pop(attr, None)
                                    node_copy[nk] = attrs_copy
                                elif isinstance(nv, dict):
                                    node_copy[nk] = nv.copy()
                                else:
                                    node_copy[nk] = nv
                            fs_structure_copy[k] = node_copy
                        else:
                            fs_structure_copy[k] = v
                    fs_structure_copy['_plugin_registry'] = self._plugin_registry
                    content = generate_file_content(path_for_node, fs_structure_copy)
                    node["content"] = content

                self._root.update()
            except Exception as e:
                self.logger.error(f"Content generation failed in getattr: {str(e)}", exc_info=True)
                node["content"] = ""

        else:
            # Ensure content is never None for normal files
            if node["type"] == "file" and node.get("content") is None:
                node["content"] = ""

        content = node.get("content", "")
        if node["type"] == "symlink":
            return len(content)
        else:  # file
            return len(content.encode('utf-8'))
