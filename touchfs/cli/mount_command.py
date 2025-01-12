"""Command line interface for mounting TouchFS filesystems.

This module is maintained for backwards compatibility.
The implementation has been moved to the touchfs.cli.mount package.
"""

from .mount import (
    # Main CLI functions
    mount_main,
    add_mount_parser,
    
    # Filesystem utilities
    handle_filesystem_dialogue,
    format_simple_tree,
    
    # Mount utilities
    get_mounted_touchfs,
)

__all__ = [
    'mount_main',
    'add_mount_parser',
    'handle_filesystem_dialogue',
    'format_simple_tree',
    'get_mounted_touchfs',
]
