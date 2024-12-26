"""File-related operations for the Memory filesystem."""
from typing import Optional
from fuse import FuseOSError
from errno import ENOENT
from stat import S_IFREG

from ...content.generator import generate_file_content
from .base import MemoryBase


class MemoryFileOps:
    """Mixin class that handles file operations: open, read, write, create, truncate, release."""

    def __init__(self, base: MemoryBase):
        self.base = base
        self.logger = base.logger
        self._root = base._root
        self._open_files = base._open_files
        self.fd = 0

    def create(self, path: str, mode: int) -> int:
        self.logger.info(f"Creating file: {path} with mode: {mode}")
        dirname, basename = self.base._split_path(path)

        parent = self.base[dirname]
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

    def open(self, path: str, flags: int) -> int:
        self.logger.debug(f"Open operation started - path: {path}")
        node = self.base[path]
        if node and node["type"] == "file":
            content = node.get("content", "")

            # Generate content if missing or if there's a generator
            if not content or ("xattrs" in node and "generator" in node["xattrs"]):
                self.logger.info(f"Generating content for: {path}")
                try:
                    self._root.update()
                    # Create a deep copy of fs_structure to prevent modifying original
                    fs_structure = {}
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
                    fs_structure['_plugin_registry'] = self.base._plugin_registry
                    content = generate_file_content(path, fs_structure)
                    node["content"] = content
                    node["attrs"]["st_size"] = str(len(content.encode('utf-8')))
                    self._root.update()
                except Exception as e:
                    self.logger.error(f"Content generation failed: {str(e)}", exc_info=True)
                    node["content"] = ""

            self.fd += 1
            self._open_files[self.fd] = {"path": path, "node": node}
            return self.fd

        raise FuseOSError(ENOENT)

    def read(self, path: str, size: int, offset: int, fh: int) -> bytes:
        self.logger.debug(f"Read operation started - path: {path}, size: {size}, offset: {offset}, fh: {fh}")
        if fh in self._open_files:
            node = self._open_files[fh]["node"]
        else:
            node = self.base[path]
            if not node or node["type"] != "file":
                self.logger.warning(f"Cannot read from non-existent or non-file: {path}")
                raise FuseOSError(ENOENT)
            # Auto-open if needed
            if not node.get("content", ""):
                self.open(path, 0)

        content = node.get("content", "")
        self.logger.debug(f"Returning content slice - offset: {offset}, size: {size}, total length: {len(content)}")
        return content[offset:offset + size].encode('utf-8')

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
                node["attrs"]["st_size"] = str(len(new_content.encode('utf-8')))
                self.logger.debug(f"Successfully wrote {len(data)} bytes to {path}")
                return len(data)
            except Exception as e:
                self.logger.error(f"Error writing to file {path}: {str(e)}", exc_info=True)
                raise

        self.logger.warning(f"Cannot write to non-file node at path: {path}")
        raise FuseOSError(ENOENT)

    def truncate(self, path: str, length: int, fh: Optional[int] = None):
        node = self.base[path]
        if node:
            content = node.get("content", "")
            node["content"] = content[:length]
            node["attrs"]["st_size"] = str(length)

    def release(self, path: str, fh: int):
        """Clean up when a file is closed."""
        self.logger.debug(f"Releasing file descriptor {fh} for path: {path}")
        if fh in self._open_files:
            del self._open_files[fh]
        return 0
