"""Filesystem generation functionality for TouchFS generate command.

This module reuses the filesystem generation functionality from the mount command
to provide consistent behavior across commands.
"""

from ..mount.filesystem import handle_filesystem_dialogue, format_simple_tree

__all__ = ['handle_filesystem_dialogue', 'format_simple_tree']
