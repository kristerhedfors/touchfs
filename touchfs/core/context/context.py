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
    
    def __init__(self, max_tokens: int = 32000):
        """Initialize context builder.
        
        Args:
            max_tokens: Maximum number of tokens to include in context
        """
        self.max_tokens = max_tokens
        self.encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
        self.current_tokens = 0
        self.context_parts: List[Dict[str, Any]] = []  # Store structured file data

    def count_tokens(self, text: str) -> Optional[int]:
        """Count the number of tokens in text."""
        try:
            if not isinstance(text, str):
                return None
            return len(self.encoding.encode(text))
        except Exception:
            return None

    def would_exceed_token_limit(self, text: str) -> bool:
        """Check if adding text would exceed token limit."""
        try:
            token_count = self.count_tokens(text)
            if token_count is None:
                return True
            return (self.current_tokens + token_count) > self.max_tokens
        except Exception:
            return True

    def add_file_content(self, path: str, content: Union[str, bytes], logger=None) -> bool:
        """Add file content to context if within token limit.
        
        Structures the file content following MCP resource format with:
        1. File path as URI
        2. Content type identification
        3. File metadata
        4. Formatted content
        
        Args:
            path: Path to the file (relative)
            content: File content
            logger: Optional logger for debug output
            
        Returns:
            bool: True if content was added, False if it would exceed token limit
        """
        def log_debug(msg):
            if logger:
                logger.debug(msg)
                
        try:
            path_obj = Path(path)
            log_debug(f"Processing file: {path}")
            
            # Determine if content should be treated as text based on file extension
            text_extensions = {'.txt', '.md', '.py', '.js', '.css', '.html', '.json', '.yml', '.yaml', '.ini', '.conf'}
            is_text_file = path_obj.suffix.lower() in text_extensions
            
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
                        log_debug(f"Failed to decode {path} as UTF-8, using base64")
                else:
                    # Use base64 for non-text files
                    content_str = base64.b64encode(content).decode('utf-8')
                    content_type = "binary"
            else:
                content_str = str(content)  # Ensure string conversion
                content_type = "text"

            # Format content for output
            formatted_content = f"# File: {path}\nType: {path_obj.suffix[1:] if path_obj.suffix else 'unknown'}\n"
            if content_type == "binary":
                formatted_content += f"{content_str}\n"
            else:
                formatted_content += "```\n" + content_str.rstrip() + "\n```\n"

            # Check token limit before adding
            if self.would_exceed_token_limit(formatted_content):
                log_debug(f"Skipping {path}: would exceed token limit")
                return False

            # Structure as MCP resource
            resource = {
                "uri": f"file://{path}",
                "type": "source_file",
                "metadata": {
                    "path": path,
                    "extension": path_obj.suffix,
                    "filename": path_obj.name,
                    "content_type": content_type,
                    "formatted_content": formatted_content
                },
                "content": content_str
            }
            log_debug(f"Created resource metadata: {resource['metadata']}")
            
            # Add to context parts and update token count
            self.context_parts.append(resource)
            token_count = self.count_tokens(formatted_content)
            if token_count:
                self.current_tokens += token_count
            log_debug(f"Added {path} to context ({content_type})")
            return True
            
        except Exception as e:
            log_debug(f"Failed to add file content for {path}: {e}")
            return False

    def build(self, logger=None) -> str:
        """Build and return the complete context string.
        
        Args:
            logger: Optional logger for debug output
            
        Returns:
            str: Formatted context string with file contents and metadata
        """
        return build_text_context(self.context_parts, logger=logger)

def build_text_context(resources: List[Dict[str, Any]], logger=None) -> str:
    """Build text context for LLM content generation.
    
    This function is used by both touchfs mount and touchfs context
    to build the context string that gets sent to the LLM.
    
    Args:
        resources: List of resource dictionaries with metadata and content
        logger: Optional logger for debug output
        
    Returns:
        str: Formatted context string with file contents and metadata
    """
    def log_debug(msg):
        if logger:
            logger.debug(msg)
            
    # Sort resources by path using _sort_path_key logic
    try:
        sorted_resources = []
        for resource in resources:
            try:
                path = resource["metadata"]["path"]
                if not isinstance(path, str):
                    log_debug(f"Invalid path in resource metadata: {path}")
                    continue
                sorted_resources.append(resource)
            except (KeyError, TypeError) as e:
                log_debug(f"Invalid resource format: {e}")
                continue
                
        # Pre-validate and generate sort keys for resources
        sort_keys = []
        for resource in sorted_resources:
            try:
                path = resource["metadata"]["path"]
                key = _sort_path_key(path, logger)
                if any(x is None for x in key):
                    log_debug(f"Invalid sort key (contains None) for resource path: {path}")
                    log_debug(f"Sort key: {key}")
                    raise ValueError(f"Invalid sort key for resource path: {path}")
                sort_keys.append((key, resource))
            except Exception as e:
                log_debug(f"Failed to generate sort key for resource path: {path}")
                log_debug(f"Error: {str(e)}")
                raise RuntimeError(f"Failed to generate sort key for resource: {e}")
        
        # Sort using pre-validated keys
        try:
            sort_keys.sort()
            sorted_resources = [r for _, r in sort_keys]
        except TypeError as e:
            log_debug("Sort keys:")
            for key, _ in sort_keys:
                log_debug(f"  {key}")
            raise RuntimeError(f"Failed to sort resources: {e}")
    except Exception as e:
        log_debug(f"Resource sorting failed: {e}")
        log_debug(f"Resources: {resources}")
        raise RuntimeError(f"Failed to sort resources: {e}")
    
    output_parts = []
    current_module = None
    
    # Add context metadata header
    output_parts.append(f"# Context Information")
    output_parts.append("")
    
    # Process each resource
    for resource in sorted_resources:
        path = resource["metadata"]["path"]
        module_path = str(Path(path).parent)
        
        # Add module header if we've entered a new module
        if module_path != current_module:
            current_module = module_path
            if module_path and module_path != '.':
                output_parts.append(f"\n# Module: {module_path}\n")
        
        # Add pre-formatted content
        output_parts.append(resource["metadata"]["formatted_content"])
    
    return "\n".join(output_parts)

