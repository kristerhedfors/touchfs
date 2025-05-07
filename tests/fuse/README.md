# FUSE Testing for TouchFS

This directory contains files for testing FUSE (Filesystem in Userspace) functionality with TouchFS in a devcontainer environment.

## Contents

- **hello_fuse.c**: A simple FUSE filesystem example that creates a read-only file with "Hello World from FUSE!" content
- **hello_fuse**: The compiled binary of hello_fuse.c
- **test_fuse.sh**: A script to test FUSE functionality in the devcontainer

## How to Use

To test FUSE functionality in the devcontainer, run:

```bash
./test_fuse.sh
```

This script will:
- Check if the FUSE device exists
- Compile the hello_fuse.c example
- Mount a simple FUSE filesystem at /tmp/fuse_mount
- Test if the filesystem is working correctly
- Clean up after the test

## Related Documentation

For detailed information about FUSE setup for TouchFS, see the [FUSE Setup documentation](../../docs/FUSE_SETUP.md).
