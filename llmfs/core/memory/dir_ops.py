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
        self.logger.info(f"Creating directory: {path} with mode: {mode}")
        dirname, basename = self.base._split_path(path)

        parent = self.base[dirname]
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

    def readdir(self, path: str, fh: int) -> list[str]:
        node = self.base[path]
        if node and node["type"] == "directory":
            return ['.', '..'] + list(node["children"].keys())
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
