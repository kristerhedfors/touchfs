"""Command line interface for generating content for files.

This module is maintained for backwards compatibility.
The implementation has been moved to the touchfs.cli.generate package.
"""

from .generate import (
    # Main CLI functions
    generate_main,
    add_generate_parser,
    run,
    
    # Filesystem utilities
    handle_filesystem_dialogue,
)

__all__ = [
    'generate_main',
    'add_generate_parser',
    'run',
    'handle_filesystem_dialogue',
]
