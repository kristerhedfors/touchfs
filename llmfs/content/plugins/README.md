# 🔌 LLMFS Plugins Guide

Welcome to the LLMFS plugins guide! This document will help you understand and work with the special files in your `.llmfs` directory that make your filesystem smart and customizable.

## 📝 Content Generation Behavior

LLMFS generates content only under specific conditions to ensure safety and predictability:

1. **Generation Requirements**
   - File must be marked with `generate_content` extended attribute (xattr)
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
      setfattr -n user.generate_content -v true myfile.txt
      ```
      This can be useful if touch behavior isn't working as expected.

3. **Safety Features**
   - Never overwrites existing content
   - Generation only occurs for empty files
   - Clear separation between marked and unmarked files

## 🎯 What Can You Do With Plugins?

### 1. Customize File Generation
The `.llmfs` directory contains files that let you control how content is generated:

```bash
# Use a specific AI model (must support structured output)
echo "gpt-4o-2024-08-06" > .llmfs/model.default

# Customize generation prompts
echo "Write secure, well-documented code" > .llmfs/prompt.default

# Set different prompts for different directories
echo "Focus on performance" > src/.llmfs/prompt
echo "Include detailed tests" > tests/.llmfs/prompt
```

### 2. Monitor Your Filesystem
Keep track of what's happening in your filesystem:

```bash
# View the current structure
cat .llmfs/tree

# Read auto-generated documentation
cat .llmfs/README

# Monitor system logs
tail -f .llmfs/log
```

### 3. Optimize Performance
Control caching to speed up repeated operations:

```bash
# Enable caching
echo 1 > .llmfs/cache_enabled

# Watch cache performance
watch -n1 cat .llmfs/cache_stats

# Clear the cache if needed
echo 1 > .llmfs/cache_clear

# See what's in the cache
cat .llmfs/cache_list
```

## 📁 Special Files Explained

### In Your Root Directory

`.llmfs/model.default`
- Sets the AI model for content generation
- Must use models that support structured output (e.g., gpt-4o-2024-08-06)
- Example: `echo "gpt-4o-2024-08-06" > .llmfs/model.default`

`.llmfs/prompt.default`
- Controls how content is generated
- Can include specific guidelines or requirements
- Example: `echo "Include error handling in all functions" > .llmfs/prompt.default`

`.llmfs/README`
- Auto-generated documentation about your filesystem
- Updates automatically as files change
- Example: `cat .llmfs/README`

`.llmfs/tree`
- Shows your filesystem structure
- Includes file types and generation status
- Example: `cat .llmfs/tree`

`.llmfs/log`
- Real-time system logs
- Helpful for debugging
- Example: `tail -f .llmfs/log`

### Cache Control Files

`.llmfs/cache_enabled`
- Turn caching on (1) or off (0)
- Helps speed up repeated operations
- Example: `echo 1 > .llmfs/cache_enabled`

`.llmfs/cache_stats`
- Shows cache performance metrics
- Includes hits, misses, and size
- Example: `cat .llmfs/cache_stats`

`.llmfs/cache_clear`
- Write 1 to clear the cache
- Useful when you want fresh content
- Example: `echo 1 > .llmfs/cache_clear`

`.llmfs/cache_list`
- Lists all cached content
- Shows what's been generated before
- Example: `cat .llmfs/cache_list`

## 🎨 Customization Patterns

### Directory-Specific Settings
You can customize settings for different parts of your project using dot files:

```
project/
├── .llmfs/
│   ├── model.default  # Global fallback settings
│   └── prompt.default
├── .llmfs.prompt     # Project-wide prompt
├── .llmfs.model      # Project-wide model
├── src/
│   └── .llmfs.prompt # Source code specific prompt
├── tests/
│   └── .prompt       # Test specific prompt (alternative style)
└── docs/
    └── .model        # Docs specific model (alternative style)
```

Settings cascade down directories in this order:
1. Check current directory for .llmfs.prompt/.llmfs.model
2. If not found, check for .prompt/.model
3. If not found, check parent directory (same order)
4. Finally, use .llmfs/prompt.default or .llmfs/model.default

### Real-Time Monitoring
Keep an eye on your filesystem:

```bash
# Split terminal view for monitoring
tmux new-session \; \
  split-window -h 'watch -n1 cat .llmfs/cache_stats' \; \
  split-window -v 'tail -f .llmfs/log'
```

## 💡 Tips and Tricks

1. **Faster Development**
   ```bash
   # Enable caching at the start of your session
   echo 1 > .llmfs/cache_enabled
   
   # Monitor performance
   watch -n1 cat .llmfs/cache_stats
   ```

2. **Custom Prompts**
   ```bash
   # Create a prompt template
   cat > .llmfs/prompt.default << EOF
   Focus on:
   - Clean code principles
   - Comprehensive error handling
   - Clear documentation
   EOF
   ```

3. **Debugging**
   ```bash
   # Watch logs in real-time
   tail -f .llmfs/log
   
   # Check cache status
   cat .llmfs/cache_stats
   ```

## 🤝 Contributing

Want to create your own plugin? Check out our [Developer Guide](CONTRIBUTING.md) for technical details.
