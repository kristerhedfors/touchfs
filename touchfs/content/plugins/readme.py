"""README generator that creates filesystem tree documentation with ANSI colors."""
from typing import Dict, List, Union
from ...models.filesystem import FileNode
from .proc import ProcPlugin

# ANSI color codes
BOLD = "\033[1m"
BLUE = "\033[34m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RED = "\033[31m"
MAGENTA = "\033[35m"
RESET = "\033[0m"

# Compound styles
HEADER = f"{BOLD}{BLUE}"
SUBHEADER = f"{BOLD}{CYAN}"
CODE = f"{GREEN}"
TREE_PREFIX = f"{YELLOW}"
FILE_INFO = f"{MAGENTA}"

class ReadmeGenerator(ProcPlugin):
    """Generator that creates README in .touchfs directory with filesystem tree structure."""
    
    def generator_name(self) -> str:
        return "readme"
    
    def get_proc_path(self) -> str:
        return "readme"
    
    def _get_node_attr(self, node: Union[Dict, FileNode], attr: str, default=None):
        """Safely get attribute from either dict or FileNode object."""
        if isinstance(node, dict):
            return node.get(attr, default)
        return getattr(node, attr, default)
    
    def _build_tree(self, path: str, structure: Dict[str, Union[Dict, FileNode]], indent: str = "") -> List[str]:
        """Build a tree representation of the filesystem structure."""
        result = []
        
        node = structure[path]
        children = self._get_node_attr(node, 'children', {})
        sorted_names = sorted(children.keys())
        
        for i, name in enumerate(sorted_names):
            child_path = children[name]
            is_last = i == len(sorted_names) - 1
            
            # Choose the appropriate symbols with colors
            prefix = f"{TREE_PREFIX}└── {RESET}" if is_last else f"{TREE_PREFIX}├── {RESET}"
            child_indent = indent + (f"{TREE_PREFIX}    {RESET}" if is_last else f"{TREE_PREFIX}│   {RESET}")
            
            # Build the line with file name and status
            child_node = structure[child_path]
            line = f"{indent}{prefix}{CYAN}{name}{RESET}"
            
            if self._get_node_attr(child_node, 'type') == "file":
                # Add appropriate spacing
                line += " " * max(1, 40 - len(line))  # Ensure at least one space
                
                xattrs = self._get_node_attr(child_node, 'xattrs', {})
                if xattrs and "generator" in xattrs:
                    line += f"{FILE_INFO}[Auto-generated by {xattrs['generator']} plugin]{RESET}"
                else:
                    # Find nearest prompt file using settings function
                    from ...config.settings import find_nearest_prompt_file
                    prompt_path = find_nearest_prompt_file(child_path, structure)
                    prompt_info = f", using {prompt_path[1:]}" if prompt_path else ""
                    line += f"{FILE_INFO}[Generated on first read{prompt_info}]{RESET}"
                
                result.append(line)
            else:
                result.append(line)
                # Recursively add children if this is a directory
                result.extend(self._build_tree(child_path, structure, child_indent))
        
        return result
    
    def _get_touchfs_overview(self, fs_structure: Dict[str, Union[Dict, FileNode]]) -> str:
        """Generate overview of .touchfs directory contents."""
        overview = []
        touchfs_dir = "/.touchfs"
        
        if touchfs_dir not in fs_structure:
            return "No .touchfs directory found."
            
        node = fs_structure[touchfs_dir]
        touchfs_files = self._get_node_attr(node, 'children', {})
        
        overview.append(f"{HEADER}## .touchfs Directory Overview{RESET}\n")
        overview.append(f"The .touchfs directory contains special files that control and monitor the filesystem:\n")
        
        file_descriptions = {
            "model.default": "Specifies the OpenAI model used for content generation. Can be set using JSON format or raw model name. Default: gpt-4o-2024-08-06",
            "prompt.default": "Contains the system prompt template used for content generation. Supports custom prompts per directory and includes best practices for different file types.",
            "readme": "This file - provides filesystem documentation and structure overview. Auto-updates when filesystem changes.",
            "tree": "Provides a structured, greppable tree visualization of the filesystem, showing which plugins generate each file's content.",
            "log": "Provides access to the TouchFS log file (/var/log/touchfs/touchfs.log) for monitoring system activity and debugging."
        }
        
        for name, path in sorted(touchfs_files.items()):
            node = fs_structure[path]
            overview.append(f"\n{SUBHEADER}### {name}{RESET}")
            
            # Add file description
            if name in file_descriptions:
                overview.append(f"\n{file_descriptions[name]}")
            
            # Add generator info if available
            xattrs = self._get_node_attr(node, 'xattrs', {})
            if xattrs and "generator" in xattrs:
                overview.append(f"\nManaged by: {xattrs['generator']} plugin")
            
            # Add preview of current content if available
            content = self._get_node_attr(node, 'content')
            if content:
                content_preview = content.strip()[:200]
                if len(content) > 200:
                    content_preview += "..."
                overview.append(f"\nCurrent content preview:\n{CODE}```\n{content_preview}\n```{RESET}")
        
        return "\n".join(overview)

    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, Union[Dict, FileNode]]) -> str:
        """Generate a readme with filesystem structure and .touchfs overview."""
        # Force update of filesystem structure before generating
        tree_lines = self._build_tree("/", fs_structure)
        tree_str = "\n".join(tree_lines)
        touchfs_overview = self._get_touchfs_overview(fs_structure)
        
        return f"""{HEADER}# Project Structure{RESET}

This directory contains the following structure:

{tree_str}

Files in the tree are marked in two ways:
{FILE_INFO}- "[Auto-generated by ...]" indicates files whose content is dynamically generated by a plugin on every read
- "[Generated on first read]" indicates files whose content is generated when first accessed and then cached{RESET}

{touchfs_overview}

{HEADER}## Usage Tips{RESET}

{SUBHEADER}1. **Model Selection**{RESET}
   - Edit model.default to change the OpenAI model
   - Use JSON format for additional settings
   - Or simply write the model name directly

{SUBHEADER}2. **Content Generation**{RESET}
   - Default generator handles most files
   - Uses nearest prompt.default for context
   - Temperature 0.2 for consistent output

{SUBHEADER}3. **System Monitoring**{RESET}
   - View logs through .touchfs/log
   - Check filesystem structure with .touchfs/tree
   - Monitor file generation status in readme

{SUBHEADER}4. **Context System**{RESET}
   - Use touchfs_context to analyze project context:
     {CODE}```bash
     # Get context from current directory
     touchfs_context .
     
     # Limit token count
     touchfs_context . --max-tokens 4000
     
     # Exclude specific files
     touchfs_context . --exclude "*.pyc"
     ```{RESET}
   - Smart file ordering (e.g., __init__.py first)
   - Token-aware content inclusion
   - Rich metadata for each file
   - Organized by module structure

{SUBHEADER}5. **Custom Prompts**{RESET}
   - Create prompt.default in any directory
   - Inherits from parent if not found
   - Supports best practices templates

{SUBHEADER}6. **File Generation**{RESET}
   - Plugin-managed files: Content regenerated on every read (e.g., .touchfs/model.default)
   - Default files: Content generated and cached on first read (e.g., /etc/fstab)
   - Both types use context-aware generation based on filesystem state

The .touchfs directory provides a centralized location for controlling and monitoring
the filesystem's behavior. Files in this directory are automatically updated to
reflect the current system state.

{HEADER}## Context System Details{RESET}

The context system helps you understand and work with your project's structure:

{SUBHEADER}1. **Built-in Context Management**{RESET}
   - Automatic context collection during generation
   - Hierarchical inheritance through directories
   - Smart token management and truncation
   - Prioritizes important files like __init__.py

{SUBHEADER}2. **Command Line Tool (touchfs_context)**{RESET}
   - Analyze project structure and content
   - Control token usage with --max-tokens
   - Exclude irrelevant files with --exclude
   - Get MCP-compliant output for tools/plugins

{SUBHEADER}3. **Output Format**{RESET}
   - Structured file content as resources
   - File metadata (path, type, etc.)
   - Module/directory organization
   - Syntax-highlighted content blocks

Example touchfs_context output:
{CODE}```
# Context Information
Total Files: 12
Token Count: 3200
Token Limit: 8000

# Module: src/core
# File: __init__.py
Type: python
```{RESET}

The context system helps ensure generated content is relevant and consistent with your project's structure and conventions.
"""