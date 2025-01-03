"""Command line interface for MCP-compliant context generation.

This module provides the CLI interface for generating context that follows
Model Context Protocol (MCP) principles, focusing on:
1. Structured file content collection
2. MCP-compliant output formatting
3. Resource organization and metadata

The context command generates a JSON structure containing:
- File contents as MCP resources with URIs and metadata
- Token usage statistics
- File collection metadata
"""

import sys
import os
import argparse
import json
from typing import Optional
from ..core.context import build_context
from ..config.logger import setup_logging

def parse_args() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description='Generate MCP-compliant context from files for LLM content generation',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory to generate context from (default: current directory)'
    )
    parser.add_argument(
        '--max-tokens', '-m',
        type=int,
        default=8000,
        help='Maximum number of tokens to include in context (affects both content and metadata)'
    )
    parser.add_argument(
        '--exclude', '-e',
        action='append',
        help='Glob patterns to exclude (can be specified multiple times)'
    )
    parser.add_argument(
        '--debug-stderr',
        action='store_true',
        help='Enable debug logging to stderr'
    )
    return parser.parse_args()

def main(directory: str = '.', max_tokens: int = 8000, exclude: Optional[list] = None, debug_stderr: bool = False) -> int:
    """Main entry point for context command.
    
    Orchestrates the context generation process:
    1. Sets up logging and validates inputs
    2. Collects file contents following MCP principles
    3. Generates structured, MCP-compliant output
    
    The generated context follows MCP format with:
    - version: Format version identifier
    - metadata: Context generation statistics
    - resources: Array of file contents with metadata
    
    Args:
        directory: Directory to generate context from
        max_tokens: Maximum tokens to include
        exclude: List of glob patterns to exclude
        debug_stderr: Enable debug logging to stderr
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Setup logging
        logger = setup_logging(debug_stderr=debug_stderr)
        logger.debug("==== TouchFS Context Command Started ====")
        
        # Get absolute path
        directory = os.path.abspath(directory)
        if not os.path.exists(directory):
            print(f"Error: Directory '{directory}' does not exist", file=sys.stderr)
            return 1
            
        # Build context in MCP format
        context = build_context(
            directory=directory,
            max_tokens=max_tokens,
            exclude_patterns=exclude
        )
        
        # Output the formatted context
        print(context)
        return 0
        
    except Exception as e:
        if debug_stderr:
            print(f"Error generating context: {e}", file=sys.stderr)
        return 1

def run():
    """Entry point for the command-line script."""
    args = parse_args()
    sys.exit(main(
        directory=args.directory,
        max_tokens=args.max_tokens,
        exclude=args.exclude,
        debug_stderr=args.debug_stderr
    ))
