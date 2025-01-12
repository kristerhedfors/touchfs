# TouchFS 👇 - The Swiss Army Knife of Synthetic Data Generation 🔧

> _The Touch Screen of File Systems_ ✨

Just as touch screens revolutionized user interfaces by making buttons context-aware within apps, TouchFS brings that same revolution to the filesystem level. While the native touch command integration is just one plugin in TouchFS's extensible system, it demonstrates the power of context-aware file generation - touch a file, and watch as it materializes with perfect context awareness! 🪄 Whether you need test data, training sets, or synthetic content, TouchFS's plugin system means any event can spark the creation of anything imaginable! This fundamental pattern is now published, unpatentable, and freely available under the MIT license.

## The Power of Touch ⚡

```bash
# Mount your magical filesystem
touchfs mount workspace -F "Create a modern web application"

# Want docs? Just touch them! 📚
touch workspace/README.md      # After generation, edit this to precisely reflect your intentions
touch workspace/docs/api.md    # Edit generated docs to match your specific requirements

# Need code? Touch brings it to life! 💻 (Generated code will align with your edited docs)
touch workspace/src/app.py
touch workspace/tests/test_app.py
```

## Magical Examples 🎩

### Time Travel to Windows 3.11 🕰️

```bash
# Create a nostalgic DOS environment
touchfs mount workspace -F "Create a Windows 3.11 style system"

touch workspace/AUTOEXEC.BAT    # Classic startup configuration
touch workspace/CONFIG.SYS      # System configuration
touch workspace/WIN.INI         # Windows initialization
touch workspace/SYSTEM.INI      # System settings
```

### Modern Async API Project 🚀

```bash
# Launch a modern backend project
touchfs mount workspace \
  -F "Create a FastAPI project with async endpoints" \
  -p "Write clean, modern Python with type hints"

touch workspace/app.py          # FastAPI application
touch workspace/models/user.py  # Pydantic models
touch workspace/routers/auth.py # Auth endpoints
touch workspace/tests/test_api.py
```

### AI Blog with Images 🎨

```bash
# Create an AI-powered blog
touchfs mount workspace \
  -F "Create a markdown blog about AI" \
  -p "Write engaging tech content with DALL-E images"

touch workspace/posts/future-of-ai.md      # Blog post
touch workspace/images/ai-future.jpg       # DALL-E generates futuristic image
touch workspace/templates/blog-layout.html  # Blog template
```

### Synthetic Data Generation 📊

#### Zero-Shot: E-commerce Data

```bash
# Mount filesystem for e-commerce data generation
touchfs mount workspace \
  -F "Create an e-commerce dataset" \
  -p "Generate realistic product and user data"

# Generate data without examples
touch workspace/products.json    # Infers structure from scratch
touch workspace/users.json       # Learns from common patterns
```

#### One-Shot: IoT Sensor Data

```bash
# Mount filesystem for IoT data generation
touchfs mount workspace \
  -F "Create IoT sensor readings" \
  -p "Generate realistic temperature data"

# Add one example temperature reading
echo '{
  "timestamp": "2024-01-01T00:00:00Z",
  "sensor_id": "TEMP001",
  "value": 22.5,
  "unit": "celsius",
  "battery": 98
}' > workspace/example.json

# Generate more readings following the pattern
touch workspace/sensor_1.json  # Follows example format
touch workspace/sensor_2.json  # Maintains consistency
```

#### Few-Shot: Medical Records

```bash
# Mount filesystem for medical records
touchfs mount workspace \
  -F "Create anonymized medical records" \
  -p "Generate HIPAA-compliant patient data"

# Add a few example records
echo 'patient_id,age,gender,condition
P001,45,F,hypertension
P002,62,M,diabetes' > workspace/patients_example.csv

echo 'patient_id,medication,dosage,frequency
P001,lisinopril,10mg,daily
P002,metformin,500mg,twice daily' > workspace/medications_example.csv

# Generate more records following patterns
touch workspace/new_patients.csv     # Learns from examples
touch workspace/new_medications.csv  # Maintains relationships
```

#### Many-Shot: Financial Transactions

