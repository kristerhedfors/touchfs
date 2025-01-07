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
import logging
from pathlib import Path
import tiktoken
from typing import List, Dict, Optional, Any, Union
from ...config.settings import DEFAULT_MAX_TOKENS, DEFAULT_TEXT_EXTENSIONS

logger = logging.getLogger("touchfs")

class ContextBuilder:
    """Builds structured context for content generation following MCP principles.
    
    This class handles:
    1. File content collection and organization
    2. Token limit management
    3. Metadata generation about included files
    4. MCP-compliant context formatting
    """
    
    def __init__(self, max_tokens: int = DEFAULT_MAX_TOKENS):
        """Initialize context builder.
        
        Args:
            max_tokens: Maximum number of tokens to include in context
        """
        self.max_tokens = max_tokens
        self.encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
        self.current_tokens = 0
        self.context_parts: List[Dict[str, Any]] = []  # Store structured file data
        self.failed_attempts = 0  # Track number of failed attempts
        self.MAX_FAILED_ATTEMPTS = 3  # Stop after this many consecutive failures
        self.TOKEN_LIMIT_THRESHOLD = 0.8  # Stop at 80% of max tokens
        logger.debug(f"Initialized ContextBuilder with max_tokens={max_tokens}")

    def count_tokens(self, text: str) -> Optional[int]:
        """Count the number of tokens in text."""
        try:
            if not isinstance(text, str):
                return None
            return len(self.encoding.encode(text))
        except Exception:
            return None

    def should_stop_collecting(self) -> bool:
        """Check if we should stop collecting more files."""
        # Stop if we've hit too many failed attempts
        if self.failed_attempts >= self.MAX_FAILED_ATTEMPTS:
            logger.debug(f"Stopping after {self.failed_attempts} failed attempts")
            return True
            
        # Stop if we're at 80% of max tokens
        token_threshold = self.max_tokens * self.TOKEN_LIMIT_THRESHOLD
        if self.current_tokens >= token_threshold:
            logger.debug(f"Stopping at {self.current_tokens}/{self.max_tokens} tokens (80% threshold)")
            return True
            
        return False

    def would_exceed_token_limit(self, text: str) -> bool:
        """Check if adding text would exceed token limit."""
        try:
            token_count = self.count_tokens(text)
            if token_count is None:
                logger.debug("Could not count tokens, assuming limit would be exceeded")
                self.failed_attempts += 1
                return True
            new_total = self.current_tokens + token_count
            if new_total > self.max_tokens:
                logger.debug(f"Token limit check: current={self.current_tokens}, new={token_count}, total={new_total}, max={self.max_tokens}")
                self.failed_attempts += 1
            else:
                self.failed_attempts = 0  # Reset counter on success
            return new_total > self.max_tokens
        except Exception as e:
            logger.debug(f"Token limit check failed: {e}")
            return True

    def add_file_content(self, path: str, content: Union[str, bytes]) -> bool:
        """Add file content to context if within token limit.
        
        Structures the file content following MCP resource format with:
        1. File path as URI
        2. Content type identification
        3. File metadata
        4. Formatted content
        
        Args:
            path: Path to the file (relative)
            content: File content
            
        Returns:
            bool: True if content was added, False if it would exceed token limit
        """
        try:
            path_obj = Path(path)
            logger.debug(f"Processing file: {path}")
            
            # Skip files that aren't in our text extensions list
            if path_obj.suffix.lower() not in DEFAULT_TEXT_EXTENSIONS:
                logger.debug(f"Skipping non-text file: {path}")
                return False
            
            try:
                # Try to decode as UTF-8 text
                if isinstance(content, bytes):
                    content_str = content.decode('utf-8')
                else:
                    content_str = str(content)
            except UnicodeDecodeError:
                logger.debug(f"Failed to decode {path} as UTF-8, skipping")
                return False

            # Format content for output
            formatted_content = f"# File: {path}\nType: {path_obj.suffix[1:] if path_obj.suffix else 'unknown'}\n"
            formatted_content += "```\n" + content_str.rstrip() + "\n```\n"

            # Check token limit before adding
            if self.would_exceed_token_limit(formatted_content):
                logger.debug(f"Skipping {path}: would exceed token limit")
                return False

            # Structure as MCP resource
            resource = {
                "uri": f"file://{path}",
                "type": "source_file",
                "metadata": {
                    "path": path,
                    "extension": path_obj.suffix,
                    "filename": path_obj.name,
                    "content_type": "text",
                    "formatted_content": formatted_content
                },
                "content": content_str
            }
            logger.debug(f"Created resource metadata: {resource['metadata']}")
            
            # Add to context parts and update token count
            self.context_parts.append(resource)
            token_count = self.count_tokens(formatted_content)
            if token_count:
                self.current_tokens += token_count
            logger.debug(f"Added {path} to context")
            return True
            
        except Exception as e:
            logger.debug(f"Failed to add file content for {path}: {e}")
            return False

    def build(self) -> str:
        """Build and return the complete context string.
            
        Returns:
            str: Formatted context string with file contents and metadata
        """
        return build_text_context(self.context_parts)

