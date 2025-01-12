"""Command line interface for TouchFS generate command."""

import sys
import os
import argparse
from typing import List, Optional

from ...config.logger import setup_logging
from ...core.context import build_context
from ..touch.path_utils import create_file_with_xattr
from ...content.filesystem_generator import generate_filesystem_list

def generate_main(
    files: List[str], 
    force: bool = False, 
    parents: bool = False, 
    debug_stdout: bool = False, 
    max_tokens: Optional[int] = None,
    filesystem_generation_prompt: Optional[str] = None,
    yes: bool = False,
    no_content: bool = False,
    openai_client=None
) -> int:
    """Main entry point for generate command.
    
    This command supports two modes:
    1. File Generation Mode: Generate content for specific files
    2. Filesystem Generation Mode (-F): Generate directory structure from prompt
    
    Args:
        files: Files to generate content for, or target directory when using -F
        force: Skip confirmation prompt
        parents: Create parent directories if needed
        debug_stdout: Enable debug output to stdout
        max_tokens: Maximum number of tokens to include in context
        filesystem_generation_prompt: Optional prompt for filesystem generation
        yes: Auto-confirm filesystem structure without prompting
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Setup logging
        logger = setup_logging(command_name="generate", debug_stdout=debug_stdout)
        logger.debug("==== TouchFS Generate Command Started ====")

        # Handle filesystem generation if prompt provided
        if filesystem_generation_prompt:
            if len(files) != 1:
                print("Error: When using -F/--filesystem-generation-prompt, exactly one target directory must be specified", file=sys.stderr)
                return 1

            target_dir = os.path.abspath(files[0])
            if os.path.exists(target_dir):
                if os.path.isfile(target_dir):
                    print(f"Error: '{target_dir}' exists and is a file", file=sys.stderr)
                    return 1
                if os.listdir(target_dir):
                    print(f"Error: '{target_dir}' exists and is not empty", file=sys.stderr)
                    return 1
            else:
                if not parents:
                    parent_dir = os.path.dirname(target_dir)
                    if not os.path.exists(parent_dir):
                        print(f"Error: Parent directory '{parent_dir}' does not exist", file=sys.stderr)
                        print("Use --parents/-p to create parent directories", file=sys.stderr)
                        # Continue like touch command - don't return error

            try:
                # Generate filesystem structure
                print(f"\nGenerating filesystem from prompt: {filesystem_generation_prompt[:50]}...", file=sys.stdout)
                sys.stdout.flush()
                
                fs_list = generate_filesystem_list(filesystem_generation_prompt, client=openai_client)
                
                # Convert flat file list to tree structure for visualization
                tree_data = {"data": {"/": {"type": "directory", "children": {}}}}
                for file in sorted(fs_list.files):
                    current = tree_data["data"]["/"]
                    parts = file.split('/')
                    path = "/"
                    
                    # Build directory structure
                    for i, part in enumerate(parts[:-1]):
                        path = os.path.join(path, part).replace("\\", "/")
                        if path not in tree_data["data"]:
                            tree_data["data"][path] = {
                                "type": "directory",
                                "children": {}
                            }
                        if part not in current["children"]:
                            current["children"][part] = path
                        current = tree_data["data"][path]
                    
                    # Add file
                    file_path = "/" + file
                    tree_data["data"][file_path] = {
                        "type": "file",
                        "content": None
                    }
                    current["children"][parts[-1]] = file_path
                
                # Format and display tree
                from ..mount.filesystem import format_simple_tree
                tree_visualization = format_simple_tree(tree_data["data"])
                print("\nGenerated Filesystem Structure:")
                print(tree_visualization)
                
                if not yes:
                    print("\nAccept this structure? Type 'y' to accept, 'n' to reject, or enter new instructions: ", end='')
                    sys.stdout.flush()
                    response = input().strip().lower()
                    if response == 'n':
                        print("Operation cancelled", file=sys.stderr)
                        return 1
                    elif response != 'y':
                        print("\nRefining structure not yet supported in generate command", file=sys.stderr)
                        print("Use mount command for interactive filesystem refinement", file=sys.stderr)
                        return 1
                
                # Create target directory and its parent if needed
                os.makedirs(target_dir, exist_ok=True)

                # Create all files from the list
                for rel_path in fs_list.files:
                    abs_path = os.path.join(target_dir, rel_path)
                    
                    # Create parent directories
                    parent_dir = os.path.dirname(abs_path)
                    if parent_dir:
                        os.makedirs(parent_dir, exist_ok=True)
                    
                    # Create and optionally generate content for file
                    import time
                    start_time = time.time()
                    context = build_context(parent_dir, max_tokens=max_tokens) if not no_content else None
                    result, _, content = create_file_with_xattr(abs_path, create_parents=True, 
                                                              context=context, logger=logger,
                                                              generate_content=not no_content)
                    if result and content:
                        lines = content.count('\n') + 1
                        chars = len(content)
                        duration = time.time() - start_time
                        print(f"Generated {abs_path}: {chars} chars, {lines} lines in {duration:.2f}s")
                    elif not no_content:
                        print(f"Warning: No content was generated for {abs_path}")
                    else:
                        print(f"Created empty file: {abs_path}")

                print(f"\nFilesystem structure created in '{target_dir}'", file=sys.stderr)
                return 0
            except Exception as e:
                print(f"Error creating filesystem structure: {e}", file=sys.stderr)
                return 1

        # Regular file generation mode
        abs_paths = [os.path.abspath(path) for path in files]
        
        # Check parent directories first
        need_parents = False
        for path in abs_paths:
            parent_dir = os.path.dirname(path)
            if parent_dir and not os.path.exists(parent_dir):
                if not parents:
                    print(f"Error: Parent directory '{parent_dir}' does not exist", file=sys.stderr)
                    print("Use --parents/-p to create parent directories", file=sys.stderr)
                    # Continue like touch command - don't return error
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
            # Use touch command's file creation utility
            import time
            start_time = time.time()
            result, _, content = create_file_with_xattr(path, create_parents=parents, context=context, 
                                                      logger=logger, generate_content=not no_content)
            if not result:
                had_error = True
            elif content:
                lines = content.count('\n') + 1
                chars = len(content)
                duration = time.time() - start_time
                print(f"Generated {path}: {chars} chars, {lines} lines in {duration:.2f}s")
            elif not no_content:
                print(f"Warning: No content was generated for {path}")
            else:
                print(f"Created empty file: {path}")
                
        if not had_error:
            print("(Generation complete)", file=sys.stderr)
            
        return 0
            
    except Exception as e:
        if debug_stdout:
            print(f"Error in generate command: {e}", file=sys.stderr)
        return 1

def add_generate_parser(subparsers):
    """Add generate-related parsers to the CLI argument parser."""
    generate_parser = subparsers.add_parser(
        'generate',
        help='Generate content for files or create filesystem structure',
        description='''
Generate content for files using TouchFS content generation.

Two modes of operation:
1. File Generation Mode:
   Generate content for specific files. Each file will be created if it doesn't
   exist and populated with AI-generated content based on context.

2. Filesystem Generation Mode (-F):
   Generate an entire filesystem structure from a prompt. This will create
   directories and files according to the generated structure. Files will be
   created empty initially, with content generated when accessed.
''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    generate_parser.add_argument(
        'files',
        nargs='+',
        help='Files to generate content for, or target directory when using -F'
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
    generate_parser.add_argument(
        '-F', '--filesystem-generation-prompt',
        type=str,
        help='Generate filesystem structure from prompt in target directory'
    )
    generate_parser.add_argument(
        '-y', '--yes',
        action='store_true',
        help='Auto-confirm filesystem structure without prompting (only with -F)'
    )
    generate_parser.add_argument(
        '-n', '--no-content',
        action='store_true',
        help='Create empty files without generating content'
    )
    generate_parser.set_defaults(func=lambda args: sys.exit(generate_main(
        files=args.files,
        force=args.force,
        parents=args.parents,
        debug_stdout=args.debug_stdout,
        max_tokens=args.max_tokens,
        filesystem_generation_prompt=args.filesystem_generation_prompt,
        yes=args.yes,
        no_content=args.no_content
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
        max_tokens=getattr(args, 'max_tokens', None),
        filesystem_generation_prompt=getattr(args, 'filesystem_generation_prompt', None),
        yes=getattr(args, 'yes', False),
        no_content=getattr(args, 'no_content', False)
    ))
