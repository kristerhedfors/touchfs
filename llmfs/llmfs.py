#!/usr/bin/env python3
#
# llmfs.py
#
# Example memory filesystem backed by JSON.
#
import logging
import json
from errno import ENOENT
from stat import S_IFDIR, S_IFLNK, S_IFREG
import sys
from sys import argv, exit
import time
import os.path
import copy

# For fusepy, do: pip install fusepy
from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

class JsonFS:
    def __init__(self, *args, **kw):
        self._data = {
            "/": {
                "type": "directory",
                "children": {},
                "attrs": {}
            }
        }
        self._str = ''

    def find(self, path):
        if not path or path == '/':
            return self._data["/"]
            
        # Normalize path
        path = os.path.normpath(path)
        return self._data.get(path)

    def findall(self, path):
        if path == '/':
            return [self._data["/"]]
            
        path = os.path.normpath(path)
        if path.endswith('*'):
            base_path = os.path.dirname(path[:-1])
            if base_path in self._data and self._data[base_path]["type"] == "directory":
                return [self._data[os.path.join(base_path, child)] for child in self._data[base_path]["children"]]
        return []

    def update(self):
        """Re-serialize the entire tree to self._str."""
        self._str = json.dumps(self._data, indent=2)

    def __str__(self):
        return self._str

