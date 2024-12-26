"""Extended attribute-related operations for the Memory filesystem."""
from fuse import FuseOSError
from errno import ENOENT
from .base import MemoryBase


class MemoryXattrOps:
    """Mixin class that handles getxattr, listxattr, setxattr, removexattr."""

    def __init__(self, base: MemoryBase):
        self.base = base
        self.logger = base.logger
        self._root = base._root

    def getxattr(self, path: str, name: str, position: int = 0) -> bytes:
        node = self.base[path]
        if not node:
            raise FuseOSError(ENOENT)
        value = node.get("xattrs", {}).get(name, "")
        return value.encode('utf-8')

    def listxattr(self, path: str) -> list[str]:
        node = self.base[path]
        return list(node.get("xattrs", {}).keys()) if node else []

    def setxattr(self, path: str, name: str, value: str, options: int, position: int = 0):
        node = self.base[path]
        if node:
            if "xattrs" not in node:
                node["xattrs"] = {}
            node["xattrs"][name] = value

    def removexattr(self, path: str, name: str):
        node = self.base[path]
        if node and "xattrs" in node:
            node["xattrs"].pop(name, None)
