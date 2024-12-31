#!/bin/bash

# Exit on error
set -e

# Echo all commands
set -x

# Create workspace directory
mkdir -p workspace

# Mount empty touchfs
touchfs_mount workspace

# Set the generation prompt
cat > workspace/.prompt << EOL
Create a female hero character from aspects defined in files:

Requirements:
- Text descriptions in files must be extremely concise (2-3 sentences)
- Each file should focus only on its specific aspect
EOL

# throw in project README as context
cp ../../README.md workspace/README.md

# Write the files list
cat > workspace/files.txt << EOL
physical_traits.txt
outfit.txt
pose.txt
personality.txt
expression.txt
EOL

cd workspace

# generate files
touch $(cat files.txt)

# remove project README to keep from image generation context
rm README.md

# create hero images
touch hero1.jpg hero2.jpg

# Copy the generated files to the workspace directory
cp $(cat files.txt) ..
cp hero1.jpg hero2.jpg ..
cd ..

# Show the latest logs
echo "Checking generation logs..."
tail -n 100 /var/log/touchfs/touchfs.log

# Unmount the filesystem
touchfs_mount -u workspace

echo "Hero image generation complete! Check the workspace directory for results."
