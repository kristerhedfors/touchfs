"""Directory-related operations for the Memory filesystem."""
from fuse import FuseOSError
from errno import ENOENT
from stat import S_IFDIR

from .base import MemoryBase


class MemoryDirOps:
    """Mixin class that handles directory operations: mkdir, readdir, rmdir."""

    def __init__(self, base: MemoryBase):
        self.base = base
        self.logger = base.logger
        self._root = base._root

    def mkdir(self, path: str, mode: int):
        self.logger.info(f"Creating directory: {path} with mode: {mode:o}")
        dirname, basename = self.base._split_path(path)
        self.logger.debug(f"Split path - dirname: {dirname}, basename: {basename}")

        parent = self.base[dirname]
        if not parent:
            self.logger.error(f"Parent directory not found for path: {path}")
            raise FuseOSError(ENOENT)
        
        self.logger.debug(f"Found parent directory: {dirname}")
        self._root._data[path] = {
            "type": "directory",
            "children": {},
            "attrs": {
                "st_mode": str(S_IFDIR | mode)
            }
        }
        parent["children"][basename] = path
        self.logger.debug(f"Successfully created directory {path} in parent {dirname}")

    def readdir(self, path: str, fh: int) -> list[str]:
        self.logger.info(f"Reading directory contents: {path}")
        node = self.base[path]
        if node and node["type"] == "directory":
            entries = ['.', '..'] + list(node["children"].keys())
            self.logger.debug(f"Directory {path} contains {len(entries)-2} entries (excluding . and ..)")
            return entries
        self.logger.warning(f"Reading empty or non-directory: {path}")
        return ['.', '..']

    def rmdir(self, path: str):
        self.logger.info(f"Removing directory: {path}")
        node = self.base[path]
        if node and node["type"] == "directory":
            if node["children"]:
                self.logger.warning(f"Cannot remove non-empty directory: {path}")
                return
            try:
                parent = self.base[self.base._split_path(path)[0]]
                parent["children"].pop(self.base._split_path(path)[1])
                del self._root._data[path]
                self.logger.debug(f"Successfully removed directory: {path}")
            except Exception as e:
                self.logger.error(f"Error removing directory {path}: {str(e)}", exc_info=True)
                raise
        else:
            self.logger.warning(f"Attempted to remove non-existent or non-directory: {path}")
