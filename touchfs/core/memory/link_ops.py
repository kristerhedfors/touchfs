"""Symlink-related operations for the Memory filesystem."""
from fuse import FuseOSError
from errno import ENOENT
from stat import S_IFLNK, S_IFREG
import os

from .base import MemoryBase


class MemoryLinkOps:
    """Mixin class that handles symlink and readlink operations."""

    def __init__(self, base: MemoryBase):
        self.base = base
        self.logger = base.logger
        self._root = base._root

    def readlink(self, path: str) -> str:
        self.logger.info(f"Reading symlink: {path}")
        node = self.base[path]
        if node:
            target = node.get("content", "")
            self.logger.debug(f"Symlink {path} points to: {target}")
            return target
        self.logger.warning(f"Attempted to read non-existent symlink: {path}")
        return ""

    def symlink(self, target: str, source: str):
        self.logger.info(f"Creating symlink: {target} -> {source}")
        dirname, basename = self.base._split_path(target)
        self.logger.debug(f"Split path - dirname: {dirname}, basename: {basename}")

        parent = self.base[dirname]
        if not parent:
            self.logger.error(f"Parent directory not found for symlink: {dirname}")
            raise FuseOSError(ENOENT)

        self._root._data[target] = {
            "type": "symlink",
            "content": source,
            "attrs": {
                "st_mode": str(S_IFLNK | 0o777)
            }
        }
        parent["children"][basename] = target
        self.logger.debug(f"Successfully created symlink {target} pointing to {source}")
