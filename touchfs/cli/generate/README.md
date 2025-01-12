# TouchFS Generate Command

This package provides the implementation for the TouchFS generate command. The command supports two modes of operation:

1. File Generation Mode:
   - Generate content for specific files
   - Each file is created if it doesn't exist
   - Content is generated immediately by default using TouchFS content generation
   - Can create empty files with -n/--no-content flag
   - Supports creating parent directories with -p/--parents flag
   - Handles multiple files in a single command
   - Displays generation stats (characters, lines, time) for each file

2. Filesystem Generation Mode (-F):
   - Generate an entire filesystem structure from a prompt
   - Creates directories and files according to the generated structure
   - Files are created with content by default
   - Can create empty files with -n/--no-content flag
   - Interactive refinement of structure (unless -y/--yes flag is used)
   - Target directory must be empty or non-existent

## Package Structure

- `__init__.py`: Package initialization and exports
- `cli.py`: Main CLI functionality and argument parsing
- `filesystem.py`: Filesystem generation and dialogue handling (reuses mount command functionality)

## Code Reuse

This package reuses functionality from other TouchFS commands to ensure consistent behavior:

- From mount command:
  - Filesystem generation dialogue (`handle_filesystem_dialogue`)
  - Tree visualization (`format_simple_tree`)
  
- From touch command:
  - File creation utilities (`create_file_with_xattr`)
  - Path handling utilities

## Example Usage

```bash
# Generate content for specific files (default behavior)
touchfs generate file1.txt file2.md

# Create empty files without content
touchfs generate -n file1.txt file2.md

# Create parent directories if needed
touchfs generate -p path/to/new/file.txt

# Generate filesystem structure with content
touchfs generate -F "Create a Python project structure" myproject/

# Generate filesystem structure without content
touchfs generate -F "Create a Python project structure" -n myproject/

# Auto-confirm filesystem structure
touchfs generate -F "Create a Python project structure" -y myproject/
