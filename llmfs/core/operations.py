"""FUSE operations implementation."""
import os
import time
from errno import ENOENT
from stat import S_IFDIR, S_IFLNK, S_IFREG
from typing import Dict, Any, Optional
from fuse import FuseOSError, Operations, LoggingMixIn

from ..content.generator import generate_file_content
from .jsonfs import JsonFS
from ..config.logger import setup_logging

class Memory(LoggingMixIn, Operations):
    """Memory filesystem implementation using FUSE.
    
    This class implements the FUSE operations interface to provide
    a virtual filesystem that stores its data in memory.
    """

    use_ns = True  # Enable nanosecond time handling
    logger = setup_logging()

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
        
        # Ensure content is never None
        content = node.get("content")
        if content is None:
            content = ""
            node["content"] = content
            
        if node["type"] == "symlink":
            return len(content)
        else:  # file
            return len(content.encode('utf-8'))

    def __init__(self, initial_data: Optional[Dict[str, Any]] = None):
        self.logger.info("Initializing Memory filesystem")
        self.fd = 0
        self._root = JsonFS()
        self._open_files = {}  # Track open file descriptors
        
        if initial_data:
            # Use provided filesystem data and ensure content is initialized
            self._root._data = initial_data
            # Initialize any None content values to empty string
            for node in self._root._data.values():
                if node.get("type") in ["file", "symlink"] and node.get("content") is None:
                    node["content"] = ""
        else:
            # Initialize empty root directory
            self._root._data["/"]["attrs"] = {
                "st_mode": str(S_IFDIR | 0o755)
            }
            self._root.update()  # Update the JSON string

    def __getitem__(self, path: str) -> Optional[Dict[str, Any]]:
        return self._root.find(path)

    def _split_path(self, path: str) -> tuple[str, str]:
        path = os.path.normpath(path)
        dirname = os.path.dirname(path)
        basename = os.path.basename(path)
        return (dirname, basename)

    def chmod(self, path: str, mode: int) -> int:
        node = self[path]
        if node:
            old_mode = int(node["attrs"]["st_mode"])
            new_mode = (old_mode & 0o770000) | mode
            node["attrs"]["st_mode"] = str(new_mode)
        return 0

    def chown(self, path: str, uid: int, gid: int):
        node = self[path]
        if node:
            node["attrs"]["st_uid"] = str(uid)
            node["attrs"]["st_gid"] = str(gid)

    def create(self, path: str, mode: int) -> int:
        self.logger.info(f"Creating file: {path} with mode: {mode}")
        dirname, basename = self._split_path(path)
        
        parent = self[dirname]
        if not parent:
            self.logger.error(f"Parent directory not found for path: {path}")
            raise FuseOSError(ENOENT)
            
        self._root._data[path] = {
            "type": "file",
            "content": "",
            "attrs": {
                "st_mode": str(S_IFREG | mode)
            }
        }
        parent["children"][basename] = path
        
        self.fd += 1
        return self.fd

    def getattr(self, path: str, fh: Optional[int] = None) -> Dict[str, int]:
        node = self[path]
            
        if node is None:
            raise FuseOSError(ENOENT)

        # Start with base attributes
        attr = {}
        for name, val in node["attrs"].items():
            if name.startswith('st_'):
                try:
                    attr[name] = int(val)
                except ValueError:
                    pass

        # Add time attributes if not present
        times = self._get_default_times()
        for time_attr in ["st_ctime", "st_mtime", "st_atime"]:
            if time_attr not in attr:
                attr[time_attr] = int(times[time_attr])

        # Add nlink if not present
        if "st_nlink" not in attr:
            attr["st_nlink"] = int(self._get_nlink(node["type"]))

        # Calculate size
        attr["st_size"] = self._get_size(node)

        return attr

    def getxattr(self, path: str, name: str, position: int = 0) -> bytes:
        node = self[path]
        if not node:
            raise FuseOSError(ENOENT)
        value = node.get("xattrs", {}).get(name, "")
        return value.encode('utf-8')

    def listxattr(self, path: str) -> list[str]:
        node = self[path]
        return list(node.get("xattrs", {}).keys())

    def mkdir(self, path: str, mode: int):
        self.logger.info(f"Creating directory: {path} with mode: {mode}")
        dirname, basename = self._split_path(path)
        
        parent = self[dirname]
        if not parent:
            self.logger.error(f"Parent directory not found for path: {path}")
            raise FuseOSError(ENOENT)
            
        self._root._data[path] = {
            "type": "directory",
            "children": {},
            "attrs": {
                "st_mode": str(S_IFDIR | mode)
            }
        }
        parent["children"][basename] = path

    def open(self, path: str, flags: int) -> int:
        self.logger.debug(f"Open operation started - path: {path}")
        node = self[path]
        if node and node["type"] == "file":
            content = node.get("content", "")
            
            # Generate content if needed
            if content == "":
                self.logger.info(f"Generating content for: {path}")
                try:
                    # First update to ensure consistent state
                    self._root.update()
                    fs_structure = self._root.data
                    
                    # Generate and set content
                    content = generate_file_content(path, fs_structure)
                    node["content"] = content
                    node["attrs"]["st_size"] = str(len(content.encode('utf-8')))
                    
                    # Update again to persist changes
                    self._root.update()
                except Exception as e:
                    self.logger.error(f"Content generation failed: {str(e)}", exc_info=True)
                    content = ""
                    node["content"] = content
            
            # Track the open file
            self.fd += 1
            self._open_files[self.fd] = {"path": path, "node": node}
            return self.fd
        
        raise FuseOSError(ENOENT)

    def read(self, path: str, size: int, offset: int, fh: int) -> bytes:
        self.logger.debug(f"Read operation started - path: {path}, size: {size}, offset: {offset}, fh: {fh}")
        
        # First try to use tracked file descriptor
        if fh in self._open_files:
            node = self._open_files[fh]["node"]
        else:
            # Fallback to path-based access
            node = self[path]
            if not node:
                self.logger.warning(f"Node not found for path: {path}")
                raise FuseOSError(ENOENT)
            if node["type"] != "file":
                self.logger.warning(f"Not a file: {path}")
                raise FuseOSError(ENOENT)
            # Auto-open if needed
            if node.get("content", "") == "":
                self.open(path, 0)  # This will generate content if needed
            
        if node and node["type"] == "file":
            content = node.get("content", "")
            self.logger.debug(f"Returning content slice - offset: {offset}, size: {size}, total content length: {len(content)}")
            return content[offset:offset + size].encode('utf-8')
            
        self.logger.warning(f"Invalid node state for path: {path}")
        raise FuseOSError(ENOENT)

    def readdir(self, path: str, fh: int) -> list[str]:
        node = self[path]
        if node and node["type"] == "directory":
            return ['.', '..'] + list(node["children"].keys())
        return ['.', '..']

    def readlink(self, path: str) -> str:
        node = self[path]
        return node.get("content", "") if node else ""

    def removexattr(self, path: str, name: str):
        node = self[path]
        if node and "xattrs" in node:
            node["xattrs"].pop(name, None)

    def rename(self, old: str, new: str):
        if old in self._root._data:
            node = self._root._data.pop(old)
            old_parent = self[os.path.dirname(old)]
            old_parent["children"].pop(os.path.basename(old))
            
            self._root._data[new] = node
            new_parent = self[os.path.dirname(new)]
            new_parent["children"][os.path.basename(new)] = new

    def rmdir(self, path: str):
        self.logger.info(f"Removing directory: {path}")
        node = self[path]
        if node and node["type"] == "directory":
            if node["children"]:
                self.logger.warning(f"Cannot remove non-empty directory: {path}")
                return
            try:
                parent = self[os.path.dirname(path)]
                parent["children"].pop(os.path.basename(path))
                del self._root._data[path]
                self.logger.debug(f"Successfully removed directory: {path}")
            except Exception as e:
                self.logger.error(f"Error removing directory {path}: {str(e)}", exc_info=True)
                raise
        else:
            self.logger.warning(f"Attempted to remove non-existent directory: {path}")

    def setxattr(self, path: str, name: str, value: str, options: int, position: int = 0):
        node = self[path]
        if node:
            if "xattrs" not in node:
                node["xattrs"] = {}
            node["xattrs"][name] = value

    def statfs(self, path: str) -> Dict[str, int]:
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)

    def symlink(self, target: str, source: str):
        dirname, basename = self._split_path(target)
        
        parent = self[dirname]
        if not parent:
            raise FuseOSError(ENOENT)
            
        self._root._data[target] = {
            "type": "symlink",
            "content": source,
            "attrs": {
                "st_mode": str(S_IFLNK | 0o777)
            }
        }
        parent["children"][basename] = target

    def truncate(self, path: str, length: int, fh: Optional[int] = None):
        node = self[path]
        if node:
            content = node.get("content", "")
            node["content"] = content[:length]
            node["attrs"]["st_size"] = str(length)

    def unlink(self, path: str):
        self.logger.info(f"Removing file: {path}")
        if path in self._root._data:
            try:
                parent = self[os.path.dirname(path)]
                parent["children"].pop(os.path.basename(path))
                del self._root._data[path]
                self.logger.debug(f"Successfully removed file: {path}")
            except Exception as e:
                self.logger.error(f"Error removing file {path}: {str(e)}", exc_info=True)
                raise
        else:
            self.logger.warning(f"Attempted to remove non-existent file: {path}")

    def utimens(self, path: str, times: Optional[tuple[float, float]] = None):
        now = time.time()
        atime, mtime = times if times else (now, now)
        node = self[path]
        if node:
            node["attrs"]["st_atime"] = str(atime)
            node["attrs"]["st_mtime"] = str(mtime)

    def release(self, path: str, fh: int):
        """Clean up when a file is closed."""
        self.logger.debug(f"Releasing file descriptor {fh} for path: {path}")
        if fh in self._open_files:
            del self._open_files[fh]
        return 0

    def write(self, path: str, data: bytes, offset: int, fh: int) -> int:
        self.logger.debug(f"Writing to file: {path} at offset: {offset}")
        
        # First try to use tracked file descriptor
        if fh in self._open_files:
            node = self._open_files[fh]["node"]
        else:
            # Fallback to path-based access
            node = self[path]
            if not node:
                self.logger.warning(f"Node not found for path: {path}")
                raise FuseOSError(ENOENT)
            if node["type"] != "file":
                self.logger.warning(f"Not a file: {path}")
                raise FuseOSError(ENOENT)
            # Auto-open if needed
            if node.get("content", "") == "":
                self.open(path, 0)  # This will generate content if needed
                
        if node and node["type"] == "file":
            try:
                if isinstance(data, bytes):
                    data = data.decode('utf-8')
                content = node.get("content", "")
                if offset > len(content):
                    content = content.ljust(offset)
                new_content = content[:offset] + data
                node["content"] = new_content
                node["attrs"]["st_size"] = str(len(new_content.encode('utf-8')))
                self.logger.debug(f"Successfully wrote {len(data)} bytes to {path}")
                return len(data)
            except Exception as e:
                self.logger.error(f"Error writing to file {path}: {str(e)}", exc_info=True)
                raise
                
        self.logger.warning(f"Node not found for path: {path}")
        raise FuseOSError(ENOENT)
