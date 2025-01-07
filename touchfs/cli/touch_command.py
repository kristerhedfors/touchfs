"""Command line interface for marking files for TouchFS content generation.

This module is maintained for backwards compatibility.
The implementation has been moved to the touchfs.cli.touch package.
"""

from .touch import (
    # Main CLI functions
    touch_main,
    add_touch_parser,
    run,
    
    # Path utilities
    is_path_in_touchfs,
    categorize_paths,
    create_file_with_xattr,
    
    # UI functions
    generate_filename_suggestions,
    display_menu,
)

__all__ = [
    'touch_main',
    'add_touch_parser',
    'run',
    'is_path_in_touchfs',
    'categorize_paths', 
    'create_file_with_xattr',
    'generate_filename_suggestions',
    'display_menu',
]
