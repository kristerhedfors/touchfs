# TouchFS Generate Command

The `touchfs generate` command provides two modes of operation:

1. File Generation Mode: Directly generates content for specific files
2. Filesystem Generation Mode: Creates directory structures with content from a prompt

By default, files are created with AI-generated content. Each generated file includes statistics showing the number of characters, lines, and generation time.

## Usage

```bash
# File Generation Mode
touchfs generate [options] file [file ...]

# Filesystem Generation Mode
touchfs generate -F "prompt" [options] directory
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

- `-n, --no-content`: Create empty files without generating content
  ```bash
  # Example: Create empty files
  touchfs generate -n file1.txt file2.txt
  ```

- `-F, --filesystem-generation-prompt`: Generate filesystem structure from prompt
  ```bash
  # Example: Create project structure
  touchfs generate -F "Create a React project" myproject/
  ```

- `-y, --yes`: Auto-confirm filesystem structure without prompting (only with -F)
  ```bash
  # Example: Auto-confirm structure
  touchfs generate -F "Create a React project" -y myproject/
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
2. Generates content by default using TouchFS content generation
3. Provides file generation statistics (chars, lines, time)
4. Can create empty files with --no-content flag
5. Uses project context for intelligent content generation
6. Handles multiple files in a single command
7. Creates parent directories with --parents flag
8. Can generate entire directory structures from prompts

## Common Use Cases

### Single File Generation
```bash
# Generate a file with content (default)
touchfs generate README.md

# Generate an empty file
touchfs generate -n README.md

# Generate with parent directories
touchfs generate src/utils/helpers.ts -p
```

### Multiple File Generation
```bash
# Generate several related files with content
touchfs generate \
  src/models/user.py \
  src/models/product.py \
  tests/test_models.py

# Generate empty files
touchfs generate -n \
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

### Filesystem Generation
```bash
# Generate project structure with content
touchfs generate -F "Create a React app with TypeScript" myapp/

# Generate project structure without content
touchfs generate -F "Create a React app with TypeScript" -n myapp/

# Auto-confirm structure
touchfs generate -F "Create a React app with TypeScript" -y myapp/
```

## Key Differences from Touch Command

The generate command differs from the touch command in several important ways:

1. **Direct Generation**: Immediately generates and writes content by default
2. **No Mount Required**: Works without needing a mounted TouchFS filesystem
3. **Parent Directory Creation**: Can create parent directories with the --parents flag
4. **Batch Processing**: Handles multiple files in a single command
5. **Context Awareness**: Uses the directory context of the first file for all generations
6. **Confirmation Flow**: Prompts for confirmation before generation (unless --force is used)
7. **Generation Stats**: Shows character count, line count, and generation time
8. **Filesystem Generation**: Can create entire directory structures from prompts

## Context Generation

The command automatically builds context from the parent directory of the first specified file. This context is used to ensure generated content is relevant and consistent with existing project files.

```bash
# Files will be generated with awareness of existing project context
touchfs generate \
  src/components/NewFeature.tsx \  # Context from src/components/
  src/hooks/useNewFeature.ts \     # Uses same context
  tests/NewFeature.test.tsx        # Uses same context

# Output includes generation stats for each file
# Generated src/components/NewFeature.tsx: 1234 chars, 45 lines in 2.31s
# Generated src/hooks/useNewFeature.ts: 567 chars, 23 lines in 1.45s
# Generated tests/NewFeature.test.tsx: 890 chars, 34 lines in 1.89s
```

## Error Handling

- Creates empty files if generation fails
- Returns success (0) even if some paths fail, matching touch behavior
- Provides detailed error messages with --debug-stdout
- Warns about missing parent directories when --parents is not used
- Shows error messages for failed content generation attempts

## See Also

- [TouchFS Main Documentation](../README.md)
- [Mount Command](mount.md)
- [Touch Command](touch.md)
- [Context Command](context.md)
