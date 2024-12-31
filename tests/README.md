# TouchFS Testing Guide

## Test Setup

The test suite uses pytest and provides several key fixtures in `conftest.py`:

- `setup_test_logging`: Session-scoped fixture that initializes logging before any tests run
- `mount_point`: Function-scoped fixture that creates a temporary directory for mounting the filesystem
- `mounted_fs`: Function-scoped fixture that mounts the filesystem and yields the mount point
- `mounted_fs_foreground`: Similar to mounted_fs but runs in foreground mode
- `mounted_fs_debug`: Mounts filesystem in debug mode and yields both mount point and process

## Test Coverage Areas

The test suite covers several key areas:

1. Basic Mount Operations (`test_mount_basic.py`)
2. File Operations (`test_file_operations.py`)
3. Directory Operations (`test_directory_operations.py`)
4. Symlink Operations (`test_symlink_operations.py`)
5. Touch Operations (`test_touch_operations.py`)
6. Content Generation (`test_content_generation.py`)
7. Filesystem Generation (`test_filesystem_generation.py`)
8. Plugin System Tests:
   - Cache Control (`test_cache_control_plugin.py`)
   - Executive (`test_executive_plugin.py`)
   - Image (`test_image_plugin.py`)
   - Model (`test_model_plugin.py`)
   - Proc (`test_proc_plugin.py`)
   - Prompt (`test_prompt_plugin.py`)
   - README (`test_readme_plugin.py`)
   - Tree (`test_tree_plugin.py`)

## Log Rotation Testing

The log rotation testing (`test_log_rotation.py`) verifies:

1. Initial log file creation and writing
2. Log file rotation when setup_logging is called again
3. Proper handling of permission errors during rotation
4. Write verification after rotation
5. Cleanup of rotated log files

Key aspects of log rotation tests:
- Uses a temporary directory for log files
- Verifies log file existence and content
- Tests error conditions (permission errors)
- Ensures proper cleanup after rotation

### Log Rotation Test Setup

The test uses several helper functions and fixtures:

- `verify_log_file()`: Verifies log file existence and minimum size
- `_reset_logger`: Fixture that resets logger state before each test
- Temporary directory creation for isolated testing
- Permission modification tests to verify error handling

## Running Tests

To run the full test suite:
```bash
pytest
```

To run specific test files:
```bash
pytest tests/test_log_rotation.py
```

To run tests in debug mode:
```bash
pytest -v --debug
