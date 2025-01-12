"""Command line interface for TouchFS touch command."""

import sys
import os
import argparse
from typing import List, Optional

from ...config.logger import setup_logging
from ...core.context import build_context
from .path_utils import categorize_paths, create_file_with_xattr
from .ui import generate_filename_suggestions, display_menu

def touch_main(files: List[str], force: bool = False, parents: bool = False, 
               debug_stdout: bool = False, max_tokens: Optional[int] = None) -> int:
    """Main entry point for touch command.
    
    This command sets the generate_content xattr that TouchFS uses to identify
    files that should have their content generated. Within a TouchFS filesystem,
    this is automatically set by the touch command - this CLI provides an
    explicit way to set the same marker.
    
    Args:
        files: List of files to mark for generation
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
        logger.debug("==== TouchFS Touch Command Started ====")
        
        # Handle directory-only arguments
        if len(files) == 1 and os.path.isdir(files[0]):
            directory = files[0]
            logger.debug(f"Directory-only argument detected: {directory}")
            
            previous_selections = []
            while True:
                # Generate suggestions based on previous selection
                suggestions = generate_filename_suggestions(
                    directory,
                    selected_filenames=previous_selections,
                    max_tokens=max_tokens,
                    logger=logger
                )
                if not suggestions:
                    logger.debug("No suggestions generated")
                    return 0

                try:
                    # Display menu and get selection
                    selected, regenerate = display_menu(suggestions, allow_multiple=True)
                except Exception as e:
                    logger.error(f"Error in menu display: {e}")
                    return 0

                if selected is None:
                    logger.debug("User cancelled selection")
                    return 0
                    
                if len(selected) == 0:
                    logger.debug("No selection made")
                    return 0
                
                # Get selected filenames
                current_selections = [suggestions[i] for i in selected]
                
                # If not regenerating, create selected files
                if not regenerate:
                    files = [os.path.join(directory, f) for f in current_selections]
                    break
                
                # Store current selections for next iteration
                previous_selections = current_selections
                continue
        
        # Categorize paths
        touchfs_paths, non_touchfs_paths = categorize_paths(files, logger=logger)
        
        # Warn about non-touchfs paths but proceed without confirmation
        if non_touchfs_paths:
            print("Warning: The following paths are not within a TouchFS filesystem (no parent directory contains a .touchfs folder):", file=sys.stderr)
            for path in non_touchfs_paths:
                print(f"  {path}", file=sys.stderr)
        
        # Prompt for touchfs paths if any exist and we're not forcing
        if touchfs_paths and not force:
            print("\nThe following paths will be marked for generation:", file=sys.stderr)
            for path in touchfs_paths:
                print(f"  {path}", file=sys.stderr)
            response = input("\nDo you want to continue? [Y/n] ")
            if response.lower() == 'n':
                print("No paths approved for marking", file=sys.stderr)
                return 0
        
        # Build context from approved paths' directory
        all_paths = non_touchfs_paths + touchfs_paths
        if all_paths:
            # Use parent directory of first path as context root
            context_root = os.path.dirname(all_paths[0])
            try:
                context = build_context(context_root, max_tokens=max_tokens)
            except Exception as e:
                logger.warning(f"Failed to build context: {e}")
                context = None
        else:
            context = None

        # Process all approved paths
        had_error = False
        create_all = False  # Track if user selected 'a' for any path
        for path in all_paths:
            result, new_create_all, _ = create_file_with_xattr(path, create_parents=parents, context=context, 
                                                             logger=logger, create_all=create_all)
            if not result:
                # If user said 'n' to directory creation, stop processing remaining paths
                if not create_all and not parents:
                    break
                had_error = True
            if new_create_all:  # If user selected 'a', use it for all subsequent files
                create_all = True
                
        if not had_error:
            print("(This is equivalent to using touch within a TouchFS filesystem)", file=sys.stderr)
            
        # Return 0 even if some paths failed, like touch does
        return 0
            
    except Exception as e:
        if debug_stdout:
            print(f"Error in touch command: {e}", file=sys.stderr)
        return 0  # Still return 0 like touch

def add_touch_parser(subparsers):
    """Add touch-related parsers to the CLI argument parser."""
    # Touch subcommand
    touch_parser = subparsers.add_parser(
        'touch',
        help='Mark files for content generation',
        description='Mark files for TouchFS content generation',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    touch_parser.add_argument(
        'files',
        nargs='+',
        help='Files to mark for generation'
    )
    touch_parser.add_argument(
        '-p', '--parents',
        action='store_true',
        help='Create parent directories if needed'
    )
    touch_parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='Skip confirmation for non-touchfs paths'
    )
    touch_parser.add_argument(
        '--debug-stdout',
        action='store_true',
        help='Enable debug output'
    )
    touch_parser.add_argument(
        '-m', '--max-tokens',
        type=int,
        help='Maximum number of tokens to include in context'
    )
    touch_parser.set_defaults(func=lambda args: sys.exit(touch_main(
        files=args.files,
        force=args.force,
        parents=args.parents,
        debug_stdout=args.debug_stdout,
        max_tokens=args.max_tokens
    )))
    
    return touch_parser

def run(args=None):
    """Entry point for the command-line script."""
    if args is None:
        parser = argparse.ArgumentParser()
        add_touch_parser(parser.add_subparsers())
        args = parser.parse_args()
    sys.exit(touch_main(
        files=args.files,
        force=args.force,
        parents=args.parents,
        debug_stdout=args.debug_stdout,
        max_tokens=getattr(args, 'max_tokens', None)
    ))
