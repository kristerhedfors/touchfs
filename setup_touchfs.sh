#!/bin/bash
# setup_touchfs.sh - Setup script for TouchFS in devcontainer environment
# This script will run automatically when the devcontainer starts

set -e  # Exit on error

echo "=========================================================="
echo "TouchFS Setup Script"
echo "=========================================================="

# Function to print section headers
section() {
    echo ""
    echo "## $1"
    echo "-----------------------------------------------------------"
}

# Check if running in devcontainer
section "Checking environment"
if [ ! -f "/.dockerenv" ]; then
    echo "WARNING: This script is designed to run inside a devcontainer."
    echo "It may not work correctly in other environments."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for FUSE device
section "Checking FUSE setup"
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
    section "Installing fusermount"
    apt-get update && apt-get install -y fuse
fi

# Install Python dependencies
section "Installing Python dependencies"
pip install -e .
echo "Installed touchfs and dependencies"

# Test FUSE functionality
section "Testing FUSE functionality"
if [ -f "./hello_fuse.c" ]; then
    # Compile the hello_fuse example if it exists
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
else
    echo "hello_fuse.c not found, skipping FUSE test."
fi

# Create a test directory for TouchFS
section "Setting up TouchFS test environment"
mkdir -p /tmp/touchfs_test

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "WARNING: OPENAI_API_KEY environment variable is not set."
    echo "You will need to set this to use TouchFS with OpenAI models."
    echo "Example: export OPENAI_API_KEY=\"your-api-key-here\""
fi

# Create a sample .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating sample .env file..."
    cat > .env << EOF
# TouchFS Configuration
# Uncomment and set your OpenAI API key
# OPENAI_API_KEY=your-api-key-here

# Default model to use (gpt-4o is recommended for best results)
TOUCHFS_DEFAULT_MODEL=gpt-4o

# Cache directory (defaults to ~/.cache/touchfs)
# TOUCHFS_CACHE_DIR=~/.cache/touchfs

# Log level (DEBUG, INFO, WARNING, ERROR)
TOUCHFS_LOG_LEVEL=INFO
EOF
    echo "Created sample .env file. Please edit it to add your OpenAI API key."
fi

# Add touchfs alias to .bashrc if it doesn't exist
if ! grep -q "alias touchfs=" ~/.bashrc; then
    echo "Adding touchfs alias to ~/.bashrc..."
    echo "# TouchFS alias" >> ~/.bashrc
    echo "alias touchfs='python -m touchfs'" >> ~/.bashrc
    echo "Added touchfs alias to ~/.bashrc"
fi

section "Setup complete!"
echo "TouchFS is now set up and ready to use."
echo ""
echo "Quick start:"
echo "1. Set your OpenAI API key: export OPENAI_API_KEY=\"your-api-key-here\""
echo "2. Mount a TouchFS filesystem: touchfs mount workspace"
echo "3. Create files with content: touch workspace/README.md"
echo "4. Unmount when done: touchfs umount workspace"
echo ""
echo "For more information, see the README.md file."
echo "=========================================================="
