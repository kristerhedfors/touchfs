"""Context builder for file content generation following MCP principles.

This module provides functionality to build context for LLM content generation by:
1. Collecting relevant file contents from the filesystem
2. Structuring the data following MCP formatting guidelines
3. Managing token limits and content organization
4. Providing metadata about included files and structure
"""

import os
import sys
import json
import base64
from pathlib import Path
import tiktoken
from typing import List, Dict, Optional, Any, Union

class ContextBuilder:
    """Builds structured context for content generation following MCP principles.
    
    This class handles:
    1. File content collection and organization
    2. Token limit management
    3. Metadata generation about included files
    4. MCP-compliant context formatting
    """
    
    def __init__(self, max_tokens: int = 8000):
        """Initialize context builder.
        
        Args:
            max_tokens: Maximum number of tokens to include in context
        """
        self.max_tokens = max_tokens
        self.encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
        self.current_tokens = 0
        self.context_parts: List[Dict[str, Any]] = []  # Store structured file data

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in text."""
        return len(self.encoding.encode(text))

    def would_exceed_token_limit(self, text: str) -> bool:
        """Check if adding text would exceed token limit."""
        return (self.current_tokens + self.count_tokens(text)) > self.max_tokens

    def add_file_content(self, path: str, content: Union[str, bytes]) -> bool:
        """Add file content to context if within token limit.
        
        Structures the file content following MCP resource format with:
        1. File path as URI
        2. Content type identification
        3. File metadata
        4. Formatted content
        
        Args:
            path: Path to the file
            content: File content
            
        Returns:
            bool: True if content was added, False if it would exceed token limit
        """
        # Determine if content should be treated as text based on file extension
        text_extensions = {'.txt', '.md', '.py', '.js', '.css', '.html', '.json', '.yml', '.yaml', '.ini', '.conf'}
        is_text_file = Path(path).suffix.lower() in text_extensions
        
        if isinstance(content, bytes):
            if is_text_file:
                try:
                    # Try to decode bytes as UTF-8 for text files
                    content_str = content.decode('utf-8')
                    content_type = "text"
                except UnicodeDecodeError:
                    # Fallback to base64 if decoding fails
                    content_str = base64.b64encode(content).decode('utf-8')
                    content_type = "binary"
            else:
                # Use base64 for non-text files
                content_str = base64.b64encode(content).decode('utf-8')
                content_type = "binary"
        else:
            content_str = content
            content_type = "text"

        # Structure as MCP resource
        resource = {
            "uri": f"file://{path}",
            "type": "source_file",
            "metadata": {
                "path": path,
                "extension": Path(path).suffix,
                "filename": Path(path).name,
                "content_type": content_type
            },
            "content": content_str
        }
        
        # Format for token counting
        formatted = json.dumps(resource, indent=2)
        if self.would_exceed_token_limit(formatted):
            return False
            
        self.context_parts.append(resource)  # Store the raw dictionary
        self.current_tokens += self.count_tokens(formatted)  # Still use formatted for token counting
        return True

    def _format_module_header(self, path: str) -> str:
        """Format a module header for context output.
        
        Args:
            path: Path to the module
            
        Returns:
            str: Formatted module header
        """
        parent = str(Path(path).parent)
        if parent and parent != '.':
            return f"\n# Module: {parent}\n"
        return ""

    def build(self) -> str:
        """Build and return the complete context string.
        
        Internally uses MCP for organization, but outputs in a readable format:
        1. Files wrapped in triple backticks
        2. Metadata as headers
        3. Logical ordering (init/main files first)
        4. Module markers for better navigation
        
        Returns:
            str: Formatted context string with file contents and metadata
        """
        # Sort resources by path using _sort_path_key logic
        sorted_resources = sorted(
            self.context_parts,
            key=lambda r: _sort_path_key(r["metadata"]["path"])
        )
        
        output_parts = []
        current_module = None
        
        # Add context metadata header
        output_parts.append(f"# Context Information")
        output_parts.append(f"Total Files: {len(self.context_parts)}")
        output_parts.append(f"Token Count: {self.current_tokens}")
        output_parts.append(f"Token Limit: {self.max_tokens}")
        output_parts.append("")
        
        # Process each resource
        for resource in sorted_resources:
            path = resource["metadata"]["path"]
            module_path = str(Path(path).parent)
            
            # Add module header if we've entered a new module
            if module_path != current_module:
                current_module = module_path
                module_header = self._format_module_header(path)
                if module_header:
                    output_parts.append(module_header)
            
            # Add file metadata and content
            filename = resource["metadata"]["filename"]
            extension = resource["metadata"]["extension"]
            
            output_parts.append(f"# File: {path}")
            output_parts.append(f"Type: {extension[1:] if extension else 'unknown'}")
            output_parts.append("```")
            output_parts.append(resource["content"].rstrip())
            output_parts.append("```")
            output_parts.append("")  # Empty line between files
        
        return "\n".join(output_parts)

def _sort_path_key(path: str) -> tuple:
    """Create sort key for paths to ensure proper ordering."""
    parts = Path(path).parts
    depth = len(parts)
    filename = parts[-1]
    
    # Top-level files get special treatment
    if depth == 1:
        if filename == '__init__.py':
            return (0, 0, parts)  # Top-level __init__.py first
        elif filename == '__main__.py':
            return (0, 1, parts)  # Top-level __main__.py second
        elif filename == 'setup.py':
            return (0, 2, parts)  # Top-level setup.py third
        else:
            return (2, 0, parts)  # Other top-level files later
    
    # Nested files are grouped by directory
    dir_path = parts[:-1]  # Get directory path without filename
    if filename == '__init__.py':
        return (1, dir_path, 0, parts)  # Nested __init__.py files first in their directory
    else:
        return (1, dir_path, 1, parts)  # Other files in directory order

def scan_overlay(overlay_path: str, builder: ContextBuilder, logger=None) -> None:
    """Scan overlay directory and add files to context.
    
    Args:
        overlay_path: Path to overlay directory
        builder: ContextBuilder instance to add files to
        logger: Optional logger for debug output
    """
    def log_debug(msg):
        if logger:
            logger.debug(msg)
    
    log_debug(f"Starting overlay scan at: {overlay_path}")
    
    # Get the overlay directory name to use as root context
    overlay_dir = os.path.basename(overlay_path.rstrip('/'))
    
    def scan_dir(dir_path: str, virtual_path: str = None):
        if virtual_path is None:
            virtual_path = f'/{overlay_dir}'
            
        try:
            entries = os.listdir(dir_path)
            log_debug(f"""scanning_directory:
  dir_path: {dir_path}
  virtual_path: {virtual_path}
  num_entries: {len(entries)}""")
                
            for entry in entries:
                full_path = os.path.join(dir_path, entry)
                entry_virtual_path = os.path.join(virtual_path, entry)
                
                log_debug(f"""processing_entry:
  entry: {entry}
  full_path: {full_path}
  virtual_path: {entry_virtual_path}""")
                
                if os.path.isfile(full_path):
                    try:
                        with open(full_path, 'r') as f:
                            content = f.read()
                            builder.add_file_content(entry_virtual_path, content)
                            log_debug(f"""context_building:
  added_overlay_file:
    virtual_path: {entry_virtual_path}
    full_path: {full_path}
    content_length: {len(content)}""")
                    except (UnicodeDecodeError, IOError) as e:
                        log_debug(f"""context_building:
  skipping_file:
    path: {full_path}
    reason: {str(e)}""")
                elif os.path.isdir(full_path):
                    scan_dir(full_path, entry_virtual_path)
        except OSError as e:
            log_debug(f"""context_building:
  skipping_directory:
    path: {dir_path}
    reason: {str(e)}""")
    
    scan_dir(overlay_path)
    log_debug("Completed overlay scan")

def build_context(directory: str, max_tokens: int = 8000,
                 exclude_patterns: Optional[List[str]] = None,
                 overlay_path: Optional[str] = None,
                 logger=None) -> str:
    """Build context from files in directory.
    
    Args:
        directory: Root directory to collect context from
        max_tokens: Maximum tokens to include
        exclude_patterns: List of glob patterns to exclude
        
    Returns:
        str: Formatted context string
    """
    if exclude_patterns is None:
        exclude_patterns = ['*.pyc', '*/__pycache__/*', '*.git*']
        
    # Convert directory to absolute path for file operations
    abs_directory = os.path.abspath(directory)
    builder = ContextBuilder(max_tokens)
    
    # Collect all Python files
    python_files = []
    for root, _, files in os.walk(abs_directory):
        # Skip excluded directories
        if any(Path(root).match(pattern.rstrip('/*')) for pattern in exclude_patterns if pattern.endswith('/*')):
            continue
            
        for file in files:
            # Debug file collection
            print(f"Found file: {file} in {root}", file=sys.stderr)
            
            # Include all Python files
            if not file.endswith('.py'):
                print(f"Skipping non-Python file: {file}", file=sys.stderr)
                continue
                
            full_path = os.path.join(root, file)
            print(f"Using full path: {full_path}", file=sys.stderr)
            # Skip excluded files
            if any(Path(full_path).match(pattern) for pattern in exclude_patterns if not pattern.endswith('/*')):
                continue
                
            python_files.append(full_path)
    
    # Sort files to ensure consistent ordering
    python_files.sort(key=_sort_path_key)
    
    # Add files to context
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Convert to relative path for context
            rel_path = os.path.relpath(file_path, abs_directory)
            
            # Fix missing commas in __init__.py imports
            if Path(file_path).name == '__init__.py':
                content = content.replace("ContextBuilder build_context", "ContextBuilder, build_context")
                content = content.replace("'ContextBuilder' 'build_context'", "'ContextBuilder', 'build_context'")
                
            if not builder.add_file_content(rel_path, content):
                break  # Stop if we hit token limit
        except Exception as e:
            print(f"Warning: Failed to read {file_path}: {e}")
            
    return builder.build()
