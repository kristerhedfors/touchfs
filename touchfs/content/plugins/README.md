# 🔌 TouchFS Plugins Guide

Welcome to the TouchFS plugins guide! This document will help you understand how to customize your filesystem's behavior using prompt and model files.

## 📝 Content Generation Behavior

TouchFS generates content only under specific conditions to ensure safety and predictability:

1. **Generation Requirements**
   - File must be marked with `touchfs.generate_content` extended attribute (xattr)
   - File must be empty (0 bytes)
   - Generation is triggered during size calculation (stat operations)

2. **File Marking Methods**
   a. **Initial Structure Files**
      - Automatically marked during filesystem mount
      - Created empty and ready for generation
      - No explicit touch needed
   
   b. **New Files (Recommended Method)**
      ```bash
      # Create and mark a new file
      touch myfile.txt
      
      # Or mark multiple files at once
      touch file1.txt file2.py file3.md
      ```
   
   c. **Advanced Usage (Under the Hood)**
      The touch command is actually setting extended attributes. If needed, you can use setfattr directly:
      ```bash
      # What touch does internally
      setfattr -n touchfs.generate_content -v true myfile.txt
      ```
      This can be useful if touch behavior isn't working as expected.

3. **Safety Features**
   - Never overwrites existing content
   - Generation only occurs for empty files
   - Clear separation between marked and unmarked files

## 🎯 What Can You Do With Plugins?

### 1. Customize File Generation
You can control how content is generated using .prompt and .model files:

```bash
# Use a specific AI model (must support structured output)
echo "gpt-4o-2024-08-06" > .model

# Customize generation prompts
echo "Write secure, well-documented code" > .prompt

# Set different prompts for different directories
cd src && echo "Focus on performance" > .prompt
cd ../tests && echo "Include detailed tests" > .prompt
```

### 2. Monitor Your Filesystem
Keep track of what's happening in your filesystem using the read-only .touchfs directory:

```bash
# View the current structure
cat .touchfs/tree

# Read auto-generated documentation
cat .touchfs/README

# Monitor system logs
tail -f .touchfs/log
```

### 3. Generate Images
TouchFS can generate images using OpenAI's DALL-E API. You can control image generation through prompt files at different levels:

```bash
# Project-wide prompt for all images
echo "Use vibrant colors and dramatic lighting" > .prompt

# Directory-specific prompts
mkdir landscapes
cd landscapes
echo "Focus on natural scenery with mountains and water" > .prompt
touch sunset.jpg     # Uses directory prompt

# File-specific prompts
mkdir portraits
cd portraits
echo "Professional headshot style with neutral background" > .prompt
touch ceo.jpg        # Uses portraits/.prompt

# Override for specific image
echo "A confident business leader in a modern office setting" > ceo.prompt
touch ceo2.jpg       # Uses ceo.prompt
```

Basic usage examples:

```bash
# Create an image of a cat
touch cat_in_window.jpg  # Supports .jpg, .jpeg, and .png
cat cat_in_window.jpg    # Generates and displays image

# Use a custom prompt
echo "A serene mountain landscape at sunset" > .prompt
touch mountain_view.png
cat mountain_view.png    # Generates landscape using custom prompt

# Configure image generation
echo "dall-e-3" > .model  # Change model (default: dall-e-3)
```

Key features:
- Supports common image formats (.jpg, .jpeg, .png)
- Smart prompt generation from filenames
- Uses filesystem context for relevance
- Configurable via .model files
- Standard quality mode and 1024x1024 size for optimal generation

### 4. Monitor Cache Performance
You can monitor cache performance through the read-only .touchfs directory:

```bash
# Watch cache performance
watch -n1 cat .touchfs/cache_stats

# See what's in the cache
cat .touchfs/cache_list
```

## 📁 Special Files Explained

### In Your Working Directory

`.prompt`
- Controls how content is generated
- Can include specific guidelines or requirements
- Example: `echo "Include error handling in all functions" > .prompt`

`.model`
- Sets the AI model for content generation
- Must use models that support structured output (e.g., gpt-4o-2024-08-06)
- Example: `echo "gpt-4o-2024-08-06" > .model`

### Read-only Files in .touchfs Directory

`.touchfs/README`
- Auto-generated documentation about your filesystem
- Updates automatically as files change
- Example: `cat .touchfs/README`

`.touchfs/tree`
- Shows your filesystem structure
- Includes file types and generation status
- Example: `cat .touchfs/tree`

`.touchfs/log`
- Real-time system logs
- Helpful for debugging
- Example: `tail -f .touchfs/log`

`.touchfs/cache_stats`
- Shows cache performance metrics
- Includes hits, misses, and size
- Example: `cat .touchfs/cache_stats`

`.touchfs/cache_list`
- Lists all cached content
- Shows what's been generated before
- Example: `cat .touchfs/cache_list`

## 🎨 Customization Patterns

### Directory-Specific Settings
You can customize settings for different parts of your project using prompt and model files:

```
project/
├── .prompt          # Project-wide prompt
├── .model           # Project-wide model
├── src/
│   └── .prompt      # Source code specific prompt
├── tests/
│   └── .prompt      # Test specific prompt
└── docs/
    └── .model       # Docs specific model
```

Settings cascade down directories in this order:
1. Check current directory for .prompt/.model
2. If not found, check parent directory
3. If not found, use system defaults

### Real-Time Monitoring
Keep an eye on your filesystem:

```bash
# Split terminal view for monitoring
tmux new-session \; \
  split-window -h 'watch -n1 cat .touchfs/cache_stats' \; \
  split-window -v 'tail -f .touchfs/log'
```

## 💡 Tips and Tricks

1. **Custom Prompts**
   ```bash
   # Create a prompt template
   cat > .prompt << EOF
   Focus on:
   - Clean code principles
   - Comprehensive error handling
   - Clear documentation
   EOF
   ```

2. **Debugging**
   ```bash
   # Watch logs in real-time
   tail -f .touchfs/log
   
   # Check cache status
   cat .touchfs/cache_stats
   ```

## 🤝 Contributing

Want to create your own plugin? Check out our [Developer Guide](CONTRIBUTING.md) for technical details.
