# TouchFS Context Command

The `touchfs context` command generates MCP-compliant context from files for LLM content generation. It provides structured file content collection with metadata that follows Model Context Protocol principles.

## Usage

```bash
touchfs context [options] [path]
```

If no path is provided, uses the current directory.

## Options

- `--max-tokens`, `-m`: Maximum number of tokens to include in context
  ```bash
  # Example: Limit context size
  touchfs context --max-tokens 4000
  ```

- `--exclude`, `-e`: Glob patterns to exclude (can be specified multiple times)
  ```bash
  # Example: Exclude specific patterns
  touchfs context \
    --exclude "*.pyc" \
    --exclude "node_modules/*" \
    --exclude ".git/*"
  ```

- `--include`, `-i`: Glob patterns to include (can be specified multiple times)
  ```bash
  # Example: Only include specific files
  touchfs context \
    --include "*.py" \
    --include "*.md"
  ```

- `--debug-stdout`: Enable debug output to stdout
  ```bash
  # Example: Debug context generation
  touchfs context --debug-stdout
  ```

- `--list-files`, `-l`: Only list file paths that would be included
  ```bash
  # Example: Preview included files
  touchfs context --list-files
  ```

## Output Format

The command generates a JSON structure containing:

1. **Version Information**:
   - Format version identifier
   - MCP compliance metadata

2. **File Resources**:
   - File contents with URIs
   - File metadata (path, size, type)
   - Token usage statistics

3. **Collection Metadata**:
   - Total token count
   - File count
   - Collection timestamp

## Common Use Cases

### Basic Context Generation
```bash
# Generate context from current directory
touchfs context

# Generate from specific directory
touchfs context /path/to/project
```

### Filtered Context Generation
```bash
# Include only Python and documentation files
touchfs context \
  --include "*.py" \
  --include "*.md" \
  --exclude "tests/*"
```

### Token Management
```bash
# Limit context size for large projects
touchfs context \
  --max-tokens 8000 \
  --exclude "*.min.js" \
  --exclude "vendor/*"
```

### Context Preview
```bash
# List files that would be included
touchfs context --list-files

# Preview with debug information
touchfs context --debug-stdout --list-files
```

## Use Cases for Context Generation

### Development Support
- Understanding project structure
- Analyzing code patterns
- Generating documentation
- Creating test cases

### Content Generation
- Providing context for file generation
- Maintaining consistent style
- Understanding project conventions
- Guiding code completion

### Project Analysis
- Token usage assessment
- File organization review
- Dependency analysis
- Code quality checks

## Error Handling

- Reports token limit exceeded conditions
- Handles missing or invalid directories
- Provides debug output for troubleshooting
- Gracefully handles file access errors

## Integration with Other Commands

The context command supports other TouchFS commands by:

1. **Mount Command**: Provides context for filesystem generation
2. **Generate Command**: Supplies context for content generation
3. **Touch Command**: Informs filename suggestions and file organization

## See Also

- [TouchFS Main Documentation](../README.md)
- [Mount Command](mount.md)
- [Generate Command](generate.md)
- [Touch Command](touch.md)
