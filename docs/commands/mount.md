# TouchFS Mount Command

The `touchfs mount` command creates and mounts a TouchFS filesystem at a specified directory.

## Usage

```bash
touchfs mount [options] [mountpoint]
```

If no mountpoint is provided, lists currently mounted TouchFS filesystems.

## Options

- `-p, --prompt`: Set default prompt for content generation when files are touched
  ```bash
  # Example: Set content generation prompt
  touchfs mount workspace -p "Create modern TypeScript components"
  ```

- `-F, --filesystem-generation-prompt`: Generate initial filesystem structure before mounting
  ```bash
  # Example: Generate project structure on mount
  touchfs mount workspace -F "Create a FastAPI project structure with tests"
  ```

- `--overlay`: Mount on top of existing directory, merging contents
  ```bash
  # Example: Generate tests for existing project
  touchfs mount workspace --overlay ./my-project
  ```

- `-f, --foreground`: Run in foreground with debug output to stdout
  ```bash
  # Example: Debug mount issues
  touchfs mount workspace -f
  ```

- `--allow-other`: Allow other users to access the mount
  ```bash
  # Example: Allow access for other users
  touchfs mount workspace --allow-other
  ```

- `--allow-root`: Allow root to access the mount
  ```bash
  # Example: Allow root access
  touchfs mount workspace --allow-root
  ```

- `--nothreads`: Disable multi-threading
  ```bash
  # Example: Run single-threaded
  touchfs mount workspace --nothreads
  ```

- `--nonempty`: Allow mounting over non-empty directory
  ```bash
  # Example: Mount over existing directory
  touchfs mount workspace --nonempty
  ```

## Common Use Cases

### Basic Empty Filesystem
```bash
# Mount with default settings
touchfs mount workspace
```

### Content Generation with Prompt
```bash
# Mount with specific content generation style
touchfs mount workspace -p "Write modern, well-documented Python code with type hints"
```

### Initial Project Structure
```bash
# Generate structure and set content style
touchfs mount workspace \
  -F "Create a React Native mobile app structure" \
  -p "Write TypeScript React Native components with clean architecture"
```

### Development with Overlay
```bash
# Mount on existing project to extend it
touchfs mount workspace --overlay ./my-project

# Now you can generate new files that complement existing ones:
touch workspace/tests/test_api.py  # Generates test based on existing api.py
touch workspace/docs/api.md        # Generates docs based on implementation
```

### Debugging
```bash
# Run in foreground with debug output
touchfs mount workspace -f

# Check logs at /var/log/touchfs/touchfs.log
tail -f /var/log/touchfs/touchfs.log
```

## Examples with Different Project Types

### React Frontend
```bash
touchfs mount workspace \
  -F "Create a modern React frontend project with TypeScript" \
  -p "Write clean, maintainable React components"
```

### FastAPI Backend
```bash
touchfs mount workspace \
  -F "Create a FastAPI backend with SQLAlchemy and tests" \
  -p "Write async Python with type hints and docstrings"
```

### Mobile App
```bash
touchfs mount workspace \
  -F "Create a React Native app with navigation and state management" \
  -p "Write modern mobile components with TypeScript"
```

### Documentation Site
```bash
touchfs mount workspace \
  -F "Create a technical documentation site structure" \
  -p "Write clear, comprehensive documentation with examples"
```

## See Also

- [TouchFS Main Documentation](../README.md)
- [Generate Command](generate.md)
- [Touch Command](touch.md)
- [Context Command](context.md)
