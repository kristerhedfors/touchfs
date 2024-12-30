"""Context builder for file content generation."""

import os
from pathlib import Path
import tiktoken
from typing import List, Dict, Optional

class ContextBuilder:
    """Builds context for content generation by collecting surrounding file contents."""
    
    def __init__(self, max_tokens: int = 8000):
        """Initialize context builder.
        
        Args:
            max_tokens: Maximum number of tokens to include in context
        """
        self.max_tokens = max_tokens
        self.encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
        self.current_tokens = 0
        self.context_parts: List[str] = []

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in text."""
        return len(self.encoding.encode(text))

    def would_exceed_token_limit(self, text: str) -> bool:
        """Check if adding text would exceed token limit."""
        return (self.current_tokens + self.count_tokens(text)) > self.max_tokens

    def add_file_content(self, path: str, content: str) -> bool:
        """Add file content to context if within token limit.
        
        Returns:
            bool: True if content was added, False if it would exceed token limit
        """
        formatted = f"# File: {path}\n```\n{content}\n```\n"
        if self.would_exceed_token_limit(formatted):
            return False
            
        self.context_parts.append(formatted)
        self.current_tokens += self.count_tokens(formatted)
        return True

    def build(self) -> str:
        """Build and return the complete context string."""
        return "\n".join(self.context_parts)

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

def build_context(directory: str, max_tokens: int = 8000, 
                 exclude_patterns: Optional[List[str]] = None) -> str:
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
        
    builder = ContextBuilder(max_tokens)
    
    # Collect all Python files
    python_files = []
    for root, _, files in os.walk(directory):
        # Skip excluded directories
        if any(Path(root).match(pattern.rstrip('/*')) for pattern in exclude_patterns if pattern.endswith('/*')):
            continue
            
        for file in files:
            if not file.endswith('.py'):
                continue
                
            full_path = os.path.join(root, file)
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
            if not builder.add_file_content(file_path, content):
                break  # Stop if we hit token limit
        except Exception as e:
            print(f"Warning: Failed to read {file_path}: {e}")
            
    return builder.build()
