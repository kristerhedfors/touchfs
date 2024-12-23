#!/usr/bin/env python3
#
# Copyright(c) 2017 - Krister Hedfors
#
# Modified in 2023-2024 for Python 3 compatibility
#
import logging

from errno import ENOENT
from stat import S_IFDIR, S_IFLNK, S_IFREG
import sys
from sys import argv, exit
import time
import os.path
import io
import copy
import itertools

# For fusepy, do: pip install fusepy
from fuse import FUSE, FuseOSError, Operations, LoggingMixIn
import xml.etree.ElementTree as ET


class MyElementTree(ET.ElementTree):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._str = ''

    def find(self, path):
        if path == '/':
            return self.getroot()
        if len(path) and path[0] == '/':
            path = '.' + path
        return super().find(path)

    def findall(self, path):
        if path == '/':
            return self.getroot()
        if len(path) and path[0] == '/':
            path = '.' + path
        return super().findall(path)

    def update(self):
        s = io.StringIO()
        tree = copy.deepcopy(self)
        #
        # This is necessary as the root element '' is not returned
        # by findall('//*')
        #
        elements = itertools.chain([self.getroot()], tree.findall('//*'))
        for elem in elements:
            if elem.tag == '':
                elem.tag = 'root'
            attrib = elem.attrib
            # Use .items() in Python 3
            for (key, val) in list(attrib.items()):
                attrib[str(key)] = str(val)
        tree.write(s, encoding='unicode')
        del tree
        self._str = s.getvalue()

    def __str__(self):
        return self._str


