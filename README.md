# 🌳 TouchFS - A New Philosophy in File Generation

TouchFS represents a fundamental shift in how we think about file generation and project structure. At its core lies a simple yet powerful idea: files are not just static containers of content, but nodes in a dynamic, evolving system where each file's content is influenced by its position in the filesystem hierarchy and the contents of its siblings.

## The Core Idea

Consider this elegant formula for file generation:

```bash
touch $(cat filesystem.txt)
```

This simple command encapsulates the essence of TouchFS - each file listed in filesystem.txt is generated not only with its own prompt and position in the filesystem, but with awareness of all contents in other files generated up until that point. The order of generation becomes a crucial part of the system's evolution.

This creates a peculiar domain-specific language where the ordering of files in the list forms the core of the project's evolution over a sequence of generation steps. For each model and problem domain, there exists an optimal path through this sequential generation. While it might seem logical to start with a README.md, in some cases starting with a core fundamental idea as an embryo in code results in a completely different type of project when fully generated.

## Integration Philosophy

A fundamentally clean and integrated architecture allows for seamless utilization by all available tools in that domain. Instead of integrating individual tools, TouchFS integrates at the layer in which the tools exist - in this case, the filesystem itself, as most tools are files operating with and on other files.

## Quick Examples

1. Create a Python project structure:
```bash
# Mount a new filesystem
touchfs_mount ~/python_project --prompt "Create a modern Python project with tests and CI"

# Initial structure files are pre-tagged
cat src/main.py        # Generates and shows content
cat tests/test_main.py # Generates and shows content

# New files need touch to tag them
touch src/utils.py     # Creates and tags new file
cat src/utils.py      # Generates and shows content
```

2. Generate some images:
```bash
# Mount a new filesystem for an art project
touchfs_mount ~/art_gallery --prompt "Create an art gallery structure"

# Generate a landscape image
touch mountain_sunset.jpg    # Creates and tags new image file
cat mountain_sunset.jpg      # Generates image using filename as prompt

# Use a custom prompt for more control
echo "A serene mountain lake at sunset" > .touchfs/prompt
touch lake_reflection.png
cat lake_reflection.png      # Generates image using custom prompt
```

## Installation

```bash
pip install touchfs

# Set up your OpenAI API key
export OPENAI_API_KEY="your-api-key-here"
```

## Documentation

- [Architecture & Technical Details](docs/architecture.md)
- [Plugin System](touchfs/content/plugins/README.md)
- [Image Generation](touchfs/image/README.md)
- [Example Projects](examples/README.md)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
