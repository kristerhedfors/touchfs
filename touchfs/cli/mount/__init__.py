"""TouchFS mount command package.

This package provides functionality for mounting TouchFS filesystems.
It handles both mounting and listing mounted filesystems.

Key Features:
1. Mount TouchFS filesystems with FUSE
2. List currently mounted TouchFS filesystems
3. Interactive filesystem generation dialogue
4. Support for foreground/background operation
5. Configurable mount options (allow_other, allow_root, etc.)
"""

from .cli import mount_main, add_mount_parser
from .filesystem import handle_filesystem_dialogue, format_simple_tree
from .utils import get_mounted_touchfs

__all__ = [
    # Main CLI functions
    'mount_main',
    'add_mount_parser',
    
    # Filesystem utilities
    'handle_filesystem_dialogue',
    'format_simple_tree',
    
    # Mount utilities
    'get_mounted_touchfs',
]
