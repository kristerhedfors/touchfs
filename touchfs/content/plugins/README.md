# 🔌 TouchFS Plugins Guide

Welcome to the TouchFS plugins guide! This document will help you understand and work with the special files in your `.touchfs` directory that make your filesystem smart and customizable.

## 📝 Content Generation Behavior

TouchFS generates content only under specific conditions to ensure safety and predictability:

1. **Generation Requirements**
   - File must be marked with `generate_content` extended attribute (xattr)
   - File must be empty (0 bytes)
   - Generation is triggered during size calculation (stat operations)

2. **File Marking Methods**
   a. **Initial Structure Files**
      - Automatically marked during filesystem mount
      - Created empty and ready for generation
      - No explicit touch needed
   s 
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
      setfattr -n user.generate_content -v true myfile.txt
      ```
      This can be useful if touch behavior isn't working as expected.

3. **Safety Features**
   - Never overwrites existing content
   - Generation only occurs for empty files
   - Clear separation between marked and unmarked files

## 🎯 What Can You Do With Plugins?

### 1. Customize File Generation
The `.touchfs` directory contains files that let you control how content is generated:

```bash
# Use a specific AI model (must support structured output)
echo "gpt-4o-2024-08-06" > .touchfs/model.default

# Customize generation prompts
echo "Write secure, well-documented code" > .touchfs/prompt.default

# Set different prompts for different directories
echo "Focus on performance" > src/.touchfs/prompt
echo "Include detailed tests" > tests/.touchfs/prompt
```

### 2. Monitor Your Filesystem
Keep track of what's happening in your filesystem:

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
echo "Use vibrant colors and dramatic lighting" > .touchfs/prompt.default

# Directory-specific prompts
mkdir landscapes
echo "Focus on natural scenery with mountains and water" > landscapes/.prompt
cd landscapes
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
echo "A serene mountain landscape at sunset" > .touchfs/prompt
touch mountain_view.png
cat mountain_view.png    # Generates landscape using custom prompt

# Configure image generation
echo "dall-e-3" > .touchfs/model.default  # Change model (default: dall-e-3)
```

Key features:
- Supports common image formats (.jpg, .jpeg, .png)
- Smart prompt generation from filenames
- Uses filesystem context for relevance
- Configurable via model.default files
- Standard quality mode and 1024x1024 size for optimal generation

### 4. Optimize Performance
Control caching to speed up repeated operations:

```bash
# Enable caching
echo 1 > .touchfs/cache_enabled

# Watch cache performance
watch -n1 cat .touchfs/cache_stats

# Clear the cache if needed
echo 1 > .touchfs/cache_clear

# See what's in the cache
cat .touchfs/cache_list
```

## 📁 Special Files Explained

### In Your Root Directory

`.touchfs/model.default`
- Sets the AI model for content generation
- Must use models that support structured output (e.g., gpt-4o-2024-08-06)
- Example: `echo "gpt-4o-2024-08-06" > .touchfs/model.default`

`.touchfs/prompt.default`
- Controls how content is generated
- Can include specific guidelines or requirements
- Example: `echo "Include error handling in all functions" > .touchfs/prompt.default`

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

### Cache Control Files

`.touchfs/cache_enabled`
- Turn caching on (1) or off (0)
- Helps speed up repeated operations
- Example: `echo 1 > .touchfs/cache_enabled`

`.touchfs/cache_stats`
- Shows cache performance metrics
- Includes hits, misses, and size
- Example: `cat .touchfs/cache_stats`

`.touchfs/cache_clear`
- Write 1 to clear the cache
- Useful when you want fresh content
- Example: `echo 1 > .touchfs/cache_clear`

`.touchfs/cache_list`
- Lists all cached content
- Shows what's been generated before
- Example: `cat .touchfs/cache_list`

## 🎨 Customization Patterns

### Directory-Specific Settings
You can customize settings for different parts of your project using dot files:

```
project/
├── .touchfs/
│   ├── model.default  # Global fallback settings
│   └── prompt.default
├── .touchfs.prompt     # Project-wide prompt
├── .touchfs.model      # Project-wide model
├── src/
│   └── .touchfs.prompt # Source code specific prompt
├── tests/
│   └── .prompt       # Test specific prompt (alternative style)
└── docs/
    └── .model        # Docs specific model (alternative style)
```

Settings cascade down directories in this order:
1. Check current directory for .touchfs.prompt/.touchfs.model
2. If not found, check for .prompt/.model
3. If not found, check parent directory (same order)
4. Finally, use .touchfs/prompt.default or .touchfs/model.default

### Real-Time Monitoring
Keep an eye on your filesystem:

```bash
# Split terminal view for monitoring
tmux new-session \; \
  split-window -h 'watch -n1 cat .touchfs/cache_stats' \; \
  split-window -v 'tail -f .touchfs/log'
```

## 💡 Tips and Tricks

1. **Faster Development**
   ```bash
   # Enable caching at the start of your session
   echo 1 > .touchfs/cache_enabled
   
   # Monitor performance
   watch -n1 cat .touchfs/cache_stats
   ```

2. **Custom Prompts**
   ```bash
   # Create a prompt template
   cat > .touchfs/prompt.default << EOF
   Focus on:
   - Clean code principles
   - Comprehensive error handling
   - Clear documentation
   EOF
   ```

3. **Debugging**
   ```bash
   # Watch logs in real-time
   tail -f .touchfs/log
   
   # Check cache status
   cat .touchfs/cache_stats
   ```

## 🤝 Contributing

Want to create your own plugin? Check out our [Developer Guide](CONTRIBUTING.md) for technical details.
