#!/bin/bash
# Script to test FUSE functionality in the devcontainer

set -e  # Exit on error

echo "Testing FUSE functionality in the devcontainer..."

# Check if /dev/fuse exists
if [ ! -e /dev/fuse ]; then
    echo "ERROR: /dev/fuse device not found!"
    echo "The devcontainer may not be properly configured for FUSE."
    echo "Please rebuild the devcontainer using the updated configuration."
    exit 1
fi

echo "FUSE device found: $(ls -la /dev/fuse)"

# Check if fusermount is available
if command -v fusermount &> /dev/null; then
    echo "fusermount is available: $(which fusermount)"
    echo "fusermount version: $(fusermount -V)"
else
    echo "WARNING: fusermount command not found!"
fi

# Compile the hello_fuse example
echo "Compiling hello_fuse.c..."
gcc -Wall hello_fuse.c $(pkg-config fuse --cflags --libs) -o hello_fuse
echo "Compilation successful!"

# Create mount point
echo "Creating mount point at /tmp/fuse_mount..."
mkdir -p /tmp/fuse_mount

# Check if any process is using the mount point
if mount | grep -q "/tmp/fuse_mount"; then
    echo "Unmounting existing filesystem from /tmp/fuse_mount..."
    fusermount -u /tmp/fuse_mount || sudo umount -f /tmp/fuse_mount
fi

# Run the FUSE filesystem in the background
echo "Mounting FUSE filesystem at /tmp/fuse_mount..."
./hello_fuse /tmp/fuse_mount &
FUSE_PID=$!

# Give it a moment to mount
sleep 2

# Test if the mount worked
echo "Testing the mounted filesystem..."
if [ -f /tmp/fuse_mount/hello ]; then
    echo "SUCCESS: FUSE filesystem mounted successfully!"
    echo "Contents of /tmp/fuse_mount/hello:"
    cat /tmp/fuse_mount/hello
else
    echo "ERROR: Failed to mount FUSE filesystem or 'hello' file not found!"
    echo "Mount point contents:"
    ls -la /tmp/fuse_mount
fi

# Clean up
echo "Cleaning up..."
fusermount -u /tmp/fuse_mount || sudo umount -f /tmp/fuse_mount
kill $FUSE_PID 2>/dev/null || true

echo "FUSE test completed."
