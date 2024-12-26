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
        node = self.base[path]
        return node.get("content", "") if node else ""

    def symlink(self, target: str, source: str):
        dirname, basename = self.base._split_path(target)

        parent = self.base[dirname]
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
