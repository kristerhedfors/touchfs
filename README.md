# 🌳 TouchFS - The Touch Screen of File Systems

Just as touch screens revolutionized user interfaces by making buttons context-aware within apps, TouchFS brings that same revolution to the filesystem level. Touch a file, and it materializes with perfect context awareness. This fundamental pattern is now published, unpatentable, and freely available under the MIT license.

## The Power of Touch

```bash
# Mount your context-aware filesystem
touchfs mount workspace --overlay ./src

# Want a README? Just touch it.
touch README.md

# Done. The filesystem understood its context and materialized the content.
```

Need something specific? Set your context:

```bash
echo "Create a technical README focusing on the API endpoints" > .prompt
touch README_v2.md
```

## Technical Implementation

When TouchFS intercepts a `touch` command, it:
1. Blocks file operations while looking up the actual touch process
2. Interprets the command's arguments to resolve file paths
3. Flags the targeted files with an extended attribute `generate_content=True`

## How It Works

The order in which you create files affects their generated content. Each unique context (including generation order) produces different content, which is automatically cached:

```bash
# Mount with a project prompt (uses GPT to understand and generate text content)
touchfs mount ~/project --prompt "Create a web scraping tool"

# When done, unmount the filesystem
touchfs mount -u ~/project

# Scenario 1: README first, then app
touch README.md
touch app.py

# Result:
# ┌─────────────────┐          ┌─────────────────┐
# │   README.md     │          │     app.py      │
# │ (Generated 1st) │──────────│  (Generated 2nd) │
# │                 │          │                  │
# │ Web Scraper     │          │ import requests  │
# │ ============    │  shapes  │                  │
# │ A Python tool   │───app────│ def scrape():   │
# │ for scraping    │  design  │   # Implement   │
# │ websites...     │          │   # scraping    │
# └─────────────────┘          └─────────────────┘
#                    [Cache A]

# Scenario 2: app first, then README
rm README.md app.py  # Clear previous files
touch app.py
touch README.md

# Result:
# ┌─────────────────┐          ┌─────────────────┐
# │     app.py      │          │   README.md     │
# │ (Generated 1st) │──────────│  (Generated 2nd) │
# │                 │          │                  │
# │ from bs4 import │  guides  │ Web Scraper     │
# │ BeautifulSoup  │───doc────│ ============    │
# │                 │  style   │ Uses Beautiful  │
# │ class Scraper:  │          │ Soup for HTML   │
# │   def parse():  │          │ parsing...      │
# └─────────────────┘          └─────────────────┘
#                    [Cache B]
```

## Sequential Generation

Generate entire project structures with context awareness:

```bash
# Create a list of files for GPT to generate in sequence
cat > files.txt << EOF
src/models.py
src/database.py
src/api.py
tests/test_models.py
tests/test_api.py
README.md
EOF

# Create necessary directories
mkdir -p src tests

# Generate files in sequence
touch $(cat files.txt)

# Result (GPT generates each file in order, using previous files as context):
# ┌─────────────┐
# │ models.py   │ 1st: Defines core data models
# └─────┬───────┘
#       │
#       ▼
# ┌─────────────┐
# │database.py  │ 2nd: Uses models to create DB schema
# └─────┬───────┘
#       │
#       ▼
# ┌─────────────┐
# │   api.py    │ 3rd: Implements API using models & DB
# └─────┬───────┘
#       │
#       ▼
# ┌─────────────┐
# │test_models  │ 4th: Tests based on actual model impl
# └─────┬───────┘
#       │
#       ▼
# ┌─────────────┐
# │ test_api    │ 5th: API tests using real models & DB
# └─────┬───────┘
#       │
#       ▼
# ┌─────────────┐
# │  README.md  │ 6th: Docs based on full implementation
# └─────────────┘
```

This approach lets you define complex generation sequences in a simple text file. Each file is generated with awareness of all previously generated files, creating a cohesive codebase where later files naturally build upon earlier ones.

## Image Generation

For image files, TouchFS uses DALL-E 3 to generate content based on context from surrounding files:

```bash
# Mount an art project filesystem
touchfs mount ~/art --prompt "Create concept art for a sci-fi game"

# When finished, unmount the filesystem
touchfs mount -u ~/art

# Generate images in sequence
touch character.jpg     # DALL-E 3 generates based on filename and project context
touch background.jpg    # Uses context from character.jpg to maintain visual style
touch character_in_background.jpg  # Combines context from both previous images
```

Each image is generated with awareness of previously generated images and surrounding files, with DALL-E 3 using this rich context to maintain consistent style, theme, and visual coherence across the project. This context-aware generation ensures that each new image naturally fits within the established visual language of the project.

In Scenario 1 above, the README is generated first, establishing high-level concepts that influence the app's implementation. In Scenario 2, the app is generated first, making concrete implementation choices that the README then documents. Each scenario's unique context (including generation order) is part of the cache key, ensuring consistent results when repeating the same sequence.

## Overlay Mount Mode

TouchFS can be mounted in overlay mode, where it acts as a writable layer on top of an existing directory:

