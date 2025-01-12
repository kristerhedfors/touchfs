"""TouchFS generate command package.

This package provides functionality for generating content for files and filesystem
structures. It supports both individual file content generation and complete
filesystem structure generation from prompts.

Key Features:
1. Creates files if they don't exist
2. Generates content immediately using TouchFS content generation
3. Extends with --parents/-p flag to create parent directories
4. Handles multiple files in a single command
5. Supports filesystem structure generation from prompts (-F flag)
"""

from .cli import generate_main, add_generate_parser, run
from .filesystem import handle_filesystem_dialogue

__all__ = [
    # Main CLI functions
    'generate_main',
    'add_generate_parser',
    'run',
    
    # Filesystem functions
    'handle_filesystem_dialogue',
]
