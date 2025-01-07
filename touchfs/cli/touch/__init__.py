"""TouchFS touch command package.

This package provides functionality for marking files for TouchFS content generation.
It extends the behavior of the standard touch command within TouchFS filesystems.

Key Features:
1. Like touch, creates files if they don't exist
2. Sets generate_content xattr to mark files for content generation
3. Extends touch with --parents/-p flag to create parent directories
4. Handles multiple files in a single command
5. Safe operation with confirmation for non-touchfs paths
"""

from .cli import touch_main, add_touch_parser, run
from .path_utils import is_path_in_touchfs, categorize_paths, create_file_with_xattr
from .ui import generate_filename_suggestions, display_menu

__all__ = [
    # Main CLI functions
    'touch_main',
    'add_touch_parser',
    'run',
    
    # Path utilities
    'is_path_in_touchfs',
    'categorize_paths',
    'create_file_with_xattr',
    
    # UI functions
    'generate_filename_suggestions',
    'display_menu',
]
