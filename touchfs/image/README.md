# LLMFS Image Generator

This directory demonstrates how to use the LLMFS image generator plugin, which uses OpenAI's DALL-E API to generate images on demand.

## Setup

1. Ensure you have an OpenAI API key set in your environment:
```bash
export OPENAI_API_KEY=your_api_key_here
```

2. Mount the filesystem:
```bash
python -m touchfs mount /path/to/mount/point
```

## Usage

### Basic Usage

Simply create an empty image file with a descriptive name, and the generator will create an image based on the filename:

```bash
# The filename will be used as the prompt
touch sunset_over_mountains.jpg

# Creates a PNG instead
touch northern_lights.png
```

### Using Prompt Files

For more control over image generation, create a `.prompt` file in the same directory:

```bash
# Create a prompt file
echo "A stunning aurora borealis with vibrant greens and purples dancing across a starlit sky" > .prompt

# Any image files in this directory will use this prompt
touch aurora.jpg
```

### Supported File Types

- `.jpg`/`.jpeg`
- `.png`

### Image Settings

The generator uses these default settings:
- Model: DALL-E 3
- Size: 1024x1024 (square images are fastest to generate)
- Quality: Standard

## Examples

1. Basic filename-based generation:
```bash
touch mountain_lake_reflection.jpg
```

2. Using a prompt file:
```bash
# Create directory for nature scenes
mkdir nature
cd nature

# Create prompt file
echo "A serene mountain lake at sunrise, with perfect reflections of snow-capped peaks in crystal clear water" > .prompt

# Generate multiple images using the same prompt
touch lake_morning.jpg
touch lake_sunset.jpg
```

## Notes

- Image generation may take a few seconds
- Each image generation counts towards your OpenAI API usage
- The generator automatically prevents DALL-E from adding extra details to your prompts
- Images are generated at 1024x1024 resolution for optimal performance
