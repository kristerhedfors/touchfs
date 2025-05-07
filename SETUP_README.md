# TouchFS Setup in Devcontainer

This document explains how to set up and use TouchFS in a devcontainer environment.

## Automatic Setup

The devcontainer is configured to automatically run the setup script when the container is created or started. This script:

1. Checks for FUSE dependencies and device availability
2. Installs Python dependencies for TouchFS
3. Tests FUSE functionality
4. Sets up a TouchFS test environment
5. Creates a sample .env file for configuration

## Manual Setup

If you need to run the setup script manually, you can do so with:

```bash
./setup_touchfs.sh
```

## Using TouchFS

After the setup is complete, you can use TouchFS as follows:

1. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

2. Mount a TouchFS filesystem:
   ```bash
   touchfs mount workspace
   ```

3. Create files with content:
   ```bash
   touch workspace/README.md
   ```

4. Unmount when done:
   ```bash
   touchfs umount workspace
   ```

## Configuration

TouchFS can be configured using environment variables or a `.env` file. The setup script creates a sample `.env` file with common configuration options:

```
# TouchFS Configuration
# Uncomment and set your OpenAI API key
# OPENAI_API_KEY=your-api-key-here

# Default model to use (gpt-4o is recommended for best results)
TOUCHFS_DEFAULT_MODEL=gpt-4o

# Cache directory (defaults to ~/.cache/touchfs)
# TOUCHFS_CACHE_DIR=~/.cache/touchfs

# Log level (DEBUG, INFO, WARNING, ERROR)
TOUCHFS_LOG_LEVEL=INFO
```

## Troubleshooting

If you encounter issues with TouchFS:

1. Check if FUSE is working correctly:
   ```bash
   ls -la /dev/fuse
   fusermount -V
   ```

2. Verify that the OpenAI API key is set:
   ```bash
   echo $OPENAI_API_KEY
   ```

3. Run the setup script again to reinstall dependencies:
   ```bash
   ./setup_touchfs.sh
   ```

4. Check the TouchFS logs for errors:
   ```bash
   export TOUCHFS_LOG_LEVEL=DEBUG
   touchfs mount workspace -f  # Run in foreground with debug output
   ```

## Additional Resources

- [TouchFS Documentation](https://github.com/kristerhedfors/touchfs)
- [FUSE Setup Guide](FUSE_SETUP.md)
