"""File-related operations for the Memory filesystem."""
import os
from typing import Optional
from fuse import FuseOSError
from errno import ENOENT
from stat import S_IFREG

from ...content.generator import generate_file_content
from .base import MemoryBase
from .touch_ops import is_being_touched

class MemoryFileOps:
    """Mixin class that handles file operations: open, read, write, create, truncate, release."""

    def __init__(self, base: MemoryBase):
        self.base = base
        self.logger = base.logger
        self._root = base._root
        self._open_files = base._open_files
        self.fd = 0

    def create(self, path: str, mode: int) -> int:
        """Create a new file and initialize its content.
        
        Args:
            path: Path where to create the file
            mode: File mode/permissions
            initial_content: Optional initial content. If provided, skips content generation.
        """
        self.logger.info(f"Creating file: {path} with mode: {mode}")
        dirname, basename = self.base._split_path(path)

        parent = self.base[dirname]
        if not parent:
            self.logger.error(f"Parent directory not found for path: {path}")
            raise FuseOSError(ENOENT)

        # Create empty file node
        self._root._data[path] = {
            "type": "file",
            "content": "",
            "attrs": {
                "st_mode": str(S_IFREG | mode),
                "st_size": "0"
            },
            "xattrs": {}
        }

        # Check if this is a touch operation
        mount_point = self.base.mount_point if hasattr(self.base, 'mount_point') else '/'
        if is_being_touched(path, mount_point, self.logger):
            self.logger.info(f"Touch operation detected for {path}")
            self._root._data[path]["xattrs"]["needs_generation"] = "true"
        parent["children"][basename] = path
        
        # Return file descriptor
        self.fd += 1
        self._open_files[self.fd] = {"path": path, "node": self._root._data[path]}
        return self.fd

    def open(self, path: str, flags: int) -> int:
        self.logger.info(f"Opening file: {path} with flags: {flags}")
        node = self.base[path]
        if node and node["type"] == "file":
            # Generate/fetch content if needed
            try:
                # Skip if content exists or file isn't tagged for generation
                if node.get("content") or not node.get("xattrs", {}).get("needs_generation"):
                    self.logger.debug(f"Using existing content for {path}")
                    self.fd += 1
                    self._open_files[self.fd] = {"path": path, "node": node}
                    return self.fd

                self.logger.info(f"Generating/fetching content for {path}")
                self._root.update()
                # Create deep copy of fs_structure
                fs_structure = {}
                
                # Copy file structure first
                for k, v in self._root.data.items():
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
                        fs_structure[k] = node_copy
                    else:
                        fs_structure[k] = v
                
                # Add plugin registry last to ensure it's not modified
                fs_structure['_plugin_registry'] = self.base._plugin_registry

                # Generate or fetch content
                content = generate_file_content(path, fs_structure)

                # Store content and update size atomically
                if content:  # Only update if content generation/fetch succeeded
                    content_bytes = content.encode('utf-8')
                    node["content"] = content
                    node["attrs"]["st_size"] = str(len(content_bytes))
                    self._root.update()
                    self.logger.debug(f"Content stored for {path}, size: {len(content_bytes)} bytes")
                else:
                    raise RuntimeError("Content generation/fetch returned empty result")

            except Exception as e:
                self.logger.error(f"Content generation/fetch failed for {path}: {str(e)}", exc_info=True)
                node["content"] = ""
                node["attrs"]["st_size"] = "0"
                self.logger.warning(f"Using empty content for {path} after generation/fetch failure")

            self.fd += 1
            self._open_files[self.fd] = {"path": path, "node": node}
            return self.fd

        raise FuseOSError(ENOENT)

    def read(self, path: str, size: int, offset: int, fh: int) -> bytes:
        self.logger.info(f"Reading from {path} - requested size: {size}, offset: {offset}")
        
        # Get the node, ensuring content is generated/fetched
        if fh in self._open_files:
            node = self._open_files[fh]["node"]
            self.logger.debug(f"Using cached file descriptor {fh}")
        else:
            # If no file handle, force an open to ensure content is generated/fetched
            self.logger.info(f"No file handle found, opening {path}")
            new_fh = self.open(path, 0)
            node = self._open_files[new_fh]["node"]

        # At this point, content should always be available since open() blocks until generation
        content = node.get("content")
        if content is None:
            self.logger.error(f"Content unexpectedly missing for {path} after open")
            raise RuntimeError(f"Content generation failed for {path}")
        content_bytes = content.encode('utf-8')
        total_size = len(content_bytes)
        
        # Ensure we don't read beyond file size
        if offset >= total_size:
            return b''
            
        # Calculate the actual bytes to read
        start_byte = offset
        end_byte = min(offset + size, total_size)
        bytes_to_read = content_bytes[start_byte:end_byte]
        
        self.logger.debug(f"Reading {len(bytes_to_read)} bytes from {path} (offset: {offset}, requested: {size}, total file size: {total_size})")
        return bytes_to_read

    def write(self, path: str, data: bytes, offset: int, fh: int) -> int:
        self.logger.debug(f"Write operation started - path: {path}, offset: {offset}")
        if fh in self._open_files:
            node = self._open_files[fh]["node"]
        else:
            node = self.base[path]
            if not node or node["type"] != "file":
                self.logger.warning(f"Cannot write to non-existent or non-file: {path}")
                raise FuseOSError(ENOENT)
            if not node.get("content", ""):
                self.open(path, 0)

        if node and node["type"] == "file":
            try:
                # Decode data if it's bytes
                if isinstance(data, bytes):
                    data = data.decode('utf-8')
                content = node.get("content", "")
                # Pad with spaces if offset is beyond the current length
                if offset > len(content):
                    content = content.ljust(offset)
                new_content = content[:offset] + data
                node["content"] = new_content
                new_size = len(new_content.encode('utf-8'))
                node["attrs"]["st_size"] = str(new_size)
                self.logger.info(f"Writing {len(data)} bytes to {path} at offset {offset}")
                self.logger.debug(f"File size changed from {len(content.encode('utf-8'))} to {new_size} bytes")
                return len(data)
            except Exception as e:
                self.logger.error(f"Error writing to file {path}: {str(e)}", exc_info=True)
                raise

        self.logger.warning(f"Cannot write to non-file node at path: {path}")
        raise FuseOSError(ENOENT)

    def truncate(self, path: str, length: int, fh: Optional[int] = None):
        self.logger.info(f"Truncating file: {path} to length: {length}")
        node = self.base[path]
        if node:
            content = node.get("content", "")
            old_length = len(content)
            node["content"] = content[:length]
            node["attrs"]["st_size"] = str(length)
            self.logger.debug(f"Truncated file {path} from {old_length} to {length} bytes")

    def release(self, path: str, fh: int):
        """Clean up when a file is closed."""
        self.logger.debug(f"Releasing file descriptor {fh} for path: {path}")
        if fh in self._open_files:
            del self._open_files[fh]
        return 0
