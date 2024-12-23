#!/usr/bin/env python3
#
# pyfs.py
#
# Example memory filesystem backed by an XML ElementTree.
# Original code: (c) 2017 by Krister Hedfors
# Modified for Python 3 + fusepy, ensuring attributes are stored as strings.
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
        """
        Re-serialize the entire tree to self._str.
        Ensures root tag is not empty and ensures all attributes are strings.
        """
        s = io.StringIO()
        tree = copy.deepcopy(self)

        elements = itertools.chain([tree.getroot()], tree.findall('//*'))
        for elem in elements:
            # If the root tag is '', rename it to 'root'
            if elem.tag == '':
                elem.tag = 'root'
            # Make sure all attributes are strings so they can be serialized
            for k, v in list(elem.attrib.items()):
                elem.attrib[k] = str(v)

        tree.write(s, encoding='unicode')
        del tree
        self._str = s.getvalue()

    def __str__(self):
        return self._str


class Memory(LoggingMixIn, Operations):
    """
    Example memory filesystem using an XML ElementTree.
    Supports only one level of files for demonstration.
    """

    FS_XML = '/fs.xml'

    def __init__(self):
        self.fd = 0
        t = int(time.time())
        # Store attributes as strings!
        attrib = dict(
            st_mode=str(S_IFDIR | 0o755),
            st_ctime=str(t),
            st_mtime=str(t),
            st_atime=str(t),
            st_nlink='2'
        )
        self._root = MyElementTree(ET.Element('', attrib=attrib))
        self.create(self.FS_XML, 0o644)
        # st_size also stored as string:
        self[self.FS_XML].attrib['st_size'] = '5'

    def __getitem__(self, name):
        # Debug printing
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

    #
    # FUSE Methods
    #

    def chmod(self, path, mode):
        elem = self[path]
        old_mode = int(elem.attrib['st_mode'])
        new_mode = (old_mode & 0o770000) | mode
        elem.attrib['st_mode'] = str(new_mode)
        return 0

    def chown(self, path, uid, gid):
        elem = self[path]
        elem.attrib['st_uid'] = str(uid)
        elem.attrib['st_gid'] = str(gid)

    def create(self, path, mode):
        """
        Create a file with given mode.
        """
        t = int(time.time())
        attrib = dict(
            st_mode=str(S_IFREG | mode),
            st_nlink='1',
            st_size='0',
            st_ctime=str(t),
            st_mtime=str(t),
            st_atime=str(t)
        )
        self._add_node(path, attrib)
        self.fd += 1
        return self.fd

    def _add_node(self, path, attrib=None):
        if attrib is None:
            attrib = {}
        dirname, basename = self._split_path(path)
        rootnode = self._root.find(dirname)
        e = ET.SubElement(rootnode, basename)
        t = str(int(time.time()))
        e.attrib.update(dict(
            st_mode='0',
            st_nlink='2',
            st_size='0',
            st_ctime=t,
            st_mtime=t,
            st_atime=t
        ))
        for k, v in attrib.items():
            e.attrib[k] = str(v)
        return e

    def _split_path(self, path):
        path = os.path.normpath(path)
        dirname = os.path.dirname(path)
        basename = os.path.basename(path)
        return (dirname, basename)

    def getattr(self, path, fh=None):
        """
        Return a dictionary of stat-style info. Convert stored string attributes to int.
        """
        if path == self.FS_XML:
            # Regenerate the XML, then update fs.xml size
            self._root.update()
            self[self.FS_XML].attrib['st_size'] = str(len(str(self._root)))

        elem = self._root.find(path)
        if elem is None:
            raise FuseOSError(ENOENT)

        print('GETATTR {0} returns {1} {2}'.format(path, elem, elem.attrib))

        # Convert relevant attribs to int in the returned dict
        attr = {}
        for (name, val) in elem.attrib.items():
            if name.startswith('st_'):
                try:
                    attr[name] = int(val)
                except ValueError:
                    pass
        return attr

    def getxattr(self, path, name, position=0):
        # xattrs stored in 'attrs' dict within elem.attrib
        attrs = self[path].attrib.get('attrs', {})
        return attrs.get(name, '')

    def listxattr(self, path):
        attrs = self[path].attrib.get('attrs', {})
        return list(attrs.keys())

    def mkdir(self, path, mode):
        """
        Create a directory with the given mode.
        """
        t = int(time.time())
        attrib = dict(
            st_nlink='3',
            st_mode=str(S_IFDIR | mode),
            st_ctime=str(t),
            st_mtime=str(t),
            st_atime=str(t)
        )
        self._add_node(path, attrib)

    def open(self, path, flags):
        self.fd += 1
        return self.fd

    def read(self, path, size, offset, fh):
        """
        If reading /fs.xml, return the entire serialized XML string.
        Otherwise, return the text stored in the element.
        """
        if path == self.FS_XML:
            # Return the serialized XML from memory
            data = str(self._root)
            return data[offset : offset + size]

        elem = self[path]
        text = elem.text or ''
        return text[offset : offset + size]

    def readdir(self, path, fh):
        """
        Return directory listings: '.' and '..' plus the children of path.
        """
        if len(path) > 1:
            path += '/'
        path += '*'
        logging.debug(path)
        names = [e.tag for e in self._root.findall(path)]
        return ['.', '..'] + names

    def readlink(self, path):
        return self[path].text or ''

    def removexattr(self, path, name):
        attrs = self[path].attrib.get('attrs', {})
        try:
            del attrs[name]
        except KeyError:
            pass

    def rename(self, old, new):
        elem = self[old]
        self._root.getroot().remove(elem)
        (basedir, name) = self._split_path(new)
        elem.tag = name
        self[basedir].append(elem)

    def rmdir(self, path):
        elem = self[path]
        if elem is not None:
            # Check if it's actually a directory
            mode = int(elem.attrib.get('st_mode', '0'))
            if mode & S_IFDIR:
                self._root.getroot().remove(elem)
                # Decrement nlink on root if you want
                root_elem = self['/']
                root_nlink = int(root_elem.attrib['st_nlink'])
                root_elem.attrib['st_nlink'] = str(root_nlink - 1)

    def setxattr(self, path, name, value, options, position=0):
        # Store xattrs in the 'attrs' dict on the element
        attrs = self[path].attrib.setdefault('attrs', {})
        attrs[name] = value

    def statfs(self, path):
        # Return some fixed values
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)

    def symlink(self, target, source):
        """
        Create a symlink named 'target' that points to 'source'.
        """
        t = int(time.time())
        attrib = dict(
            st_mode=str(S_IFLNK | 0o777),
            st_nlink='1',
            st_size=str(len(source)),
            st_ctime=str(t),
            st_mtime=str(t),
            st_atime=str(t)
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
            mode = int(elem.attrib.get('st_mode', '0'))
            if mode & S_IFREG:
                self._root.getroot().remove(elem)

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
        if isinstance(data, bytes):
            # Convert bytes to string
            data = data.decode('utf-8', errors='replace')
        new_text = text[:offset] + data
        elem.text = new_text
        elem.attrib['st_size'] = str(len(new_text))
        return len(data)

    #
    # Helper methods
    #
    def _split_path(self, path):
        path = os.path.normpath(path)
        dirname = os.path.dirname(path)
        basename = os.path.basename(path)
        return (dirname, basename)

    def _add_node(self, path, attrib=None):
        if attrib is None:
            attrib = {}
        dirname, basename = self._split_path(path)
        rootnode = self._root.find(dirname)
        e = ET.SubElement(rootnode, basename)
        t = str(int(time.time()))
        # Initialize some default attributes, as strings
        e.attrib.update(dict(
            st_mode='0',
            st_nlink='2',
            st_size='0',
            st_ctime=t,
            st_mtime=t,
            st_atime=t
        ))
        for k, v in attrib.items():
            e.attrib[k] = str(v)
        return e


if __name__ == '__main__':
    if len(argv) != 2:
        print('usage: %s <mountpoint>' % argv[0])
        exit(1)

    logging.basicConfig(level=logging.DEBUG)
    mountpoint = argv[1]
    fuse = FUSE(Memory(), mountpoint, foreground=True)
