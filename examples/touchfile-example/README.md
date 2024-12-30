This example demonstrates using TouchFS to generate a Touchfile that defines a sequence of file operations using ONLY mkdir and touch commands, similar to how Docker uses Dockerfile to define containers. The Touchfile is an executable bash script that TouchFS generates based on a prompt.


## How It Works

1. TouchFS generates the Touchfile based on a .prompt file
2. The Touchfile contains ONLY:
   - mkdir commands to create directories
   - touch commands to create files
   - No file content is written in the Touchfile
   - The sequence of touch operations triggers TouchFS to generate appropriate content
   - Each file's content is determined automatically based on its position in the sequence

## Files

- `.prompt`: Defines what kind of Touchfile should be generated
- `workspace/`: Directory where TouchFS is mounted and files are created
- Generated files:
  - `Touchfile`: The generated script
  - Project files created by executing the Touchfile

## Usage

1. Create workspace:
   ```bash
   mkdir workspace
   ```

2. Mount TouchFS:
   ```bash
   touchfs_mount workspace
   ```
   cd workspace

3. Generate and execute Touchfile:
   ```bash
   touch Touchfile  # This triggers TouchFS to generate the Touchfile
   chmod +x Touchfile
   ./Touchfile
   ```

This will first generate the Touchfile through TouchFS, then execute it to create all project files in sequence.


## Key Features

- TouchFS determines the proper sequence of file operations
- Generated Touchfile serves as documentation of file creation steps
- Content generation is automatic and context-aware
- Easy to modify and re-run to experiment with different structures
