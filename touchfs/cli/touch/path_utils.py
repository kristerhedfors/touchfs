"""Path management utilities for TouchFS touch command."""

import os
import sys
from typing import List, Tuple, Optional
from logging import Logger

def is_path_in_touchfs(path: str, logger: Optional[Logger] = None) -> bool:
    """Check if a path is within a mounted touchfs filesystem.
    
    Args:
        path: Path to check
        logger: Optional logger for debug output
        
    Returns:
        True if path is within a touchfs mount, False otherwise
    """
    try:
        # Get absolute path and resolve any symlinks
        abs_path = os.path.realpath(path)
        if logger:
            logger.debug(f"Checking if path is in touchfs: {abs_path}")
        
        # Walk up directory tree checking for .touchfs marker
        current = abs_path
        while current != '/':
            marker_path = os.path.join(current, '.touchfs')
            if logger:
                logger.debug(f"Checking for marker at: {marker_path}")
            if os.path.exists(marker_path):
                if logger:
                    logger.debug(f"Found touchfs marker at: {marker_path}")
                return True
            parent = os.path.dirname(current)
            if parent == current:  # Handle root directory case
                if logger:
                    logger.debug("Reached root directory")
                break
            current = parent
            
        # Also check the root directory
        root_marker = os.path.join('/', '.touchfs')
        if logger:
            logger.debug(f"Checking root marker: {root_marker}")
        if os.path.exists(root_marker):
            if logger:
                logger.debug("Found touchfs marker in root directory")
            return True
            
        if logger:
            logger.debug("No touchfs marker found")
        return False
    except Exception as e:
        print(f"Warning: Error checking if path is in touchfs: {e}", file=sys.stderr)
        return False

def categorize_paths(paths: List[str], logger: Optional[Logger] = None) -> Tuple[List[str], List[str]]:
    """Categorize paths into touchfs and non-touchfs lists.
    
    Args:
        paths: List of paths to categorize
        logger: Optional logger for debug output
        
    Returns:
        Tuple of (touchfs_paths, non_touchfs_paths)
    """
    touchfs_paths = []
    non_touchfs_paths = []
    
    for path in paths:
        abs_path = os.path.abspath(path)
        if logger:
            logger.debug(f"Checking path: {abs_path}")
            
        if is_path_in_touchfs(abs_path, logger=logger):
            if logger:
                logger.debug(f"Path is in touchfs: {abs_path}")
            touchfs_paths.append(abs_path)
        else:
            if logger:
                logger.debug(f"Path is not in touchfs: {abs_path}")
            non_touchfs_paths.append(abs_path)
            
    if logger:
        logger.debug(f"TouchFS paths: {touchfs_paths}")
        logger.debug(f"Non-TouchFS paths: {non_touchfs_paths}")
            
    return touchfs_paths, non_touchfs_paths

def create_file_with_xattr(path: str, create_parents: bool = False, context: Optional[str] = None, 
                          logger: Optional[Logger] = None, create_all: bool = False, 
                          generate_content: bool = False) -> Tuple[bool, bool, Optional[str]]:
    """Create a file and optionally generate content.
    
    Args:
        path: Path to file to create and mark
        create_parents: Whether to create parent directories if they don't exist
        context: Optional context string to store in xattr
        logger: Optional logger for debug output
        create_all: Whether to create all parent directories without prompting
        generate_content: Whether to generate content for the file
        
    Returns:
        Tuple of (success, create_all, content) where:
            success: True if successful, False if error occurred
            create_all: Updated create_all flag based on user input
            content: Generated content if successful and generate_content=True, None otherwise
    """
    try:
        # Handle parent directories
        parent_dir = os.path.dirname(path)
        if parent_dir and not os.path.exists(parent_dir):
            if create_parents:
                os.makedirs(parent_dir)
            elif create_all:
                os.makedirs(parent_dir)
            else:
                # Prompt for directory creation
                print(f"\nDirectory '{parent_dir}' does not exist.", file=sys.stderr)
                while True:
                    response = input("Create directory? [y/n/a] (a=yes to all) ").lower()
                    if response == 'y':
                        os.makedirs(parent_dir)
                        break
                    elif response == 'n':
                        print(f"Skipping '{path}' - directory not created", file=sys.stderr)
                        return False, create_all
                    elif response == 'a':
                        os.makedirs(parent_dir)
                        # Create file with create_all=True
                        success, new_create_all, _ = create_file_with_xattr(path, create_parents=False, context=context, 
                                                                          logger=logger, create_all=True)
                        return success, True  # Return True for create_all regardless of recursive result
                    else:
                        print("Please answer y, n, or a", file=sys.stderr)
            
        # Create file and optionally generate content
        try:
            content = None
            if not os.path.exists(path):
                logger.debug(f"Creating file: {path}") if logger else None
                
                generated_content = None
                if generate_content:
                    try:
                        from ...content.generator import generate_content as gen_content
                        generated_content = gen_content(path, context)
                        with open(path, 'w') as f:
                            f.write(generated_content)
                        logger.debug(f"Generated content for: {path}") if logger else None
                    except Exception as e:
                        error_msg = f"Error generating content: {e}"
                        logger.error(error_msg) if logger else None
                        print(error_msg, file=sys.stderr)
                        # Fall back to empty file on generation error
                        with open(path, 'w') as f:
                            f.write('')
                        generated_content = None
                else:
                    with open(path, 'w') as f:
                        f.write('')  # Explicitly write empty content
                        
                logger.debug(f"File created successfully: {path}") if logger else None
                
            # Set xattrs
            logger.debug(f"Setting xattrs for: {path}") if logger else None
            try:
                os.setxattr(path, 'touchfs.generate_content', b'true')
                if context:
                    os.setxattr(path, 'touchfs.context', context.encode('utf-8'))
                logger.debug(f"Xattrs set successfully for: {path}") if logger else None
            except OSError as e:
                if e.errno == 95:  # Operation not supported
                    print(f"Warning: Extended attributes not supported for '{path}'", file=sys.stderr)
                    print(f"Successfully created '{path}' but could not mark for generation", file=sys.stderr)
                else:
                    raise
            
            if generate_content and generated_content:
                print(f"Successfully generated content for '{path}'", file=sys.stderr)
            elif not generate_content:
                print(f"Successfully marked '{path}' for TouchFS content generation", file=sys.stderr)
            return True, create_all, generated_content
        except OSError as e:
            if e.errno == 95:  # Operation not supported
                # Create file but don't fail if xattrs aren't supported
                print(f"Warning: Extended attributes not supported for '{path}'", file=sys.stderr)
                print(f"Successfully created '{path}' but could not mark for generation", file=sys.stderr)
                return True, create_all, None
            raise
    except OSError as e:
        print(f"Error processing '{path}': {e}", file=sys.stderr)
        return False, create_all, None
