# TouchFS Mount Package

This package provides functionality for mounting TouchFS filesystems. It is organized into several modules:

## Modules

### cli.py
Contains the main CLI functionality for mounting TouchFS filesystems, including argument parsing and the main mount command implementation.

### filesystem.py
Handles filesystem generation and interactive dialogue with users during filesystem generation. Includes utilities for formatting filesystem trees.

### utils.py
Provides utility functions for working with mounted TouchFS filesystems, such as listing currently mounted filesystems.

## Usage

The package is typically used through the `touchfs mount` command, but its components can also be used programmatically:

```python
from touchfs.cli.mount import mount_main, get_mounted_touchfs

# List mounted filesystems
mounted = get_mounted_touchfs()
for mountpoint, pid, cmd in mounted:
    print(f"{mountpoint} {pid} {cmd}")

# Mount a filesystem
exit_code = mount_main(
    mountpoint="/path/to/mount",
    foreground=True,
    filesystem_generation_prompt="Create a Python project"
)
```

## Testing

The mount functionality is tested in `tests/test_mount_basic.py` and related test files. The tests cover:
- Basic mounting and unmounting
- Filesystem generation
- Mount point listing
- Error handling