```bash
# Mount TouchFS in overlay mode on top of an existing project
touchfs mount ~/mount-point --overlay ~/existing-project

# The mount point now shows:
# 1. All files from ~/existing-project (read-only)
# 2. Any new files you create (writable TouchFS layer)
# 3. Both layers merged into a single view

# Example: Generate new test files alongside existing code
ls ~/existing-project
# src/
#   app.py
#   models.py

touch ~/mount-point/tests/test_app.py
touch ~/mount-point/tests/test_models.py

# Result:
# ┌─────────────────┐          ┌─────────────────┐
# │ Existing Files  │          │  TouchFS Layer  │
# │  (Read-only)    │          │   (Writable)    │
# │                 │          │                 │
# │ src/           │          │ tests/          │
# │  ├── app.py    │  guides  │  ├── test_app.py│
# │  └── models.py │───tests──│  └── test_models│
# │                 │          │                 │
# └─────────────────┘          └─────────────────┘
#          Merged view in ~/mount-point
#                shows both layers

# When done, unmount as usual
touchfs mount -u ~/mount-point
```

The overlay mode is useful for:
- Generating tests for existing code
- Adding documentation to existing projects
- Extending projects with new features
- Experimenting with changes without modifying original files

All generated content remains context-aware, taking into account both the existing files (read-only layer) and any new files you create (TouchFS layer).

## Installation

```bash
pip install touchfs

# Set up your OpenAI API key
export OPENAI_API_KEY="your-api-key-here"
```

## CLI Commands

### Mount Command

The `touchfs mount` command mounts a TouchFS filesystem at a specified directory:

```bash
# Basic mount
touchfs mount ~/workspace

# Mount with content generation prompt
touchfs mount ~/workspace -p "Create a web scraping tool"

# Mount with filesystem generation prompt
touchfs mount ~/workspace -F "Create a project structure for a web scraper"

# Mount in foreground mode with debug output
touchfs mount ~/workspace -f

# Mount with specific permissions
touchfs mount ~/workspace --allow-other --allow-root

# List currently mounted TouchFS filesystems
touchfs mount
```

Key options:
- `-p, --prompt`: Set default prompt for file content generation
- `-F, --filesystem-generation-prompt`: Generate initial filesystem structure from prompt
- `-f, --foreground`: Run in foreground with debug output to stdout
- `-u, --unmount`: Unmount the filesystem (alternative to umount command)
- `--allow-other`: Allow other users to access the mount
- `--allow-root`: Allow root to access the mount
- `--nothreads`: Disable multi-threading
- `--nonempty`: Allow mounting over non-empty directory
- `--force`: Force unmount even if busy (with -u)

### Umount Command

The `touchfs umount` command unmounts a TouchFS filesystem:

```bash
# Basic unmount
touchfs umount ~/workspace

# Force unmount if busy
touchfs umount ~/workspace --force
```

This is equivalent to `touchfs mount -u` but provides a more familiar command name for Unix users.

### Generate Command

The `touchfs generate` command generates content for files using the same content generation functionality as TouchFS mount points:

```bash
# Generate content for a single file
touchfs generate file.txt

# Create parent directories if needed
touchfs generate path/to/new/file.txt -p

# Generate content for multiple files at once
touchfs generate file1.txt file2.py README.md

# Skip confirmation prompt
touchfs generate file.txt --force
```

Unlike the touch command which only marks files for generation, this command directly generates and writes the content using TouchFS's content generation functionality. This is particularly useful for:
- One-off content generation without mounting a TouchFS filesystem
- Batch generating content for multiple files
- Testing content generation results quickly
- Creating files with generated content in non-existent directory structures

### Touch Command

The `touchfs touch` command provides an explicit way to mark files for content generation, equivalent to using `touch` within a TouchFS filesystem:

```bash
# Mark a single file for generation
touchfs touch file.txt

# Create parent directories if needed
touchfs touch path/to/new/file.txt -p

# Mark multiple files at once
touchfs touch file1.txt file2.py README.md

# Skip confirmation for non-touchfs paths
touchfs touch file.txt --force
```

This command sets the generate_content xattr that TouchFS uses to identify files that should have their content generated. Within a TouchFS filesystem, this is automatically set by the touch command - this CLI provides an explicit way to set the same marker.

### Context Command

The `touchfs context` command generates MCP-compliant context from files for LLM content generation:

```bash
# Generate context from current directory
touchfs context

# Generate context from specific directory
touchfs context /path/to/directory

# Limit token count
touchfs context --max-tokens 4000

# Exclude specific patterns
touchfs context --exclude "*.pyc" --exclude "node_modules/*"

# Enable debug output
touchfs context --debug-stdout
```

The command generates a JSON structure containing:
- File contents as MCP resources with URIs and metadata
- Token usage statistics (controlled by --max-tokens, affects both content and metadata)
- File collection metadata

This is useful for:
- Understanding what context TouchFS will use for generation
- Debugging content generation issues
- Creating custom generation workflows
- Testing context collection without triggering generation

## Documentation

- [Architecture & Technical Details](docs/architecture.md)
- [Plugin System](touchfs/content/plugins/README.md)
- [Example Projects](examples/README.md)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License. The context-aware file generation pattern described here is now published prior art and cannot be patented. Like the touch screen revolution before it, this fundamental pattern is now free for everyone to use, share, and build upon.
