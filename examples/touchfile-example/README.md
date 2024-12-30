# Touchfile Example

This example demonstrates using LLMFS to generate a Touchfile that defines a sequence of file operations using ONLY mkdir and touch commands, similar to how Docker uses Dockerfile to define containers. The Touchfile is an executable bash script that LLMFS generates based on a prompt.

## Concept

Just as Dockerfile is used to define containers, a Touchfile is used to define a sequence of file operations. The key aspects are:

1. LLMFS generates the Touchfile based on a .prompt file
2. The Touchfile contains ONLY:
   - mkdir commands to create directories
   - touch commands to create files
   - Comments explaining the sequence
3. Content generation:
   - No file content is written in the Touchfile
   - The sequence of touch operations triggers LLMFS to generate appropriate content
   - Each file's content is determined automatically based on its position in the sequence

## Example Structure

The example includes:

- `.prompt`: Defines what kind of Touchfile should be generated
- `workspace/`: Directory where LLMFS is mounted and files are created
- Generated files:
  - `Touchfile`: Generated script that defines file creation sequence
  - Project files: Created by executing the Touchfile

## Usage

1. Create a workspace directory:
   ```bash
   mkdir workspace
   ```

2. Mount LLMFS:
   ```bash
   llmfs_mount workspace
   ```

3. Write concept to .prompt:
   ```bash
   cp .prompt workspace/
   ```

4. Generate and execute Touchfile:
   ```bash
   cd workspace
   touch Touchfile  # This triggers LLMFS to generate the Touchfile
   chmod +x Touchfile
   ./Touchfile
   ```

This will first generate the Touchfile through LLMFS, then execute it to create all project files in sequence.

## Benefits

- LLMFS determines the proper sequence of file operations
- Generated Touchfile serves as documentation of file creation steps
- Self-contained script that can be version controlled
- Clear separation between file sequence definition and execution
