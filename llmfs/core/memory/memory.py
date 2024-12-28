"""Memory class that aggregates all mixin operations into a single FUSE interface."""
from fuse import Operations

from .base import MemoryBase
from .file_ops import MemoryFileOps
from .dir_ops import MemoryDirOps
from .link_ops import MemoryLinkOps
from .xattr_ops import MemoryXattrOps
from .meta_ops import MemoryMetaOps


class Memory(MemoryBase, Operations):
    """Memory filesystem that integrates all operation mixins."""
    
    def __init__(self, initial_data=None, mount_point=None):
        super().__init__(initial_data)
        self.mount_point = mount_point
        self.file_ops = MemoryFileOps(self)
        self.dir_ops = MemoryDirOps(self)
        self.link_ops = MemoryLinkOps(self)
        self.xattr_ops = MemoryXattrOps(self)
        self.meta_ops = MemoryMetaOps(self)

    # File operations delegation
    def create(self, path, mode):
        return self.file_ops.create(path, mode)

    def open(self, path, flags):
        return self.file_ops.open(path, flags)

    def read(self, path, size, offset, fh):
        return self.file_ops.read(path, size, offset, fh)

    def write(self, path, data, offset, fh):
        return self.file_ops.write(path, data, offset, fh)

    def truncate(self, path, length, fh=None):
        return self.file_ops.truncate(path, length, fh)

    def release(self, path, fh):
        return self.file_ops.release(path, fh)

    # Directory operations delegation
    def mkdir(self, path, mode):
        return self.dir_ops.mkdir(path, mode)

    def readdir(self, path, fh):
        return self.dir_ops.readdir(path, fh)

    def rmdir(self, path):
        return self.dir_ops.rmdir(path)

    # Symlink operations delegation
    def readlink(self, path):
        return self.link_ops.readlink(path)

    def symlink(self, target, source):
        return self.link_ops.symlink(target, source)

    # Extended attribute operations delegation
    def getxattr(self, path, name, position=0):
        return self.xattr_ops.getxattr(path, name, position)

    def listxattr(self, path):
        return self.xattr_ops.listxattr(path)

    def setxattr(self, path, name, value, options, position=0):
        return self.xattr_ops.setxattr(path, name, value, options, position)

    def removexattr(self, path, name):
        return self.xattr_ops.removexattr(path, name)

    # Metadata operations delegation
    def chmod(self, path, mode):
        return self.meta_ops.chmod(path, mode)

    def chown(self, path, uid, gid):
        return self.meta_ops.chown(path, uid, gid)

    def getattr(self, path, fh=None):
        return self.meta_ops.getattr(path, fh)

    def rename(self, old, new):
        return self.meta_ops.rename(old, new)

    def statfs(self, path):
        return self.meta_ops.statfs(path)

    def utimens(self, path, times=None):
        return self.meta_ops.utimens(path, times)

    def unlink(self, path):
        return self.meta_ops.unlink(path)
