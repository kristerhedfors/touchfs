# Kitten Image Generator Example

A simple example demonstrating how to use TouchFS with the image plugin to generate kitten images from text prompts.

## How It Works

1. Clean up any existing workspace
2. Mount TouchFS in a fresh workspace directory
3. Create a PNG file with a text prompt describing the desired kitten image
4. The image plugin automatically generates the image based on the file's content
5. Clean up the workspace when done

## Usage

1. Open `kitten_image.ipynb` in Jupyter
2. Run each cell in sequence to:
   - Clean up any existing workspace
   - Create and mount a fresh workspace
   - Generate a kitten image
   - Display the result
   - Clean up the workspace

The example uses simple filesystem operations (echo) to trigger image generation through TouchFS.