def _sort_path_key(path: str, logger=None) -> tuple:
    """Create sort key for paths to ensure proper ordering."""
    def log_debug(msg):
        if logger:
            logger.debug(msg)
            
    try:
        # Convert path to string to handle Path objects
        path_str = str(path)
        log_debug(f"Generating sort key for path: {path_str}")
        
        # Split path into parts
        parts = Path(path_str).parts
        depth = len(parts)
        filename = parts[-1] if parts else ''
        
        # Convert directory parts to strings to ensure they're comparable
        dir_parts = tuple(str(p) for p in (parts[:-1] if len(parts) > 1 else ('',)))
        
        # Determine file priority
        if filename == '__init__.py':
            file_priority = 0
        elif filename == '__main__.py':
            file_priority = 1
        elif filename == 'setup.py':
            file_priority = 2
        else:
            file_priority = 3
            
        # Create sort key with consistent types and ensure no None values
        sort_key = (
            0 if depth == 1 else 1,  # priority: int
            len(dir_parts),          # dir_depth: int
            tuple(str(p) if p is not None else '' for p in dir_parts),  # dir_path: tuple of str
            file_priority,           # file_priority: int
            str(filename) if filename is not None else ''            # filename: str
        )
        
        log_debug(f"Generated sort key: {sort_key}")
        return sort_key
        
    except Exception as e:
        log_debug(f"Error in _sort_path_key for path '{path}': {e}")
        # Return a fallback sort key with consistent types
        return (999, 0, ('',), 999, str(path))

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
                            builder.add_file_content(entry_virtual_path, content, logger)
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

def build_context(directory: str, max_tokens: int = 32000,
                 exclude_patterns: Optional[List[str]] = None,
                 overlay_path: Optional[str] = None,
                 logger=None) -> str:
    """Build context from files in directory.
    
    Args:
        directory: Root directory to collect context from
        max_tokens: Maximum tokens to include
        exclude_patterns: List of glob patterns to exclude
        logger: Optional logger for debug output
        
    Returns:
        str: Formatted context string
    """
    def log_debug(msg):
        if logger:
            logger.debug(msg)
            
    if exclude_patterns is None:
        exclude_patterns = ['*.pyc', '*/__pycache__/*', '*.git*']
        
    # Convert directory to absolute path for file operations
    abs_directory = os.path.abspath(directory)
    builder = ContextBuilder(max_tokens)
    
    # Collect all files
    files = []
    for root, _, filenames in os.walk(abs_directory):
        # Skip excluded directories
        if any(Path(root).match(pattern.rstrip('/*')) for pattern in exclude_patterns if pattern.endswith('/*')):
            continue
            
        for file in filenames:
            full_path = os.path.join(root, file)
            
            # Skip excluded files
            if any(Path(full_path).match(pattern) for pattern in exclude_patterns if not pattern.endswith('/*')):
                continue
                
            files.append(full_path)
    
    # Sort files to ensure consistent ordering
    try:
        # First validate all paths can generate sort keys
        sort_keys = []
        for file_path in files:
            try:
                rel_path = os.path.relpath(file_path, abs_directory)
                key = _sort_path_key(rel_path, logger)
                if any(x is None for x in key):
                    log_debug(f"Invalid sort key (contains None) for path: {rel_path}")
                    log_debug(f"Sort key: {key}")
                    raise ValueError(f"Invalid sort key for path: {rel_path}")
                sort_keys.append((key, file_path))
            except Exception as e:
                log_debug(f"Failed to generate sort key for path: {file_path}")
                log_debug(f"Error: {str(e)}")
                raise
        
        # Sort using pre-validated keys
        sort_keys.sort()
        files = [f for _, f in sort_keys]
    except Exception as e:
        log_debug(f"File sorting failed: {e}")
        log_debug(f"Files being sorted: {files}")
        raise RuntimeError(f"Failed to sort files: {e}")
    
    # Add files to context
    for file_path in files:
        # Convert to relative path for context
        rel_path = os.path.relpath(file_path, abs_directory)
        
        try:
            # First try to read as text
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # If that fails, read as binary
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
            except IOError as e:
                log_debug(f"Failed to read {file_path}: {e}")
                continue
        except IOError as e:
            log_debug(f"Failed to read {file_path}: {e}")
            continue
            
        if not builder.add_file_content(rel_path, content, logger):
            break  # Stop if we hit token limit
            
    return builder.build(logger=logger)
