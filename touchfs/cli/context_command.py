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

def add_arguments(parser):
    """Add context command arguments to parser.
    
    Args:
        parser: ArgumentParser instance to add arguments to
    """
    parser.add_argument(
        'path',
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
        '--debug-stdout',
        action='store_true',
        help='Enable debug output to stdout'
    )

def main(directory: str = '.', max_tokens: int = 8000, exclude: Optional[list] = None, debug_stdout: bool = False) -> int:
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
            logger=logger
        )
        
        # Output the formatted context
        print(context)
        return 0
        
    except Exception as e:
        print(f"Error generating context: {e}", file=sys.stderr)
        return 1

def run(args):
    """Entry point for the command-line script."""
    sys.exit(main(
        directory=args.path,
        max_tokens=args.max_tokens,
        exclude=args.exclude,
        debug_stdout=args.debug_stdout
    ))