def build_text_context(resources: List[Dict[str, Any]]) -> str:
    """Build text context for LLM content generation.
    
    This function is used by both touchfs mount and touchfs context
    to build the context string that gets sent to the LLM.
    
    Args:
        resources: List of resource dictionaries with metadata and content
        
    Returns:
        str: Formatted context string with file contents and metadata
    """
    # Sort resources by path using _sort_path_key logic
    try:
        sorted_resources = []
        for resource in resources:
            try:
                path = resource["metadata"]["path"]
                if not isinstance(path, str):
                    logger.debug(f"Invalid path in resource metadata: {path}")
                    continue
                sorted_resources.append(resource)
            except (KeyError, TypeError) as e:
                logger.debug(f"Invalid resource format: {e}")
                continue
                
        # Pre-validate and generate sort keys for resources
        sort_keys = []
        for resource in sorted_resources:
            try:
                path = resource["metadata"]["path"]
                key = _sort_path_key(path)
                if any(x is None for x in key):
                    logger.debug(f"Invalid sort key (contains None) for resource path: {path}")
                    logger.debug(f"Sort key: {key}")
                    raise ValueError(f"Invalid sort key for resource path: {path}")
                sort_keys.append((key, resource))
            except Exception as e:
                logger.debug(f"Failed to generate sort key for resource path: {path}")
                logger.debug(f"Error: {str(e)}")
                raise RuntimeError(f"Failed to generate sort key for resource: {e}")
        
        # Sort using pre-validated keys
        try:
            sort_keys.sort()
            sorted_resources = [r for _, r in sort_keys]
        except TypeError as e:
            logger.debug("Sort keys:")
            for key, _ in sort_keys:
                logger.debug(f"  {key}")
            raise RuntimeError(f"Failed to sort resources: {e}")
    except Exception as e:
        logger.debug(f"Resource sorting failed: {e}")
        logger.debug(f"Resources: {resources}")
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

def _sort_path_key(path: str) -> tuple:
    """Create sort key for paths to ensure proper ordering."""
    try:
        # Convert path to string to handle Path objects
        path_str = str(path)
        logger.debug(f"Generating sort key for path: {path_str}")
        
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
        
        logger.debug(f"Generated sort key: {sort_key}")
        return sort_key
        
    except Exception as e:
        logger.debug(f"Error in _sort_path_key for path '{path}': {e}")
        # Return a fallback sort key with consistent types
        return (999, 0, ('',), 999, str(path))

def build_context(directory: str, max_tokens: int = DEFAULT_MAX_TOKENS,
                 exclude_patterns: Optional[List[str]] = None,
                 include_patterns: Optional[List[str]] = None) -> str:
    """Build context from files in directory.
    
    Args:
        directory: Root directory to collect context from
        max_tokens: Maximum tokens to include
        exclude_patterns: List of glob patterns to exclude
        include_patterns: List of glob patterns to include. When specified,
                         only files matching these patterns will be included.
        
    Returns:
        str: Formatted context string
    """
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
            rel_path = Path(os.path.relpath(full_path, abs_directory))
            
            # Skip excluded files
            if any(Path(full_path).match(pattern) for pattern in exclude_patterns if not pattern.endswith('/*')):
                continue
            
            # If include patterns are specified, only include matching files
            if include_patterns:
                if not any(rel_path.match(pattern) for pattern in include_patterns):
                    continue
                
            files.append(full_path)
    
    # Log collected files
    logger.debug(f"Found files: {files}")
    
    # Sort files to ensure consistent ordering
    try:
        # First validate all paths can generate sort keys
        sort_keys = []
        for file_path in files:
            try:
                rel_path = os.path.relpath(file_path, abs_directory)
                key = _sort_path_key(rel_path)
                if any(x is None for x in key):
                    logger.debug(f"Invalid sort key (contains None) for path: {rel_path}")
                    logger.debug(f"Sort key: {key}")
                    raise ValueError(f"Invalid sort key for path: {rel_path}")
                sort_keys.append((key, file_path))
            except Exception as e:
                logger.debug(f"Failed to generate sort key for path: {file_path}")
                logger.debug(f"Error: {str(e)}")
                raise
        
        # Sort using pre-validated keys
        sort_keys.sort()
        files = [f for _, f in sort_keys]
        logger.debug(f"Sorted files: {files}")
    except Exception as e:
        logger.debug(f"File sorting failed: {e}")
        logger.debug(f"Files being sorted: {files}")
        raise RuntimeError(f"Failed to sort files: {e}")
    
            # Add files to context
    for file_path in files:
        # Check if we should stop collecting more files
        if builder.should_stop_collecting():
            logger.debug("Stopping file collection due to token limit or failed attempts")
            break
            
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
                logger.debug(f"Failed to read {file_path}: {e}")
                continue
        except IOError as e:
            logger.debug(f"Failed to read {file_path}: {e}")
            continue
            
        if not builder.add_file_content(rel_path, content):
            continue  # Continue to next file if this one was skipped or hit token limit
            
    return builder.build()