```bash
# Mount filesystem for financial data
touchfs mount workspace \
  -F "Create financial transaction data" \
  -p "Generate realistic spending patterns"

# Import historical transaction dataset
echo '[
  {"date": "2024-01-01", "amount": 42.50, "category": "groceries"},
  {"date": "2024-01-01", "amount": 4.00, "category": "coffee"},
  {"date": "2024-01-02", "amount": 35.00, "category": "transport"},
  {"date": "2024-01-02", "amount": 12.99, "category": "subscription"}
]' > workspace/january.json

# Generate new transactions with learned patterns
touch workspace/february.json  # Follows spending patterns
touch workspace/march.json     # Maintains categories
touch workspace/anomalies.json # Flags unusual transactions
```

### Library-Guided Development 📚

#### FastAPI Project with SQLAlchemy

```bash
# Mount filesystem for FastAPI development
touchfs mount workspace \
  -F "Create a FastAPI CRUD API with SQLAlchemy" \
  -p "Follow FastAPI and SQLAlchemy best practices"

# Add framework documentation (after generation, edit docs to match your specific requirements)
curl https://fastapi.tiangolo.com/tutorial/sql-databases/ > workspace/fastapi_guide.md
curl https://docs.sqlalchemy.org/en/20/orm/quickstart.html > workspace/sqlalchemy_guide.md

# Generate code using your customized documentation context
touch workspace/models.py      # SQLAlchemy models following docs
touch workspace/database.py    # DB setup using recommended patterns
touch workspace/crud.py        # CRUD operations following examples
touch workspace/main.py        # FastAPI app with proper structure
```

#### React Component Library

```bash
# Mount filesystem for React development
touchfs mount workspace \
  -F "Create a React component library" \
  -p "Follow Material-UI patterns with Storybook docs"

# Add UI library documentation (after generation, edit docs to match your specific requirements)
curl https://mui.com/components/buttons/ > workspace/mui_guide.md
curl https://storybook.js.org/docs/react/writing-stories/introduction > workspace/storybook_guide.md

# Generate components using your customized documentation context
touch workspace/Button.tsx         # Component following MUI patterns
touch workspace/Button.test.tsx    # Tests using MUI testing guides
touch workspace/Button.stories.tsx # Storybook following examples
```

#### GraphQL API with Apollo

```bash
# Mount filesystem for GraphQL development
touchfs mount workspace \
  -F "Create a GraphQL API with Apollo" \
  -p "Follow Apollo best practices"

# Add Apollo documentation (after generation, edit docs to match your specific requirements)
curl https://www.apollographql.com/docs/apollo-server/getting-started/ > workspace/apollo_server.md
curl https://www.apollographql.com/docs/react/get-started/ > workspace/apollo_client.md

# Generate GraphQL project using your customized documentation context
touch workspace/schema.graphql  # Schema following conventions
touch workspace/resolvers.ts    # Resolvers using Apollo patterns
touch workspace/client.ts       # Client setup with proper caching
```

## Technical Implementation

While this implementation uses command interception, the core concept is UI-agnostic. Just as a touch screen can present context-aware buttons in an app, a filesystem can present context-aware files. The current CLI implementation:

1. Intercepts the `touch` command (this could just as well be a touch screen interface where filenames are selected or entered)
2. Interprets the target paths (whether from CLI arguments or UI selection)
3. Flags the targeted files with an extended attribute `generate_content=True`

The beauty of this pattern is that it's not tied to any specific interface. The same context-aware generation could be triggered through:

- CLI commands (current implementation)
- Touch screen interfaces
- File manager GUIs
- IDE plugins
- Mobile apps

## How It Works

The order in which you create files affects their generated content. Each unique context (including generation order) produces different content, which is automatically cached. For best results, it's recommended to create your README.md first to establish the project's high-level goals and structure, then proceed with implementation files that will align with those intentions:

