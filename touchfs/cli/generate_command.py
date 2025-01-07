"""Command line interface for generating content for files.

This module provides a CLI interface for generating content for files using
the same content generation functionality as TouchFS mount points. Unlike the
touch command which only marks files for generation, this command directly
generates and writes the content.

Key Features:
1. Creates files if they don't exist
2. Generates content immediately using TouchFS content generation
3. Extends with --parents/-p flag to create parent directories (like mkdir -p)
4. Handles multiple files in a single command
5. Uses project context for intelligent content generation

The command is particularly useful for:
1. One-off content generation without mounting a TouchFS filesystem
2. Batch generating content for multiple files
3. Testing content generation results quickly
4. Creating files with generated content in non-existent directory structures
"""

import sys
import os
import argparse
from typing import Optional, List, Tuple, Dict, Any
from ..config.logger import setup_logging
from ..core.context import build_context
from ..content.plugins.default import DefaultGenerator
from ..models.filesystem import FileNode, FileAttrs, FileSystem

def create_file_with_content(path: str, create_parents: bool = False, context: Optional[str] = None, logger=None, openai_client=None) -> bool:
    """Create a file and generate its content.
    
    Args:
        path: Path to file to create and generate content for
        create_parents: Whether to create parent directories if they don't exist
        context: Optional context string to use for generation
        
    Returns:
        True if successful, False if error occurred
    """
    try:
        # Handle parent directories
        parent_dir = os.path.dirname(path)
        if parent_dir and not os.path.exists(parent_dir):
            if create_parents:
                os.makedirs(parent_dir)
            else:
                print(f"Error: Parent directory '{parent_dir}' does not exist", file=sys.stderr)
                print("Use --parents/-p to create parent directories", file=sys.stderr)
                return False

        # Create FileNode for generation
        node = FileNode(
            type="file",
            content="",  # Empty content triggers generation
            attrs=FileAttrs(st_mode="33188"),  # 644 permissions
            xattrs={}
        )

        # Create filesystem structure for context
        fs_structure = {path: node}
        
        # Add context files to fs_structure
        parent_dir = os.path.dirname(path)
        if os.path.exists(parent_dir):
            for file in os.listdir(parent_dir):
                file_path = os.path.join(parent_dir, file)
                if os.path.isfile(file_path) and file_path != path:
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        fs_structure[file] = FileNode(
                            type="file",
                            content=content,
                            attrs=FileAttrs(st_mode="33188"),  # 644 permissions
                            xattrs={}
                        )
                    except Exception as e:
                        logger.debug(f"Failed to read context file {file_path}: {e}")

        # Generate content
        generator = DefaultGenerator()
        try:
            content = generator.generate(path, node, fs_structure, client=openai_client)
            logger.debug(f"Content generated successfully for: {path}")

            # Write content to file
            with open(path, 'w') as f:
                f.write(content)
            logger.debug(f"Content written successfully to: {path}")
            print(f"Successfully generated content for '{path}'", file=sys.stderr)
            return True
        except Exception as e:
            print(f"Error generating content for '{path}': {e}", file=sys.stderr)
            # Create empty file on generation failure
            if not os.path.exists(path):
                with open(path, 'w') as f:
                    f.write('')
            return False
    except OSError as e:
        print(f"Error processing '{path}': {e}", file=sys.stderr)
        return False

def generate_main(files: List[str], force: bool = False, parents: bool = False, debug_stdout: bool = False, max_tokens: Optional[int] = None, openai_client=None) -> int:
    """Main entry point for generate command.
    
    This command uses TouchFS content generation to create files with generated
    content. Unlike the touch command which only marks files for generation,
    this command directly generates and writes the content.
    
    Args:
        files: List of files to generate content for
        force: Skip confirmation for non-touchfs paths
        parents: Create parent directories as needed
        debug_stdout: Enable debug output to stdout
        max_tokens: Maximum number of tokens to include in context
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Setup logging
        logger = setup_logging(debug_stdout=debug_stdout)
        logger.debug("==== TouchFS Generate Command Started ====")
        
        # Convert paths to absolute
        abs_paths = [os.path.abspath(path) for path in files]
        
        # Check parent directories first
        need_parents = False
        for path in abs_paths:
            parent_dir = os.path.dirname(path)
            if parent_dir and not os.path.exists(parent_dir):
                if not parents:
                    print(f"Error: Parent directory '{parent_dir}' does not exist", file=sys.stderr)
                    print("Use --parents/-p to create parent directories", file=sys.stderr)
                    return 0
                need_parents = True

        # Prompt for confirmation if not forcing
        if not force:
            print("\nThe following files will have content generated:", file=sys.stderr)
            for path in abs_paths:
                print(f"  {path}", file=sys.stderr)
            response = input("\nDo you want to continue? [Y/n] ")
            if response.lower() == 'n':
                print("No files will be generated", file=sys.stderr)
                return 0

        # Create parent directories if needed
        if need_parents and parents:
            for path in abs_paths:
                parent_dir = os.path.dirname(path)
                if parent_dir and not os.path.exists(parent_dir):
                    os.makedirs(parent_dir)
        
        # Build context from approved paths' directory
        if abs_paths:
            # Use parent directory of first path as context root
            context_root = os.path.dirname(abs_paths[0])
            try:
                context = build_context(context_root, max_tokens=max_tokens)
            except Exception as e:
                logger.warning(f"Failed to build context: {e}")
                context = None
        else:
            context = None

        # Process all approved paths
        had_error = False
        for path in abs_paths:
            if not create_file_with_content(path, create_parents=parents, context=context, logger=logger, openai_client=openai_client):
                had_error = True
                
        if not had_error:
            print("(Content generation complete)", file=sys.stderr)
            
        # Return 0 even if some paths failed, like touch does
        return 0
            
    except Exception as e:
        if debug_stdout:
            print(f"Error in generate command: {e}", file=sys.stderr)
        return 0  # Still return 0 like touch

def add_generate_parser(subparsers):
    """Add generate-related parsers to the CLI argument parser."""
    # Generate subcommand
    generate_parser = subparsers.add_parser(
        'generate',
        help='Generate content for files',
        description='Generate content for files using TouchFS content generation',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    generate_parser.add_argument(
        'files',
        nargs='+',
        help='Files to generate content for'
    )
    generate_parser.add_argument(
        '-p', '--parents',
        action='store_true',
        help='Create parent directories if needed'
    )
    generate_parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='Skip confirmation prompt'
    )
    generate_parser.add_argument(
        '--debug-stdout',
        action='store_true',
        help='Enable debug output'
    )
    generate_parser.add_argument(
        '-m', '--max-tokens',
        type=int,
        help='Maximum number of tokens to include in context'
    )
    generate_parser.set_defaults(func=lambda args: sys.exit(generate_main(
        files=args.files,
        force=args.force,
        parents=args.parents,
        debug_stdout=args.debug_stdout,
        max_tokens=args.max_tokens
    )))
    
    return generate_parser

def run(args=None):
    """Entry point for the command-line script."""
    if args is None:
        parser = argparse.ArgumentParser()
        add_generate_parser(parser.add_subparsers())
        args = parser.parse_args()
    sys.exit(generate_main(
        files=args.files,
        force=args.force,
        parents=args.parents,
        debug_stdout=args.debug_stdout,
        max_tokens=getattr(args, 'max_tokens', None)
    ))
