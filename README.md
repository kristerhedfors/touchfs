# 🌳 TouchFS - Context-Aware File Generation

TouchFS is a filesystem that generates file content using OpenAI's models - GPT for text files and DALL-E for images. When you touch a file, its content is generated taking into account its location in the filesystem and the contents of other files in the project. This context-aware generation creates coherent projects where files naturally relate to and build upon each other.

## How It Works

The order in which you create files affects their generated content. Each unique context (including generation order) produces different content, which is automatically cached:

```bash
# Mount with a project prompt (uses GPT to understand and generate text content)
touchfs_mount ~/project --prompt "Create a web scraping tool"

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

For image files, TouchFS uses DALL-E to generate content:

```bash
# Mount an art project filesystem
touchfs_mount ~/art --prompt "Create concept art for a sci-fi game"

# Generate images in sequence
touch character.jpg     # DALL-E generates based on filename
touch background.jpg    # Can reference character's style
touch character_in_background.jpg  # Combines both previous images' context
```

Each image is generated with awareness of previously generated images, maintaining consistent style and theme across the project.

In Scenario 1 above, the README is generated first, establishing high-level concepts that influence the app's implementation. In Scenario 2, the app is generated first, making concrete implementation choices that the README then documents. Each scenario's unique context (including generation order) is part of the cache key, ensuring consistent results when repeating the same sequence.

## Installation

```bash
pip install touchfs

# Set up your OpenAI API key
export OPENAI_API_KEY="your-api-key-here"
```

## Documentation

- [Architecture & Technical Details](docs/architecture.md)
- [Plugin System](touchfs/content/plugins/README.md)
- [Example Projects](examples/README.md)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