class Memory(LoggingMixIn, Operations):
    """Example memory filesystem using JSON."""

    FS_JSON = '/fs.json'

    def __init__(self):
        self.fd = 0
        t = int(time.time())
        self._root = JsonFS()
        
        # Initialize root directory
        self._root._data["/"]["attrs"] = {
            "st_mode": str(S_IFDIR | 0o755),
            "st_ctime": str(t),
            "st_mtime": str(t),
            "st_atime": str(t),
            "st_nlink": "2"
        }
        
        # Create fs.json file
        self.create(self.FS_JSON, 0o644)
        self._root._data[self.FS_JSON]["attrs"]["st_size"] = "5"

    def __getitem__(self, path):
        return self._root.find(path)

    def _split_path(self, path):
        path = os.path.normpath(path)
        dirname = os.path.dirname(path)
        basename = os.path.basename(path)
        return (dirname, basename)

    def chmod(self, path, mode):
        node = self[path]
        if node:
            old_mode = int(node["attrs"]["st_mode"])
            new_mode = (old_mode & 0o770000) | mode
            node["attrs"]["st_mode"] = str(new_mode)
        return 0

    def chown(self, path, uid, gid):
        node = self[path]
        if node:
            node["attrs"]["st_uid"] = str(uid)
            node["attrs"]["st_gid"] = str(gid)

    def create(self, path, mode):
        t = int(time.time())
        dirname, basename = self._split_path(path)
        
        parent = self[dirname]
        if not parent:
            raise FuseOSError(ENOENT)
            
        self._root._data[path] = {
            "type": "file",
            "content": "",
            "attrs": {
                "st_mode": str(S_IFREG | mode),
                "st_nlink": "1",
                "st_size": "0",
                "st_ctime": str(t),
                "st_mtime": str(t),
                "st_atime": str(t)
            }
        }
        parent["children"][basename] = path
        
        self.fd += 1
        return self.fd

    def getattr(self, path, fh=None):
        if path == self.FS_JSON:
            self._root.update()
            self[self.FS_JSON]["attrs"]["st_size"] = str(len(str(self._root)))

        node = self[path]
        if node is None:
            raise FuseOSError(ENOENT)

        # Convert relevant attribs to int in the returned dict
        attr = {}
        for name, val in node["attrs"].items():
            if name.startswith('st_'):
                try:
                    attr[name] = int(val)
                except ValueError:
                    pass
        return attr

    def getxattr(self, path, name, position=0):
        node = self[path]
        return node.get("xattrs", {}).get(name, '')

    def listxattr(self, path):
        node = self[path]
        return list(node.get("xattrs", {}).keys())

    def mkdir(self, path, mode):
        t = int(time.time())
        dirname, basename = self._split_path(path)
        
        parent = self[dirname]
        if not parent:
            raise FuseOSError(ENOENT)
            
        self._root._data[path] = {
            "type": "directory",
            "children": {},
            "attrs": {
                "st_mode": str(S_IFDIR | mode),
                "st_nlink": "2",
                "st_size": "0",
                "st_ctime": str(t),
                "st_mtime": str(t),
                "st_atime": str(t)
            }
        }
        parent["children"][basename] = path

    def open(self, path, flags):
        self.fd += 1
        return self.fd

    def read(self, path, size, offset, fh):
        if path == self.FS_JSON:
            self._root.update()
            data = str(self._root)
            return data[offset:offset + size].encode('utf-8')

        node = self[path]
        if node:
            content = node.get("content", "")
            return content[offset:offset + size].encode('utf-8')
        return "".encode('utf-8')

    def readdir(self, path, fh):
        node = self[path]
        if node and node["type"] == "directory":
            return ['.', '..'] + list(node["children"].keys())
        return ['.', '..']

    def readlink(self, path):
        node = self[path]
        return node.get("content", "") if node else ""

    def removexattr(self, path, name):
        node = self[path]
        if node and "xattrs" in node:
            node["xattrs"].pop(name, None)

    def rename(self, old, new):
        if old in self._root._data:
            node = self._root._data.pop(old)
            old_parent = self[os.path.dirname(old)]
            old_parent["children"].pop(os.path.basename(old))
            
            self._root._data[new] = node
            new_parent = self[os.path.dirname(new)]
            new_parent["children"][os.path.basename(new)] = new

    def rmdir(self, path):
        node = self[path]
        if node and node["type"] == "directory" and not node["children"]:
            parent = self[os.path.dirname(path)]
            parent["children"].pop(os.path.basename(path))
            del self._root._data[path]

    def setxattr(self, path, name, value, options, position=0):
        node = self[path]
        if node:
            if "xattrs" not in node:
                node["xattrs"] = {}
            node["xattrs"][name] = value

    def statfs(self, path):
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)

    def symlink(self, target, source):
        t = int(time.time())
        dirname, basename = self._split_path(target)
        
        parent = self[dirname]
        if not parent:
            raise FuseOSError(ENOENT)
            
        self._root._data[target] = {
            "type": "symlink",
            "content": source,
            "attrs": {
                "st_mode": str(S_IFLNK | 0o777),
                "st_nlink": "1",
                "st_size": str(len(source)),
                "st_ctime": str(t),
                "st_mtime": str(t),
                "st_atime": str(t)
            }
        }
        parent["children"][basename] = target

    def truncate(self, path, length, fh=None):
        node = self[path]
        if node:
            content = node.get("content", "")
            node["content"] = content[:length]
            node["attrs"]["st_size"] = str(length)

    def unlink(self, path):
        if path in self._root._data:
            parent = self[os.path.dirname(path)]
            parent["children"].pop(os.path.basename(path))
            del self._root._data[path]

    def utimens(self, path, times=None):
        now = time.time()
        atime, mtime = times if times else (now, now)
        node = self[path]
        if node:
            node["attrs"]["st_atime"] = str(atime)
            node["attrs"]["st_mtime"] = str(mtime)

    def write(self, path, data, offset, fh):
        node = self[path]
        if node:
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            content = node.get("content", "")
            if offset > len(content):
                content = content.ljust(offset)
            new_content = content[:offset] + data
            node["content"] = new_content
            node["attrs"]["st_size"] = str(len(new_content.encode('utf-8')))
            return len(data)
        return 0

def main():
    if len(argv) != 2:
        print('usage: llmfs <mountpoint>')
        exit(1)

    logging.basicConfig(level=logging.DEBUG)
    mountpoint = argv[1]
    try:
        fuse = FUSE(Memory(), mountpoint, foreground=True, allow_other=False)
    except RuntimeError as e:
        print(f"Error mounting filesystem: {e}")
        print("Note: You may need to create the mountpoint directory first")
        exit(1)

if __name__ == '__main__':
    main()
