"""Extended attribute (xattr) definitions for TouchFS."""

# Prefix for all TouchFS xattrs
TOUCHFS_PREFIX = "touchfs."

# Core xattrs
GENERATE_CONTENT = f"{TOUCHFS_PREFIX}generate_content"  # Mark file for content generation
GENERATOR = f"{TOUCHFS_PREFIX}generator"  # Generator plugin to use
CLI_CONTEXT = f"{TOUCHFS_PREFIX}cli_context"  # Space-separated list of files created together via touch