```bash
# Mount with a project prompt (uses GPT to understand and generate text content)
touchfs mount workspace --prompt "Create a web scraping tool"

# When done, unmount the filesystem
touchfs mount -u workspace

# Scenario 1: README first, then app
touch workspace/README.md
touch workspace/app.py

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
rm workspace/README.md workspace/app.py  # Clear previous files
touch workspace/app.py
touch workspace/README.md

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
cat > workspace/files.txt << EOF
src/models.py
src/database.py
src/api.py
tests/test_models.py
tests/test_api.py
README.md
EOF

# Create necessary directories
mkdir -p workspace/src workspace/tests

# Generate files in sequence
while read -r file; do
  touch "workspace/$file"
done < workspace/files.txt

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
touchfs mount workspace --prompt "Create concept art for a sci-fi game"

# When finished, unmount the filesystem
touchfs mount -u workspace

# Generate images in sequence
touch workspace/character.jpg     # DALL-E 3 generates based on filename and project context
touch workspace/background.jpg    # Uses context from character.jpg to maintain visual style
touch workspace/character_in_background.jpg  # Combines context from both previous images
```

Each image is generated with awareness of previously generated images and surrounding files, with DALL-E 3 using this rich context to maintain consistent style, theme, and visual coherence across the project. This context-aware generation ensures that each new image naturally fits within the established visual language of the project.

In Scenario 1 above, the README is generated first, establishing high-level concepts that influence the app's implementation. In Scenario 2, the app is generated first, making concrete implementation choices that the README then documents. Each scenario's unique context (including generation order) is part of the cache key, ensuring consistent results when repeating the same sequence.

## Overlay Mount Mode

TouchFS can be mounted in overlay mode, where it acts as a writable layer on top of an existing directory:

```bash
# Mount TouchFS in overlay mode on top of an existing project
touchfs mount workspace --overlay ~/existing-project

# The mount point now shows:
# 1. All files from ~/existing-project (read-only)
# 2. Any new files you create (writable TouchFS layer)
# 3. Both layers merged into a single view

# Example: Generate new test files alongside existing code
ls ~/existing-project
# src/
#   app.py
#   models.py

touch workspace/tests/test_app.py
touch workspace/tests/test_models.py

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
#          Merged view in workspace
#                shows both layers

# When done, unmount as usual
touchfs mount -u workspace
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

### Prerequisites

TouchFS has the following prerequisites for installation and operation:

#### Platform Support & libfuse

TouchFS currently only supports Linux systems. While macOS support might be possible with macFUSE in the future, this integration has not been implemented yet.

Required dependencies:

- **Linux (Supported):**
  ```bash
  # Ubuntu/Debian:
  sudo apt update
  sudo apt install libfuse2
  ```

- **Windows (via WSL2):**
  Windows users can run TouchFS through WSL2 (Windows Subsystem for Linux). Install a Linux distribution in WSL2 and follow the Linux installation instructions above.

- **macOS (Not Currently Supported):**
  While macOS support via macFUSE may be possible in the future, it is not currently implemented or supported.

## CLI Commands

### Mount Command

The `touchfs mount` command mounts a TouchFS filesystem at a specified directory:

```bash
# Basic mount with empty filesystem
touchfs mount workspace

# Mount with default content generation prompt
# This affects what content is generated when files are touched
touchfs mount workspace -p "Create a modern web application"

# Mount with filesystem generation prompt
# This generates an initial filesystem structure before mounting
touchfs mount workspace -F "Create a project structure for a FastAPI backend with tests"

# Mount with both prompts
# First generates structure, then uses content prompt for new files
touchfs mount workspace \
  -F "Create a React frontend project structure" \
  -p "Write modern React components with TypeScript"

# Mount in foreground mode with debug output
touchfs mount workspace -f

# Mount with overlay on existing directory
touchfs mount workspace --overlay ./existing-project

# List currently mounted TouchFS filesystems
touchfs mount
```

Key options:

- `-p, --prompt`: Set default prompt for content generation when files are touched
- `-F, --filesystem-generation-prompt`: Generate initial filesystem structure before mounting
- `-f, --foreground`: Run in foreground with debug output to stdout
- `--overlay`: Mount on top of existing directory, merging contents
- `--allow-other`: Allow other users to access the mount
- `--allow-root`: Allow root to access the mount
- `--nothreads`: Disable multi-threading
- `--nonempty`: Allow mounting over non-empty directory

### Umount Command

The `touchfs umount` command unmounts a TouchFS filesystem:

```bash
# Basic unmount
touchfs umount workspace

# Force unmount if busy
touchfs umount workspace --force
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
