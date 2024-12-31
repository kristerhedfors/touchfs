"""Base class and shared utilities for the Memory filesystem implementation."""
import os
import time
import base64
import logging
from errno import ENOENT
from stat import S_IFDIR, S_IFLNK, S_IFREG
from typing import Dict, Any, Optional
from fuse import FuseOSError

from ...content.generator import generate_file_content
from ..jsonfs import JsonFS
from ...config.logger import setup_logging
from ...models.filesystem import FileNode, FileAttrs


class MemoryBase:
    """Base class containing shared logic and utilities for the Memory filesystem."""

    def __init__(self, initial_data: Optional[Dict[str, Any]] = None, mount_point: Optional[str] = None):
        """Initialize the base memory filesystem."""
        # Get the existing logger and ensure it's properly initialized for this process
        from ...config.logger import _reinit_logger_after_fork
        _reinit_logger_after_fork()
        self.logger = logging.getLogger("touchfs")
        self.logger.info("Initializing Memory filesystem (base).")
        self.logger.debug(f"Base initialization in PID: {os.getpid()}")
        self.fd = 0
        self._root = JsonFS()
        self._open_files: Dict[int, Dict[str, Any]] = {}
        self.mount_point = mount_point

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
        """Calculate size based on node type and content, triggering generation if needed.
        
        This method is the primary trigger point for content generation, which occurs during
        size calculation (stat operations) and only when:
        1. The file has the generate_content extended attribute set to true
        2. The file is empty (0 bytes)
        3. Or if it's a .touchfs proc file (which always regenerates)
        
        After successful generation:
        - The generate_content xattr is removed (except for .touchfs proc files)
        - The file size is updated to match the generated content
        - The content is stored in the node
        
        On generation failure:
        - Existing content is preserved (not cleared)
        - generate_content xattr is kept (allowing retry)
        - Returns current size or 0 if no content
        
        Args:
            node: Dictionary containing node information
            
        Returns:
            int: Size of the node's content in bytes
        """
        if node["type"] == "directory":
            self.logger.debug("Size calculation for directory: returning 0")
            return 0

        # If this is a file marked for generation, generate content if not already
        if node["type"] == "file" and (node.get("xattrs", {}).get("generator") or node.get("xattrs", {}).get("generate_content")):
            try:
                self._root.update()
                fs_structure = self._root.data

                # Find the path for this node
                path_for_node = next(path_ for path_, n in fs_structure.items() if n == node)
                
                # Generate content only if:
                # 1. File has generate_content xattr or a registered generator
                # 2. File has no content or size is 0
                # 3. Or if it's a .touchfs proc file
                content = node.get("content", "")
                current_size = int(node["attrs"].get("st_size", "0"))
                should_generate = (
                    path_for_node.startswith("/.touchfs/") or
                    (node.get("xattrs", {}).get("generate_content") and (not content or current_size == 0))
                )

                if should_generate:
                    self.logger.info(f"Generating content for size calculation - path: {path_for_node}")
                    
                    # Check for plugin first
                    generator = None
                    if "generator" in node.get("xattrs", {}):
                        # Convert dict to FileNode for plugin system
                        file_node = FileNode(
                            type=node["type"],
                            content=node.get("content", ""),
                            attrs=FileAttrs(**node["attrs"]),
                            xattrs=node.get("xattrs", {})
                        )
                        generator = self._plugin_registry.get_generator(path_for_node, file_node)
                    
                    if generator:
                        # Use plugin to generate content
                        self.logger.debug(f"Using plugin {generator.generator_name()} for {path_for_node}")
                        content = generator.generate(path_for_node, file_node, fs_structure)
                    else:
                        # Fallback to default content generation
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
                    if content:
                        # Update both the copy and original node
                        node["content"] = content
                        original_node = fs_structure[path_for_node]
                        original_node["content"] = content
                        
                        # Remove generate_content xattr after successful generation
                        # (except for .touchfs proc files which always regenerate)
                        if not path_for_node.startswith("/.touchfs/"):
                            # Update both copy and original
                            for target_node in [node, original_node]:
                                if "xattrs" in target_node and "generate_content" in target_node["xattrs"]:
                                    del target_node["xattrs"]["generate_content"]
                                    if not target_node["xattrs"]:  # Remove empty xattrs dict
                                        del target_node["xattrs"]
                        
                        # Ensure changes are persisted
                        self._root._data[path_for_node] = original_node
                        self._root.update()
                        self.logger.debug(f"Updated content for {path_for_node} (type: {'binary' if isinstance(content, bytes) else 'text'})")
            except Exception as e:
                self.logger.error(f"Content generation failed during size calculation: {str(e)}")
                # On failure:
                # 1. Keep existing content (don't clear it)
                # 2. Keep generate_content xattr (so it can try again)
                # 3. Return current size or 0 if no content
                content = node.get("content", "")
                self.logger.warning("Using existing content after generation failure")
                return len(content.encode('utf-8')) if content else 0

        else:
            # Ensure content is never None for normal files
            if node["type"] == "file" and node.get("content") is None:
                node["content"] = ""

        content = node.get("content", "")
        if node["type"] == "symlink":
            size = len(content)
            self.logger.debug(f"Size calculation for symlink: {size} bytes")
            return size
        else:  # file
            # Handle binary vs text content
            if isinstance(content, bytes):
                size = len(content)
                self.logger.debug(f"Size calculation for binary file: {size} bytes")
                return size
            else:
                # Regular text content
                size = len(content.encode('utf-8'))
                self.logger.debug(f"Size calculation for text file: {size} bytes")
                return size
