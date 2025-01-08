# TouchFS Touch Command

The `touchfs touch` command provides an explicit way to mark files for content generation, equivalent to using the standard `touch` command within a TouchFS filesystem.

## Usage

```bash
touchfs touch [options] file [file ...]
```

## Options

- `-p, --parents`: Create parent directories as needed
  ```bash
  # Example: Create file in new directory structure
  touchfs touch src/components/Button.tsx -p
  ```

- `-f, --force`: Skip confirmation for non-touchfs paths
  ```bash
  # Example: Skip confirmation prompts
  touchfs touch README.md --force
  ```

- `--debug-stdout`: Enable debug output to stdout
  ```bash
  # Example: Debug touch operations
  touchfs touch app.py --debug-stdout
  ```

- `-m, --max-tokens`: Maximum number of tokens to include in context
  ```bash
  # Example: Limit context size
  touchfs touch README.md --max-tokens 4000
  ```

## Key Features

1. Sets the generate_content xattr on files to mark them for generation
2. Interactive mode for directory-based file creation
3. Context-aware filename suggestions
4. Handles multiple files in a single command
5. Creates parent directories with --parents flag

## Common Use Cases

### Basic File Marking
```bash
# Mark a single file for generation
touchfs touch README.md

# Mark multiple files
touchfs touch app.py tests/test_app.py
```

### Interactive Directory Mode
```bash
# Enter interactive mode for a directory
touchfs touch src/components

# This will:
# 1. Generate filename suggestions based on directory context
# 2. Display an interactive menu for selection
# 3. Allow multiple selections
# 4. Option to regenerate suggestions
```

### Project Structure Creation
```bash
# Create and mark multiple related files
touchfs touch -p \
  src/models/user.py \
  src/models/product.py \
  tests/test_models.py
```

### Non-TouchFS Usage
```bash
# Mark files outside TouchFS filesystem
touchfs touch --force external/file.txt

# Create with parent directories
touchfs touch -p -f new/project/setup.py
```

## Context Generation

The command automatically builds context from the parent directory of the first specified file. This context is used for:
1. Generating filename suggestions in interactive mode
2. Understanding project structure for marking files
3. Ensuring consistent file organization

```bash
# Files will be marked with awareness of existing project context
touchfs touch \
  src/components/NewFeature.tsx \  # Context from src/components/
  src/hooks/useNewFeature.ts \     # Uses same context
  tests/NewFeature.test.tsx        # Uses same context
```

## Interactive Mode Features

When a single directory is provided as an argument, the command enters interactive mode:

1. **Filename Suggestions**:
   - Generates contextually relevant filename suggestions
   - Based on directory contents and structure
   - Updates suggestions based on previous selections

2. **Selection Menu**:
   - Multiple file selection support
   - Option to regenerate suggestions
   - Easy navigation and selection interface

3. **Iterative Creation**:
   - Can select multiple files in sequence
   - Maintains context between selections
   - Allows for organized file structure creation

## Error Handling

- Creates empty files if marking fails
- Returns success (0) even if some paths fail, matching touch behavior
- Provides detailed error messages with --debug-stdout
- Warns about non-touchfs paths
- Prompts for parent directory creation when needed

## Key Differences from Generate Command

The touch command differs from the generate command in several ways:

1. **Marking vs Generation**: Only marks files for generation rather than generating content immediately
2. **TouchFS Integration**: Designed to work within TouchFS filesystems
3. **Interactive Mode**: Provides interactive directory-based file creation
4. **Filename Suggestions**: Generates contextual filename suggestions
5. **Extended Attributes**: Sets filesystem extended attributes for TouchFS processing

## See Also

- [TouchFS Main Documentation](../README.md)
- [Mount Command](mount.md)
- [Generate Command](generate.md)
- [Context Command](context.md)