class Memory(LoggingMixIn, Operations):
    'Example memory filesystem. Supports only one level of files.'

    FS_XML = '/fs.xml'

    def __init__(self):
        self.fd = 0
        t = int(time.time())
        attrib = dict(
            st_mode=(S_IFDIR | 0o755),
            st_ctime=t,
            st_mtime=t,
            st_atime=t,
            st_nlink=2
        )
        self._root = MyElementTree(ET.Element('', attrib=attrib))
        self.create(self.FS_XML, 0o644)
        self[self.FS_XML].attrib['st_size'] = 5

    def __getitem__(self, name):
        print('GETTING name=', name)
        val = self._root.find(name)
        print('GETTING val=', repr(val))
        return val

    def __contains__(self, name):
        for x in self:
            if x == name:
                return True
        return False

    def keys(self):
        for node in self._root.findall('//*'):
            yield node.tag

    def __iter__(self):
        return self.keys()

    def chmod(self, path, mode):
        elem = self[path]
        elem.attrib['st_mode'] = str(int(elem.attrib['st_mode']) & 0o770000 | mode)
        return 0

    def chown(self, path, uid, gid):
        elem = self[path]
        elem.attrib['st_uid'] = str(uid)
        elem.attrib['st_gid'] = str(gid)

    def create(self, path, mode):
        t = int(time.time())
        attrib = dict(
            st_mode=(S_IFREG | mode),
            st_nlink=1,
            st_size=0,
            st_ctime=t,
            st_mtime=t,
            st_atime=t
        )
        self._add_node(path, attrib)
        self.fd += 1
        return self.fd

    def orig_getattr(self, path, fh=None):
        if path == self.FS_XML:
            self._root.update()
            self[self.FS_XML].attrib['st_size'] = str(len(str(self._root)))
        elem = self._root.find(path)
        if elem is None:
            raise FuseOSError(ENOENT)
        print('GETATTR {0} returns {1} {2}'.format(path, elem, elem.attrib))
        return {k: int(v) for k, v in elem.attrib.items() if v.isdigit()}

    def getattr(self, path, fh=None):
        if path == self.FS_XML:
            self._root.update()
            self[self.FS_XML].attrib['st_size'] = str(len(str(self._root)))
        elem = self._root.find(path)
        if elem is None:
            raise FuseOSError(ENOENT)
        print('GETATTR {0} returns {1} {2}'.format(path, elem, elem.attrib))
        # Convert relevant attribs to int
        attr = {}
        for (name, val) in elem.attrib.items():
            # If it’s obviously numeric, convert
            if name.startswith('st_') or name in ('st_uid', 'st_gid'):
                # Attempt to convert
                try:
                    attr[name] = int(val)
                except ValueError:
                    pass
            else:
                # Possibly store as a string or skip
                pass
        return attr

    def getxattr(self, path, name, position=0):
        attrs = self.getattr(path).get('attrs', {})
        try:
            return attrs[name]
        except KeyError:
            return ''

    def listxattr(self, path):
        attrs = self.getattr(path).get('attrs', {})
        return attrs.keys()

    def _split_path(self, path):
        path = os.path.normpath(path)
        dirname = os.path.dirname(path)
        basename = os.path.basename(path)
        return (dirname, basename)

    def _add_node(self, path, attrib=None):
        if attrib is None:
            attrib = {}
        (dirname, basename) = self._split_path(path)
        rootnode = self._root.find(dirname)
        e = ET.SubElement(rootnode, basename)
        t = int(time.time())
        e.attrib.update(
            dict(
                st_mode='0',
                st_nlink='2',
                st_size='33',
                st_ctime=str(t),
                st_mtime=str(t),
                st_atime=str(t)
            )
        )
        for k, v in attrib.items():
            e.attrib[k] = str(v)
        return e

    def mkdir(self, path, mode):
        attrib = dict(st_nlink='3', st_mode=(S_IFDIR | mode))
        self._add_node(path, attrib)

    def open(self, path, flags):
        self.fd += 1
        return self.fd

    def read(self, path, size, offset, fh):
        if path == self.FS_XML:
            return str(self._root)[offset:offset + size]
        elem = self[path]
        text = elem.text or ''
        return text[offset:offset + size]

    def readdir(self, path, fh):
        if len(path) > 1:
            path += '/'
        path += '*'
        logging.debug(path)
        names = [e.tag for e in self._root.findall(path)]
        return ['.', '..'] + names

    def readlink(self, path):
        return self[path].text

    def removexattr(self, path, name):
        attrs = self[path].attrib.get('attrs', {})
        try:
            del attrs[name]
        except KeyError:
            pass  # Should return ENOATTR

    def rename(self, old, new):
        elem = self[old]
        self._root.getroot().remove(elem)
        (basedir, name) = self._split_path(new)
        elem.tag = name
        self[basedir].append(elem)

    def rmdir(self, path):
        elem = self[path]
        if elem is not None:
            # Convert st_mode string to int to check flags
            if int(elem.attrib['st_mode']) & S_IFDIR:
                self._root.getroot().remove(elem)
                # Update link count on root if you want
                root_elem = self['/']
                root_elem.attrib['st_nlink'] = str(int(root_elem.attrib['st_nlink']) - 1)

    def setxattr(self, path, name, value, options, position=0):
        # Ignore options
        attrs = self[path].attrib.setdefault('attrs', {})
        attrs[name] = value

    def statfs(self, path):
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)

    def symlink(self, target, source):
        t = int(time.time())
        attrib = dict(
            st_mode=(S_IFLNK | 0o777),
            st_nlink=1,
            st_size=len(source),
            st_ctime=t,
            st_mtime=t,
            st_atime=t
        )
        elem = self._add_node(target, attrib)
        elem.text = source

    def truncate(self, path, length, fh=None):
        elem = self[path]
        text = elem.text or ''
        elem.text = text[:length]
        elem.attrib['st_size'] = str(length)

    def unlink(self, path):
        elem = self[path]
        if elem is not None:
            if int(elem.attrib['st_mode']) & S_IFREG:
                self._root.getroot().remove(elem)
                # self['/'].attrib['st_nlink'] -= 1

    def utimens(self, path, times=None):
        now = time.time()
        atime, mtime = times if times else (now, now)
        elem = self[path]
        elem.attrib['st_atime'] = str(atime)
        elem.attrib['st_mtime'] = str(mtime)

    def write(self, path, data, offset, fh):
        elem = self[path]
        print('WRITE {0}'.format(elem))
        text = elem.text or ''
        # data is bytes in Py3 if the FUSE wrapper passes bytes
        if isinstance(data, bytes):
            data = data.decode('utf-8', errors='replace')
        elem.text = text[:offset] + data
        elem.attrib['st_size'] = str(len(elem.text))
        return len(data)


if __name__ == '__main__':
    if len(argv) != 2:
        print('usage: %s <mountpoint>' % argv[0])
        exit(1)

    logging.basicConfig(level=logging.DEBUG)
    fuse = FUSE(Memory(), argv[1], foreground=True)
