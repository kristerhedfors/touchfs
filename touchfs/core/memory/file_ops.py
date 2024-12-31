"""File-related operations for the Memory filesystem."""
import os
from typing import Optional
from fuse import FuseOSError
from errno import ENOENT
from stat import S_IFREG

import psutil
from ...content.generator import generate_file_content
from .base import MemoryBase
from .touch_ops import is_being_touched, find_touch_processes

class MemoryFileOps:
    """Mixin class that handles file operations: open, read, write, create, truncate, release."""

    def __init__(self, base: MemoryBase):
        self.base = base
        self.logger = base.logger
        self._root = base._root
        self._open_files = base._open_files
        self.fd = 0

    def create(self, path: str, mode: int) -> int:
        """Create a new file and handle content generation marking.
        
        When a file is created via the touch command, it is automatically marked for content
        generation by setting the generate_content extended attribute. The file is created empty
        (0 bytes) and content will be generated during the first size calculation (stat operation).
        
        This behavior ensures:
        1. Safe content generation - only empty files are eligible
        2. Predictable triggering - generation occurs during size calculation
        3. No accidental overwrites - existing content is never modified
        
        Args:
            path: Path where to create the file
            mode: File mode/permissions
            
        Returns:
            File descriptor number
            
        Raises:
            FuseOSError: If parent directory doesn't exist
        """
        self.logger.info(f"Creating file: {path} with mode: {mode}")
        
        # Check if this is a touch operation
        mount_point = self.base.mount_point if hasattr(self.base, 'mount_point') else '/'
        if is_being_touched(path, mount_point, self.logger):
            self.logger.info(f"Touch operation detected for {path}")
            # Get the touch process's cwd relative to mount point
            with find_touch_processes() as touch_procs:
                for touch_proc, _ in touch_procs:
                    try:
                        touch_cwd = touch_proc.cwd()
                        # Convert touch_cwd to FUSE path if it's under mount point
                        if touch_cwd.startswith(mount_point):
                            # Convert touch_cwd to FUSE path
                            rel_path = os.path.relpath(touch_cwd, mount_point)
                            fuse_dir = "/" + rel_path if rel_path != "." else "/"
                            self.logger.debug(f"Touch operation in directory: {fuse_dir}")
                            
                            # Check if directory exists and is actually a directory
                            if fuse_dir != "/":
                                dir_node = self.base[fuse_dir]
                                if not dir_node or dir_node["type"] != "directory":
                                    self.logger.error(f"Directory {fuse_dir} does not exist")
                                    raise FuseOSError(ENOENT)
                            
                            # Update path to preserve directory structure
                            path = os.path.normpath(os.path.join(fuse_dir, os.path.basename(path)))
                            self.logger.debug(f"Updated path to: {path}")
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
        
        dirname, basename = self.base._split_path(path)
        parent = self.base[dirname]
        if not parent or parent["type"] != "directory":
            self.logger.error(f"Parent directory not found or not a directory: {dirname}")
            raise FuseOSError(ENOENT)

        # Create empty file node with basic attributes
        node = {
            "type": "file",
            "content": "",
            "attrs": {
                "st_mode": str(S_IFREG | mode),
                "st_size": "0"
            }
        }
        
        # Mark for generation if it's a touch operation creating an empty file
        if is_being_touched(path, mount_point, self.logger):
            node["xattrs"] = {
                "generate_content": b"true"
            }
            
        self._root._data[path] = node
        parent["children"][basename] = path
        
        # Return file descriptor
        self.fd += 1
        self._open_files[self.fd] = {"path": path, "node": self._root._data[path]}
        return self.fd

    def open(self, path: str, flags: int) -> int:
        """Open a file and handle content generation if needed.
        
        Content generation is triggered during size calculation (stat operations) and only occurs when:
        1. The file has the generate_content extended attribute set to true
        2. The file is empty (0 bytes)
        3. The file isn't already being processed
        
        This ensures safety by never overwriting existing content. Files are typically marked
        either during initial filesystem creation or via the touch command (which sets the
        generate_content xattr under the hood).
        
        Args:
            path: Path to the file to open
            flags: File open flags
            
        Returns:
            File descriptor number
            
        Raises:
            FuseOSError: If file doesn't exist
        """
        self.logger.info(f"Opening file: {path} with flags: {flags}")
        node = self.base[path]
        if node and node["type"] == "file":
            # Generate/fetch content if needed
            try:
                # Only generate content if:
                # 1. File has generate_content xattr
                # 2. File has no content or size is 0
                # 3. File isn't already being processed
                if (node.get("xattrs", {}).get("generate_content") and 
                    (not node.get("content") or int(node["attrs"].get("st_size", "0")) == 0)):
                    self.logger.info(f"Generating/fetching content for {path}")
                else:
                    self.logger.debug(f"Using existing content (skipping generation) for {path}")
                    self.fd += 1
                    self._open_files[self.fd] = {"path": path, "node": node}
                    return self.fd

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
                    # Handle binary vs text content
                    if isinstance(content, bytes):
                        content_size = len(content)
                    else:
                        content_size = len(content.encode('utf-8'))
                    node["content"] = content
                    node["attrs"]["st_size"] = str(content_size)
                    # Remove generate_content xattr after successful generation
                    if "xattrs" in node and "generate_content" in node["xattrs"]:
                        del node["xattrs"]["generate_content"]
                        if not node["xattrs"]:  # Remove empty xattrs dict
                            del node["xattrs"]
                    self._root.update()
                    self.logger.debug(f"Content stored for {path}, size: {content_size} bytes, type: {'binary' if isinstance(content, bytes) else 'text'}")
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

        # Check if content needs to be generated using same conditions as open()
        if (node.get("xattrs", {}).get("generate_content") and 
            (not node.get("content") or int(node["attrs"].get("st_size", "0")) == 0)):
            self.logger.info(f"Content generation needed for {path} during read")
            # Force an open to trigger generation
            new_fh = self.open(path, 0)
            node = self._open_files[new_fh]["node"]
            
        content = node.get("content")
        if content is None:
            self.logger.error(f"Content unexpectedly missing for {path} after open/generation")
            raise RuntimeError(f"Content generation failed for {path}")

        # Handle binary vs text content
        if isinstance(content, bytes):
            content_bytes = content
        else:
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
                # Preserve existing xattrs
                xattrs = node.get("xattrs", {})
                
                content = node.get("content", "")
                
                # Handle binary vs text content
                if isinstance(content, bytes):
                    # For binary content, we need to handle padding and concatenation as bytes
                    if offset > len(content):
                        content = content + b'\0' * (offset - len(content))
                    new_content = content[:offset] + data
                    new_size = len(new_content)
                else:
                    # For text content, decode bytes to string
                    data_str = data.decode('utf-8')
                    if offset > len(content):
                        content = content.ljust(offset)
                    new_content = content[:offset] + data_str
                    new_size = len(new_content.encode('utf-8'))
                
                # Update node with new content while preserving xattrs
                node["content"] = new_content
                node["attrs"]["st_size"] = str(new_size)
                if xattrs:
                    node["xattrs"] = xattrs
                
                # Check if generate_content is set in node's xattrs (could be set after write)
                if node.get("xattrs", {}).get("generate_content"):
                    node["content"] = ""
                    node["attrs"]["st_size"] = "0"
                self.logger.info(f"Writing {len(data)} bytes to {path} at offset {offset}")
                # Log size change appropriately for binary/text content
                old_size = len(content) if isinstance(content, bytes) else len(content.encode('utf-8'))
                self.logger.debug(f"File size changed from {old_size} to {new_size} bytes")
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
            if isinstance(content, bytes):
                old_length = len(content)
                if length > old_length:
                    # Pad with zeros if truncating to larger size
                    node["content"] = content + b'\0' * (length - old_length)
                else:
                    # Truncate to smaller size
                    node["content"] = content[:length]
            else:
                old_length = len(content)
                if length > old_length:
                    # Pad with spaces if truncating to larger size
                    node["content"] = content.ljust(length)
                else:
                    # Truncate to smaller size
                    node["content"] = content[:length]
            node["attrs"]["st_size"] = str(length)
            self.logger.debug(f"Truncated file {path} from {old_length} to {length} bytes")

    def release(self, path: str, fh: int):
        """Clean up when a file is closed."""
        self.logger.debug(f"Releasing file descriptor {fh} for path: {path}")
        if fh in self._open_files:
            del self._open_files[fh]
        return 0
