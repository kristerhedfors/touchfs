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

    FS_JSON = '/fs.json'
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
        elif node["type"] == "symlink":
            return len(node.get("content", ""))
        else:  # file
            return len(node.get("content", "").encode('utf-8'))

    def __init__(self, initial_data: Optional[Dict[str, Any]] = None):
        self.logger.info("Initializing Memory filesystem")
        self.fd = 0
        self._root = JsonFS()
        
        if initial_data:
            # Use provided filesystem data
            self._root._data = initial_data
        else:
            # Initialize empty root directory
            self._root._data["/"]["attrs"] = {
                "st_mode": str(S_IFDIR | 0o755)
            }
            
            # Create and initialize fs.json file
            self._root._data[self.FS_JSON] = {
                "type": "file",
                "content": "",
                "attrs": {
                    "st_mode": str(S_IFREG | 0o644)
                }
            }
            self._root.update()  # Update the JSON string
            fs_json_content = str(self._root)
            self._root._data[self.FS_JSON]["content"] = fs_json_content
            # Add fs.json to root directory's children
            self._root._data["/"]["children"]["fs.json"] = self.FS_JSON

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
        if path == self.FS_JSON:
            self._root.update()
            node = self[self.FS_JSON]
        else:
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

    def getxattr(self, path: str, name: str, position: int = 0) -> str:
        node = self[path]
        return node.get("xattrs", {}).get(name, '')

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
        self.fd += 1
        return self.fd

    def read(self, path: str, size: int, offset: int, fh: int) -> bytes:
        if path == self.FS_JSON:
            self._root.update()
            data = str(self._root)
            return data[offset:offset + size].encode('utf-8')

        node = self[path]
        if node:
            # Generate content on first read if it's null
            if node.get("content") is None and node["type"] == "file":
                self.logger.info(f"Generating content for file: {path}")
                try:
                    # Get the entire filesystem structure
                    self._root.update()
                    fs_structure = str(self._root)
                    
                    node["content"] = generate_file_content(path, fs_structure)
                    node["attrs"]["st_size"] = str(len(node["content"].encode('utf-8')))
                except Exception as e:
                    self.logger.error(f"Error generating content for {path}: {e}")
                    node["content"] = ""

            content = node.get("content", "")
            return content[offset:offset + size].encode('utf-8')
        return "".encode('utf-8')

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

    def write(self, path: str, data: bytes, offset: int, fh: int) -> int:
        self.logger.debug(f"Writing to file: {path} at offset: {offset}")
        node = self[path]
        if node:
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
        self.logger.warning(f"Attempted to write to non-existent file: {path}")
        return 0
