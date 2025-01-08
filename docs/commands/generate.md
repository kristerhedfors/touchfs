# TouchFS Generate Command

The `touchfs generate` command directly generates content for files using TouchFS's content generation functionality, without requiring a mounted filesystem.

## Usage

```bash
touchfs generate [options] file [file ...]
```

## Options

- `-p, --parents`: Create parent directories as needed
  ```bash
  # Example: Create file in new directory structure
  touchfs generate src/components/Button.tsx -p
  ```

- `-f, --force`: Skip confirmation prompts
  ```bash
  # Example: Generate without confirmation
  touchfs generate README.md --force
  ```

- `--debug-stdout`: Enable debug output to stdout
  ```bash
  # Example: Debug generation issues
  touchfs generate app.py --debug-stdout
  ```

- `-m, --max-tokens`: Maximum number of tokens to include in context
  ```bash
  # Example: Limit context size
  touchfs generate README.md --max-tokens 4000
  ```

## Key Features

1. Creates files if they don't exist
2. Generates content immediately using TouchFS content generation
3. Uses project context for intelligent content generation
4. Handles multiple files in a single command
5. Creates parent directories with --parents flag

## Common Use Cases

### Single File Generation
```bash
# Generate a single file
touchfs generate README.md

# Generate with parent directories
touchfs generate src/utils/helpers.ts -p
```

### Multiple File Generation
```bash
# Generate several related files at once
touchfs generate \
  src/models/user.py \
  src/models/product.py \
  tests/test_models.py
```

### Project Documentation
```bash
# Generate documentation files
touchfs generate \
  README.md \
  docs/api.md \
  docs/setup.md \
  CONTRIBUTING.md
```

### Component Creation
```bash
# Generate React component with types and tests
touchfs generate \
  src/components/Button.tsx \
  src/components/Button.test.tsx \
  src/types/button.ts
```

## Key Differences from Touch Command

The generate command differs from the touch command in several important ways:

1. **Direct Generation**: Immediately generates and writes content, rather than just marking files for generation
2. **No Mount Required**: Works without needing a mounted TouchFS filesystem
3. **Parent Directory Creation**: Can create parent directories with the --parents flag
4. **Batch Processing**: Handles multiple files in a single command
5. **Context Awareness**: Uses the directory context of the first file for all generations
6. **Confirmation Flow**: Prompts for confirmation before generation (unless --force is used)

## Context Generation

The command automatically builds context from the parent directory of the first specified file. This context is used to ensure generated content is relevant and consistent with existing project files.

```bash
# Files will be generated with awareness of existing project context
touchfs generate \
  src/components/NewFeature.tsx \  # Context from src/components/
  src/hooks/useNewFeature.ts \     # Uses same context
  tests/NewFeature.test.tsx        # Uses same context
```

## Error Handling

- Creates empty files if generation fails
- Returns success (0) even if some paths fail, matching touch behavior
- Provides detailed error messages with --debug-stdout
- Warns about missing parent directories when --parents is not used

## See Also

- [TouchFS Main Documentation](../README.md)
- [Mount Command](mount.md)
- [Touch Command](touch.md)
- [Context Command](context.md)
