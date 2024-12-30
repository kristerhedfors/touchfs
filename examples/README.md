# TouchFS Examples

This directory contains various examples demonstrating how to use TouchFS in different scenarios.

## How Examples Work

Each example follows a consistent pattern to demonstrate TouchFS capabilities:

1. **Setup and Cleanup**
   ```python
   # At start of example - cleanup any previous runs
   rm -rf workspace
   
   # Create and mount workspace
   mkdir workspace
   touchfs_mount workspace --prompt "Example-specific prompt"
   cd workspace
   ```

2. **Content Generation**
   - Files are touched in a specific order to trigger content generation
   - Each file's content is influenced by previously generated files
   - The filesystem maintains context between files
   ```python
   # Example sequence
   touch README.md     # Describes what we're building
   touch config.json   # AI generates config based on README
   touch main.py      # AI implements based on README and config
   ```

3. **Final Cleanup**
   ```python
   # At end of example
   cd ..
   rm -rf workspace
   ```

## Examples

### simple-api
A Jupyter notebook demonstrating how to use TouchFS to generate a simple Python web API. Shows how the filesystem generates coherent API code and client:

```python
# Setup workspace
rm -rf workspace
mkdir workspace
touchfs_mount workspace --prompt "Create a Flask-based REST API"
cd workspace

# Generate API components
touch README.md        # Describes API structure and endpoints
touch app.py          # AI generates Flask API based on README
touch curl_client.sh  # AI creates client script matching API endpoints

# Cleanup
cd ..
rm -rf workspace
```

### sci-fi-novel
A Jupyter notebook showing how to use TouchFS to help write a science fiction novel. The filesystem helps generate content by understanding context from touched files:

```python
# Setup workspace
rm -rf workspace
mkdir workspace
touchfs_mount workspace --prompt "Write a science fiction novel"
cd workspace

# Initial chapter creation
touch chapter1.txt  # AI generates opening chapter
touch chapter2.txt  # AI builds on chapter 1

# Unhappy with chapter 2, create alternative
touch chapter2_v1.txt  # Original version preserved
touch chapter2_v2.txt  # AI sees v1, writes alternative

# Missing background discovered
touch alien_culture_background.txt  # Add missing context
rm chapter3.txt      # Remove chapter needing context
touch chapter3.txt   # AI rewrites with cultural background

# Cleanup
cd ..
rm -rf workspace
```

The filesystem creates an intelligent environment where file operations guide content development. Each touch operation considers existing files as context, enabling coherent progression and refinement of the generated content.

## Key Concepts

1. **Workspace Isolation**
   - Each example runs in its own workspace directory
   - Clean state for each run
   - Easy cleanup

2. **Ordered Generation**
   - Files are created in a specific sequence
   - Later files build on context from earlier files
   - Order matters for coherent content generation

3. **Context Awareness**
   - TouchFS maintains context between files
   - Content generation considers all relevant files
   - Modifications trigger appropriate regeneration

4. **Cleanup Support**
   - Examples can be safely rerun
   - No leftover files from previous runs
   - Clean workspace for each demonstration
