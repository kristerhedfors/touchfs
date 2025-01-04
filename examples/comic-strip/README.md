# Comic Strip Generator Example

This example demonstrates using TouchFS to generate a comic strip by creating a markdown file that references image files. When the image files are touched, they are generated based on the context from the markdown file.

## Usage

1. Create workspace:
```bash
mkdir workspace
```

2. Mount TouchFS:
```bash
touchfs mount workspace
```

3. Enter workspace:
```bash
cd workspace
```

4. Create the prompt file that defines how to generate comic strips:
```bash
touch .prompt
```

5. Create your comic strip markdown file:
```bash
touch comic.md
```

6. Generate the panel images:
```bash
# TouchFS will read the comic.md context to generate each panel
touch panel1.jpg
touch panel2.jpg
touch panel3.jpg
touch panel4.jpg
```

The comic strip markdown file (comic.md) provides the context for each panel, including:
- Scene descriptions
- Character dialogue
- Panel layout
- Visual style guidelines

When you touch the jpg files, TouchFS uses this context to generate images that match the descriptions and maintain visual consistency across panels.
