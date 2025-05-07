# FUSE-enabled Devcontainer

This devcontainer configuration has been updated to support FUSE (Filesystem in Userspace) development. The configuration includes:

1. A custom Dockerfile that installs the necessary FUSE packages
2. Container settings that allow FUSE to work properly within the devcontainer

## Changes Made

1. Created a custom Dockerfile that:
   - Installs the `fuse` and `libfuse-dev` packages
   - Creates the `/dev/fuse` device if it doesn't exist
   - Adds the `fuse` kernel module to the modules list

2. Updated the devcontainer.json to:
   - Use the custom Dockerfile instead of the pre-built image
   - Add the necessary container arguments to support FUSE:
     - `--cap-add=SYS_ADMIN`: Grants the container the capability to mount filesystems
     - `--device=/dev/fuse`: Exposes the host's FUSE device to the container
     - `--security-opt=apparmor:unconfined`: Disables AppArmor restrictions that might prevent FUSE from working

## How to Use

To use this updated configuration:

1. Rebuild the devcontainer:
   - In VS Code, press F1 and select "Dev Containers: Rebuild Container"
   - Or close VS Code and reopen the project, which will prompt you to rebuild the container

2. After the container is rebuilt, you should be able to use FUSE within the devcontainer.

## Testing FUSE

You can test that FUSE is working by compiling and running the `hello_fuse.c` example:

```bash
# Compile the example
gcc -Wall hello_fuse.c `pkg-config fuse --cflags --libs` -o hello_fuse

# Create a mount point
mkdir -p /tmp/fuse_mount

# Run the FUSE filesystem (use -f to keep it in the foreground)
./hello_fuse /tmp/fuse_mount -f
```

In another terminal, you can verify it's working:

```bash
# List the contents of the mount point
ls -la /tmp/fuse_mount

# Read the hello file
cat /tmp/fuse_mount/hello
```

## Troubleshooting

If you encounter issues with FUSE in the devcontainer:

1. Ensure the container has been rebuilt with the new configuration
2. Check if the FUSE device is available: `ls -la /dev/fuse`
3. Verify the FUSE module is loaded: `lsmod | grep fuse`
4. Check if you have the necessary permissions: `fusermount -V`

If problems persist, you may need to adjust the container settings or install additional packages.
