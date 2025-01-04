# 🌳 TouchFS - Context-Aware File Generation

TouchFS is a filesystem that generates file content using OpenAI's models - GPT for text files and DALL-E 3 for images. It can generate entire filesystem structures, overlay existing directories, or mount fresh empty filesystems. When a file is touched in a mounted TouchFS, the system automatically gathers context from surrounding files and includes this context in a generation prompt. For text files, this enables the creation of coherent content that naturally relates to its environment. For image files, DALL-E 3 uses this surrounding context to generate visually consistent and contextually appropriate images. While TouchFS defaults to using `touch` as the trigger for this context-gathering and generation process, this is entirely optional - you can disable it in favor of dedicated commands that modify file attributes (xattrs) to control generation behavior.

## Why the Filesystem Layer?

There exists a philosophical question in the age of LLMs: at which layer of the technology stack should AI integration occur for optimal impact? While current trends favor web-based chat interfaces, TouchFS presents an argument for integration at the filesystem layer, rooted in several key observations:

1. **Universal Convergence Point**: Despite the diversity of modern technology stacks, from web applications to embedded systems, from databases to documentation, they all ultimately organize their information in files. The filesystem serves as a universal convergence point where different technologies, each with their distinct purposes, coexist in a shared namespace.

2. **Time-Tested Tooling**: The Unix philosophy and its tools for working with files have proven their worth since the 1970s. By integrating LLMs at the filesystem layer, we leverage this entire ecosystem of battle-tested tools (`ls`, `find`, `grep`, etc.) that developers have relied on for decades.

3. **Flexible Integration**: TouchFS's default behavior uses the familiar `touch` operation to trigger context gathering and content generation - when a file is touched, the system analyzes surrounding files to build a rich context that informs the generation prompt. However, this trigger mechanism is completely optional. You can configure the system to use dedicated commands for modifying extended attributes (xattrs) instead, providing precise control over when and how context is gathered and content is generated.

4. **Context-Rich Environment**: The filesystem hierarchy naturally provides rich context about project structure and relationships between components. Whether generating individual files, entire directory structures, or overlaying existing projects, this contextual information is gathered and incorporated into generation prompts, allowing for more coherent and contextually aware content creation - whether that's code, documentation, or even images.

While web-based chat interfaces currently dominate LLM interactions, TouchFS demonstrates that the filesystem layer offers unique advantages for certain use cases, particularly in software development where file relationships and project context are crucial. The examples below illustrate how this philosophical approach materializes in practice.

## Using Touch for Experimentation

TouchFS's use of the `touch` command provides a remarkably convenient pattern for experimentation. When exploring ideas or prototyping concepts, the ability to materialize content simply by touching a file creates a fluid, intuitive workflow.

The intentional redefinition of this POSIX command positions TouchFS firmly in the research and innovation space - it's a deliberate design choice that prioritizes experimental freedom over production readiness. This makes TouchFS an ideal platform in the context of research and innovation, for exploring new ideas in AI-filesystem integration without the constraints of traditional production requirements.

### Technical Implementation
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

# Note: No need to disable caching! Each scenario creates a different context,
# resulting in different cache entries. Running the same scenario again will
# use its cached content, but changing the order creates a new context with
# new generations.
```

## Sequential Generation

You can define a sequence of files to generate using a simple text file:

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

### Generate Command

The `touchfs generate` command provides an explicit way to mark files for content generation, equivalent to using `touch` within a TouchFS filesystem:

```bash
# Mark a single file for generation
touchfs generate file.txt

# Create parent directories if needed
touchfs generate path/to/new/file.txt -p

# Mark multiple files at once
touchfs generate file1.txt file2.py README.md

# Skip confirmation for non-TouchFS paths
touchfs generate /path/outside/touchfs/file.txt -f
```

Key features:
- Creates files if they don't exist (like `touch`)
- Sets the `generate_content` xattr to mark files for generation
- Creates parent directories with `--parents/-p` flag
- Handles multiple files in a single command
- Safe operation with confirmation for non-TouchFS paths

This command is particularly useful for:
- Working with files outside a TouchFS mount that will be moved into one
- Making content generation intent explicit in scripts/automation
- Batch marking multiple files for generation
- Creating files in non-existent directory structures

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
```

The command generates a JSON structure containing:
- File contents as MCP resources with URIs and metadata
- Token usage statistics
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

This project is licensed under the MIT License - see the LICENSE file for details.
