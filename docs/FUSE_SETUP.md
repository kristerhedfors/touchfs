# FUSE Setup for TouchFS

This document explains the setup for using FUSE (Filesystem in Userspace) with the TouchFS project in a devcontainer environment.

## What is FUSE?

FUSE (Filesystem in Userspace) is a software interface for Unix and Unix-like computer operating systems that lets non-privileged users create their own file systems without editing kernel code. This is particularly useful for projects like TouchFS that need to create custom filesystems.

## Setup Overview

To enable FUSE support in the devcontainer, the following changes have been made:

1. **Custom Dockerfile** (`.devcontainer/Dockerfile`):
   - Installs the necessary FUSE packages (`fuse` and `libfuse-dev`)
   - Creates the `/dev/fuse` device if it doesn't exist
   - Adds the `fuse` kernel module to the modules list

2. **Updated devcontainer.json** (`.devcontainer/devcontainer.json`):
   - Uses the custom Dockerfile instead of the pre-built image
   - Adds the necessary container arguments to support FUSE:
     - `--cap-add=SYS_ADMIN`: Grants the container the capability to mount filesystems
     - `--device=/dev/fuse`: Exposes the host's FUSE device to the container
     - `--security-opt=apparmor:unconfined`: Disables AppArmor restrictions that might prevent FUSE from working

3. **Test Files**:
   - `hello_fuse.c`: A simple FUSE filesystem example that creates a read-only file
   - `test_fuse.sh`: A script to test FUSE functionality in the devcontainer

## How to Use

### Step 1: Rebuild the Devcontainer

To use the updated configuration, you need to rebuild the devcontainer:

1. In VS Code, press F1 and select "Dev Containers: Rebuild Container"
2. Or close VS Code and reopen the project, which will prompt you to rebuild the container

### Step 2: Test FUSE Functionality

After rebuilding the container, you can test FUSE functionality using the provided script:

```bash
./test_fuse.sh
```

This script will:
- Check if the FUSE device exists
- Compile the hello_fuse.c example
- Mount a simple FUSE filesystem
- Test if the filesystem is working correctly
- Clean up after the test

### Step 3: Use FUSE in Your Project

Once you've confirmed that FUSE is working, you can use it in your project:

1. Include the necessary FUSE headers:
   ```c
   #define FUSE_USE_VERSION 26
   #include <fuse.h>
   ```

2. Implement the required FUSE operations for your filesystem

3. Compile your code with the FUSE libraries:
   ```bash
   gcc -Wall your_file.c `pkg-config fuse --cflags --libs` -o your_program
   ```

4. Mount your filesystem:
   ```bash
   ./your_program /path/to/mount/point
   ```

## Troubleshooting

If you encounter issues with FUSE in the devcontainer:

1. Ensure the container has been rebuilt with the new configuration
2. Check if the FUSE device is available: `ls -la /dev/fuse`
3. Verify the FUSE module is loaded: `lsmod | grep fuse`
4. Check if you have the necessary permissions: `fusermount -V`

If problems persist, you may need to adjust the container settings or install additional packages.

## Additional Resources

- [FUSE Documentation](https://github.com/libfuse/libfuse)
- [FUSE Wiki](https://github.com/libfuse/libfuse/wiki)
- [Writing a FUSE Filesystem](https://www.cs.nmsu.edu/~pfeiffer/fuse-tutorial/)
