#!/usr/bin/env python3
#
# llmfs.py
#
# Example memory filesystem backed by JSON, with LLM-based generation support.
#
import json
import os
import time
import copy
from .logger import setup_logging
from errno import ENOENT
from stat import S_IFDIR, S_IFLNK, S_IFREG
from sys import argv, exit
from typing import Dict, List, Optional, Union, Literal
from pathlib import Path

# For fusepy, do: pip install fusepy
from fuse import FUSE, FuseOSError, Operations, LoggingMixIn
from openai import OpenAI
from pydantic import BaseModel, Field

import dotenv
dotenv.load_dotenv()

# Models for structured output
class FileAttrs(BaseModel):
    st_mode: str
    st_uid: Optional[str] = None
    st_gid: Optional[str] = None

class FileNode(BaseModel):
    type: Literal["file", "directory", "symlink"]
    content: Optional[str] = ""
    children: Optional[Dict[str, str]] = None
    attrs: FileAttrs
    xattrs: Optional[Dict[str, str]] = None

class FileSystem(BaseModel):
    data: Dict[str, FileNode]

class GeneratedContent(BaseModel):
    content: str

def get_openai_client() -> OpenAI:
    """Initialize OpenAI client with API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    return OpenAI()

def read_prompt_file(path: str) -> str:
    """Read prompt from a file."""
    try:
        with open(path, 'r') as f:
            return f.read().strip()
    except Exception as e:
        raise ValueError(f"Failed to read prompt file: {e}")

def get_prompt() -> str:
    """Get prompt from environment, command line, or file."""
    # Try environment variable first
    prompt = os.getenv("LLMFS_PROMPT")
    if prompt:
        return prompt

    # Try command line argument
    if len(argv) > 2:
        prompt_arg = argv[2]
        # If it's a file path, read from file
        if os.path.isfile(prompt_arg):
            return read_prompt_file(prompt_arg)
        return prompt_arg

    raise ValueError("Prompt must be provided via LLMFS_PROMPT environment variable, command line argument, or file")

def generate_filesystem(prompt: str) -> Dict:
    """Generate filesystem structure using OpenAI."""
    client = get_openai_client()
    
    system_prompt = """
    You are a filesystem generator. Given a prompt, generate a JSON structure representing a filesystem.
    The filesystem must follow this exact structure:
    {
      "data": {
        "/": {
          "type": "directory",
          "children": {
            "example": "/example",
            "test": "/test"
          },
          "attrs": {
            "st_mode": "16877",  # directory with 755 permissions
            "st_size": "0"
          }
        },
        "/example": {
          "type": "directory",
          "children": {},
          "attrs": {
            "st_mode": "16877",
            "st_size": "0"
          }
        },
        "/test": {
          "type": "file",
          "content": null,  # Content will be generated on first read
          "attrs": {
            "st_mode": "33188",  # regular file with 644 permissions
            "st_size": "0"
          }
        }
      }
    }

    Rules:
    1. The response must have a top-level "data" field containing the filesystem structure
    2. Each node must have a "type" ("file", "directory", or "symlink")
    3. Each node must have "attrs" with st_mode and st_size
    4. For files:
       - Set content to null initially (it will be generated on first read)
       - Use st_mode "33188" for regular files (644 permissions)
    5. For directories:
       - Must have "children" mapping names to absolute paths
       - Use st_mode "16877" for directories (755 permissions)
    6. For symlinks:
       - Must have "content" with the target path
       - Use st_mode "41471" for symlinks (777 permissions)
    7. All paths must be absolute and normalized
    8. Root directory ("/") must always exist
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        # Parse and validate the response
        fs_data = json.loads(completion.choices[0].message.content)
        FileSystem.model_validate(fs_data)
        return fs_data
    except Exception as e:
        raise RuntimeError(f"Failed to generate filesystem: {e}")

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
    logger = setup_logging()

    def _get_default_times(self):
        """Get default time attributes."""
        now = str(int(time.time()))
        return {
            "st_ctime": now,
            "st_mtime": now,
            "st_atime": now
        }

    def _get_nlink(self, node_type):
        """Get appropriate nlink value based on node type."""
        return "2" if node_type == "directory" else "1"

    def _get_size(self, node):
        """Calculate size based on node type and content."""
        if node["type"] == "directory":
            return 0
        elif node["type"] == "symlink":
            return len(node.get("content", ""))
        else:  # file
            return len(node.get("content", "").encode('utf-8'))

    def __init__(self, initial_data=None):
        self.logger.info("Initializing Memory filesystem")
        self.fd = 0
        self._root = JsonFS()
        
        if initial_data:
            # Use provided filesystem data
            self._root._data = initial_data
        else:
            # Initialize empty root directory
            self._root._data["/"]["attrs"] = {
                "st_mode": str(S_IFDIR | 0o755)
            }
            
            # Create and initialize fs.json file
            self._root._data[self.FS_JSON] = {
                "type": "file",
                "content": "",
                "attrs": {
                    "st_mode": str(S_IFREG | 0o644)
                }
            }
            self._root.update()  # Update the JSON string
            fs_json_content = str(self._root)
            self._root._data[self.FS_JSON]["content"] = fs_json_content
            # Add fs.json to root directory's children
            self._root._data["/"]["children"]["fs.json"] = self.FS_JSON

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
        self.logger.info(f"Creating file: {path} with mode: {mode}")
        dirname, basename = self._split_path(path)
        
        parent = self[dirname]
        if not parent:
            self.logger.error(f"Parent directory not found for path: {path}")
            raise FuseOSError(ENOENT)
            
        self._root._data[path] = {
            "type": "file",
            "content": "",
            "attrs": {
                "st_mode": str(S_IFREG | mode)
            }
        }
        parent["children"][basename] = path
        
        self.fd += 1
        return self.fd

    def getattr(self, path, fh=None):
        if path == self.FS_JSON:
            self._root.update()
            node = self[self.FS_JSON]
        else:
            node = self[path]
            
        if node is None:
            raise FuseOSError(ENOENT)

        # Start with base attributes
        attr = {}
        for name, val in node["attrs"].items():
            if name.startswith('st_'):
                try:
                    attr[name] = int(val)
                except ValueError:
                    pass

        # Add time attributes if not present
        times = self._get_default_times()
        for time_attr in ["st_ctime", "st_mtime", "st_atime"]:
            if time_attr not in attr:
                attr[time_attr] = int(times[time_attr])

        # Add nlink if not present
        if "st_nlink" not in attr:
            attr["st_nlink"] = int(self._get_nlink(node["type"]))

        # Calculate size
        attr["st_size"] = self._get_size(node)

        return attr

    def getxattr(self, path, name, position=0):
        node = self[path]
        return node.get("xattrs", {}).get(name, '')

    def listxattr(self, path):
        node = self[path]
        return list(node.get("xattrs", {}).keys())

    def mkdir(self, path, mode):
        self.logger.info(f"Creating directory: {path} with mode: {mode}")
        dirname, basename = self._split_path(path)
        
        parent = self[dirname]
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
            # Generate content on first read if it's null
            if node.get("content") is None and node["type"] == "file":
                self.logger.info(f"Generating content for file: {path}")
                try:
                    # Get the entire filesystem structure
                    self._root.update()
                    fs_structure = str(self._root)
                    
                    client = get_openai_client()
                    system_prompt = f"""Generate appropriate Python code content for the file {path}.
The file exists within this filesystem structure:
{fs_structure}

Consider:
1. The file's location and name to determine its purpose
2. Its relationship to other files and directories
3. Follow Python best practices and PEP 8 style guide
4. Generate complete, working code that would make sense in this context

For Python files:
- If it's a module's main implementation file (like operations.py), include relevant classes and functions
- If it's a test file, include proper test cases using pytest
- If it's __init__.py, include appropriate imports and exports
- Include docstrings and type hints
- Ensure the code is complete and properly structured

Keep the code focused and production-ready."""

                    completion = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Generate Python code for {path} based on its context in the filesystem"}
                        ],
                        temperature=0.2
                    )
                    node["content"] = completion.choices[0].message.content
                    node["attrs"]["st_size"] = str(len(node["content"].encode('utf-8')))
                except Exception as e:
                    self.logger.error(f"Error generating content for {path}: {e}")
                    node["content"] = ""

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
        self.logger.info(f"Removing directory: {path}")
        node = self[path]
        if node and node["type"] == "directory":
            if node["children"]:
                self.logger.warning(f"Cannot remove non-empty directory: {path}")
                return
            try:
                parent = self[os.path.dirname(path)]
                parent["children"].pop(os.path.basename(path))
                del self._root._data[path]
                self.logger.debug(f"Successfully removed directory: {path}")
            except Exception as e:
                self.logger.error(f"Error removing directory {path}: {str(e)}", exc_info=True)
                raise
        else:
            self.logger.warning(f"Attempted to remove non-existent directory: {path}")

    def setxattr(self, path, name, value, options, position=0):
        node = self[path]
        if node:
            if "xattrs" not in node:
                node["xattrs"] = {}
            node["xattrs"][name] = value

    def statfs(self, path):
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)

    def symlink(self, target, source):
        dirname, basename = self._split_path(target)
        
        parent = self[dirname]
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

    def truncate(self, path, length, fh=None):
        node = self[path]
        if node:
            content = node.get("content", "")
            node["content"] = content[:length]
            node["attrs"]["st_size"] = str(length)

    def unlink(self, path):
        self.logger.info(f"Removing file: {path}")
        if path in self._root._data:
            try:
                parent = self[os.path.dirname(path)]
                parent["children"].pop(os.path.basename(path))
                del self._root._data[path]
                self.logger.debug(f"Successfully removed file: {path}")
            except Exception as e:
                self.logger.error(f"Error removing file {path}: {str(e)}", exc_info=True)
                raise
        else:
            self.logger.warning(f"Attempted to remove non-existent file: {path}")

    def utimens(self, path, times=None):
        now = time.time()
        atime, mtime = times if times else (now, now)
        node = self[path]
        if node:
            node["attrs"]["st_atime"] = str(atime)
            node["attrs"]["st_mtime"] = str(mtime)

    def write(self, path, data, offset, fh):
        self.logger.debug(f"Writing to file: {path} at offset: {offset}")
        node = self[path]
        if node:
            try:
                if isinstance(data, bytes):
                    data = data.decode('utf-8')
                content = node.get("content", "")
                if offset > len(content):
                    content = content.ljust(offset)
                new_content = content[:offset] + data
                node["content"] = new_content
                node["attrs"]["st_size"] = str(len(new_content.encode('utf-8')))
                self.logger.debug(f"Successfully wrote {len(data)} bytes to {path}")
                return len(data)
            except Exception as e:
                self.logger.error(f"Error writing to file {path}: {str(e)}", exc_info=True)
                raise
        self.logger.warning(f"Attempted to write to non-existent file: {path}")
        return 0

def main(mountpoint):
    if not mountpoint:
        print('usage: llmfs <mountpoint> [prompt_file]')
        print('   or: LLMFS_PROMPT="prompt" llmfs <mountpoint>')
        exit(1)

    # Setup production logging
    logger = setup_logging()

    try:
        # Get prompt and generate filesystem if provided
        initial_data = None
        try:
            prompt = get_prompt()
            print(f"Generating filesystem from prompt: {prompt[:50]}...")
            initial_data = generate_filesystem(prompt)["data"]
        except ValueError as e:
            print(f"No prompt provided, starting with empty filesystem: {e}")
        except Exception as e:
            print(f"Error generating filesystem: {e}")
            print("Starting with empty filesystem")

        # Mount filesystem
        fuse = FUSE(Memory(initial_data), mountpoint, foreground=True, allow_other=False)
    except RuntimeError as e:
        print(f"Error mounting filesystem: {e}")
        print("Note: You may need to create the mountpoint directory first")
        exit(1)

if __name__ == '__main__':
    main()
