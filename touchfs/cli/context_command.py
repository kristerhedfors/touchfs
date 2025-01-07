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
from ..config.settings import DEFAULT_MAX_TOKENS

def context_main(directory: str = '.', max_tokens: int = DEFAULT_MAX_TOKENS, exclude: Optional[list] = None, include: Optional[list] = None, debug_stdout: bool = False, list_files: bool = False) -> int:
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
        include: List of glob patterns to include. When specified,
                only files matching these patterns will be included.
        debug_stdout: Enable debug output to stdout
        list_files: Only list file paths that would be included
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Setup logging with configurable debug output
        logger = setup_logging(debug_stdout=debug_stdout)
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
            exclude_patterns=exclude,
            include_patterns=include
        )
        
        # Output either file list or formatted context
        if list_files:
            # Extract file paths from formatted context
            lines = context.split('\n')
            for line in lines:
                if line.startswith('# File: '):
                    print(line[8:])  # Remove "# File: " prefix
        else:
            print(context)
        return 0
        
    except Exception as e:
        print(f"Error generating context: {e}", file=sys.stderr)
        return 1

def add_context_parser(subparsers):
    """Add context-related parsers to the CLI argument parser."""
    # Context subcommand
    context_parser = subparsers.add_parser(
        'context',
        help='Generate MCP-compliant context from directory',
        description='Generate context that follows Model Context Protocol (MCP) principles'
    )
    context_parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Directory to generate context from (default: current directory)'
    )
    context_parser.add_argument(
        '--max-tokens', '-m',
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help='Maximum number of tokens to include in context (affects both content and metadata)'
    )
    context_parser.add_argument(
        '--exclude', '-e',
        action='append',
        help='Glob patterns to exclude (can be specified multiple times)'
    )
    context_parser.add_argument(
        '--include', '-i',
        action='append',
        help='Glob patterns to include (can be specified multiple times). When specified, only matching files and files without extensions will be included.'
    )
    context_parser.add_argument(
        '--debug-stdout',
        action='store_true',
        help='Enable debug output to stdout'
    )
    context_parser.add_argument(
        '--list-files', '-l',
        action='store_true',
        help='Only list file paths that would be included in context'
    )
    context_parser.set_defaults(func=lambda args: sys.exit(context_main(
        directory=args.path,
        max_tokens=args.max_tokens,
        exclude=args.exclude,
        debug_stdout=args.debug_stdout,
        list_files=args.list_files,
        include=args.include
    )))
    
    return context_parser
