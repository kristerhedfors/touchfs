"""Metadata and miscellaneous operations for the Memory filesystem."""
import os
import time
from typing import Dict, Optional
from fuse import FuseOSError
from errno import ENOENT
from stat import S_IFDIR, S_IFREG

from .base import MemoryBase


class MemoryMetaOps:
    """Mixin class for metadata operations: chmod, chown, rename, getattr, statfs, utimens, unlink, etc."""

    def __init__(self, base: MemoryBase):
        self.base = base
        self.logger = base.logger
        self._root = base._root

    def chmod(self, path: str, mode: int) -> int:
        node = self.base[path]
        if node:
            old_mode = int(node["attrs"]["st_mode"])
            new_mode = (old_mode & 0o770000) | mode
            node["attrs"]["st_mode"] = str(new_mode)
        return 0

    def chown(self, path: str, uid: int, gid: int):
        node = self.base[path]
        if node:
            node["attrs"]["st_uid"] = str(uid)
            node["attrs"]["st_gid"] = str(gid)

    def rename(self, old: str, new: str):
        if old in self._root._data:
            node = self._root._data.pop(old)
            old_parent = self.base[os.path.dirname(old)]
            if old_parent and "children" in old_parent:
                old_parent["children"].pop(os.path.basename(old), None)

            self._root._data[new] = node
            new_parent = self.base[os.path.dirname(new)]
            if new_parent and "children" in new_parent:
                new_parent["children"][os.path.basename(new)] = new

    def getattr(self, path: str, fh: Optional[int] = None) -> Dict[str, int]:
        node = self.base[path]

        if node is None:
            raise FuseOSError(ENOENT)

        # Base attributes from node
        attr = {}
        for name, val in node["attrs"].items():
            if name.startswith('st_'):
                try:
                    attr[name] = int(val)
                except ValueError:
                    pass

        # Time attributes
        times = self.base._get_default_times()
        for time_attr in ["st_ctime", "st_mtime", "st_atime"]:
            if time_attr not in attr:
                attr[time_attr] = int(times[time_attr])

        # nlink
        if "st_nlink" not in attr:
            attr["st_nlink"] = int(self.base._get_nlink(node["type"]))

        # size
        attr["st_size"] = self.base._get_size(node)

        return attr

    def statfs(self, path: str) -> Dict[str, int]:
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)

    def utimens(self, path: str, times: Optional[tuple[float, float]] = None):
        """Update access and modification times of a file, handling touch operations.
        
        This method is called by the touch command and plays a crucial role in content generation:
        - For empty files, it marks them for generation by setting the generate_content xattr
        - Content will be generated during the next size calculation (stat operation)
        - This is the primary mechanism for marking new files for generation
        
        Args:
            path: Path to the file
            times: Optional tuple of (atime, mtime) timestamps. If None, uses current time.
        """
        self.logger.debug(f"utimens called for {path} with times {times}")
        now = int(times[0] if times else time.time())
        node = self.base[path]
        if node:
            self.logger.debug(f"Found node of type: {node['type']}")
            # Update timestamps
            atime, mtime = times if times else (now, now)
            node["attrs"]["st_atime"] = str(atime)
            node["attrs"]["st_mtime"] = str(mtime)
            
            # Mark empty files as touched unless content generation is disabled
            if node["type"] == "file" and not node.get("content"):
                self.logger.debug(f"Empty file touched: {path}")
                if not os.getenv("TOUCHFS_DISABLE_GENERATION"):
                    self.logger.debug(f"Marking for content generation")
                    if "xattrs" not in node:
                        node["xattrs"] = {}
                    node["xattrs"]["touchfs.generate_content"] = b"true"
                    self.logger.debug(f"Node marked for content generation")
                else:
                    self.logger.debug("Content generation disabled, skipping mark")

    def unlink(self, path: str):
        self.logger.info(f"Removing file: {path}")
        if path in self._root._data:
            try:
                parent = self.base[os.path.dirname(path)]
                parent["children"].pop(os.path.basename(path), None)
                del self._root._data[path]
                self.logger.debug(f"Successfully removed file: {path}")
            except Exception as e:
                self.logger.error(f"Error removing file {path}: {str(e)}", exc_info=True)
                raise
        else:
            self.logger.warning(f"Attempted to remove non-existent file: {path}")
