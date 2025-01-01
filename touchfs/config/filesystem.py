"""Filesystem-related configuration and utilities."""
import os
import json
import logging
from typing import Optional, Dict

logger = logging.getLogger("touchfs")

def find_nearest_prompt_file(path: str, fs_structure: dict) -> Optional[str]:
    """Find the nearest prompt file by traversing up the directory tree.
    
    Looks for files in this order at each directory level:
    1. .touchfs.prompt
    2. .prompt
    
    Args:
        path: Current file path
        fs_structure: Current filesystem structure
        
    Returns:
        Path to the nearest prompt file, or None if not found
    """
    logger.debug(f"Finding nearest prompt file for path: {path}")
    
    # Start with the directory containing our file
    current_dir = os.path.dirname(path)
    if current_dir == "":
        current_dir = "/"
    logger.debug(f"Starting in directory: {current_dir}")
    
    # First check in the current directory
    touchfs_prompt_path = os.path.join(current_dir, '.touchfs.prompt')
    prompt_path = os.path.join(current_dir, '.prompt')
    
    # Normalize paths (ensure single leading slash)
    touchfs_prompt_path = "/" + touchfs_prompt_path.lstrip("/")
    prompt_path = "/" + prompt_path.lstrip("/")
    
    logger.debug(f"Checking for prompt files in current dir: {current_dir}")
    if touchfs_prompt_path in fs_structure:
        logger.debug(f"Found .touchfs.prompt in current dir: {touchfs_prompt_path}")
        return touchfs_prompt_path
    if prompt_path in fs_structure:
        logger.debug(f"Found .prompt in current dir: {prompt_path}")
        return prompt_path
    
    # Then traverse up the directory tree using the filesystem structure
    while current_dir != "/":
        # Get parent directory from filesystem structure
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # Reached root
            break
            
        logger.debug(f"Moving to parent directory: {parent_dir}")
        
        # Check if parent exists and is a directory
        parent_node = fs_structure.get(parent_dir)
        if not parent_node:
            logger.debug(f"Parent directory {parent_dir} not found")
            break
            
        # Handle both dict and FileNode objects
        node_type = parent_node.get('type', '') if isinstance(parent_node, dict) else getattr(parent_node, 'type', '')
        if node_type != "directory":
            logger.debug(f"Parent directory {parent_dir} is not a directory")
            break
            
        # Check for prompt files in parent directory
        touchfs_prompt_path = os.path.join(parent_dir, '.touchfs.prompt')
        prompt_path = os.path.join(parent_dir, '.prompt')
        
        # Normalize paths
        touchfs_prompt_path = "/" + touchfs_prompt_path.lstrip("/")
        prompt_path = "/" + prompt_path.lstrip("/")
        
        if touchfs_prompt_path in fs_structure:
            logger.debug(f"Found .touchfs.prompt at: {touchfs_prompt_path}")
            return touchfs_prompt_path
        if prompt_path in fs_structure:
            logger.debug(f"Found .prompt at: {prompt_path}")
            return prompt_path
            
        current_dir = parent_dir
    
    # Finally check root if we haven't already
    if current_dir != "/":
        logger.debug("Checking root directory")
        if "/.touchfs.prompt" in fs_structure:
            logger.debug("Found .touchfs.prompt in root")
            return "/.touchfs.prompt"
        if "/.prompt" in fs_structure:
            logger.debug("Found .prompt in root")
            return "/.prompt"
    
    logger.debug("No prompt file found")
    return None

def find_nearest_model_file(path: str, fs_structure: dict) -> Optional[str]:
    """Find the nearest model file by traversing up the directory tree.
    
    Looks for files in this order at each directory level:
    1. .touchfs.model
    2. .model
    
    Args:
        path: Current file path (absolute FUSE path)
        fs_structure: Current filesystem structure
        
    Returns:
        Path to the nearest model file, or None if not found
    """
    logger.debug(f"Finding nearest model file for path: {path}")
    
    # Start with the directory containing our file
    current_dir = os.path.dirname(path)
    if current_dir == "":
        current_dir = "/"
    logger.debug(f"Starting in directory: {current_dir}")
    
    # First check in the current directory
    touchfs_model_path = os.path.join(current_dir, '.touchfs.model')
    model_path = os.path.join(current_dir, '.model')
    
    # Normalize paths (ensure single leading slash)
    touchfs_model_path = "/" + touchfs_model_path.lstrip("/")
    model_path = "/" + model_path.lstrip("/")
    
    logger.debug(f"Checking for model files in current dir: {current_dir}")
    if touchfs_model_path in fs_structure:
        logger.debug(f"Found .touchfs.model in current dir: {touchfs_model_path}")
        return touchfs_model_path
    if model_path in fs_structure:
        logger.debug(f"Found .model in current dir: {model_path}")
        return model_path
    
    # Then traverse up the directory tree using the filesystem structure
    while current_dir != "/":
        # Get parent directory from filesystem structure
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # Reached root
            break
            
        logger.debug(f"Moving to parent directory: {parent_dir}")
        
        # Check if parent exists and is a directory
        parent_node = fs_structure.get(parent_dir)
        if not parent_node:
            logger.debug(f"Parent directory {parent_dir} not found")
            break
            
        # Handle both dict and FileNode objects
        node_type = parent_node.get('type', '') if isinstance(parent_node, dict) else getattr(parent_node, 'type', '')
        if node_type != "directory":
            logger.debug(f"Parent directory {parent_dir} is not a directory")
            break
            
        # Check for model files in parent directory
        touchfs_model_path = os.path.join(parent_dir, '.touchfs.model')
        model_path = os.path.join(parent_dir, '.model')
        
        # Normalize paths
        touchfs_model_path = "/" + touchfs_model_path.lstrip("/")
        model_path = "/" + model_path.lstrip("/")
        
        if touchfs_model_path in fs_structure:
            logger.debug(f"Found .touchfs.model at: {touchfs_model_path}")
            return touchfs_model_path
        if model_path in fs_structure:
            logger.debug(f"Found .model at: {model_path}")
            return model_path
            
        current_dir = parent_dir
    
    # Finally check root if we haven't already
    if current_dir != "/":
        logger.debug("Checking root directory")
        if "/.touchfs.model" in fs_structure:
            logger.debug("Found .touchfs.model in root")
            return "/.touchfs.model"
        if "/.model" in fs_structure:
            logger.debug("Found .model in root")
            return "/.model"
    
    logger.debug("No model file found")
    return None

def format_fs_structure(fs_structure: dict) -> str:
    """Format filesystem structure, excluding .touchfs folders."""
    # First convert all nodes to dicts
    dumped_structure = {p: n.model_dump() for p, n in fs_structure.items()}
    
    # Then filter out .touchfs paths - handle all possible path formats
    filtered_structure = {
        p: n for p, n in dumped_structure.items()
        if not any(p.endswith('.touchfs') or '.touchfs/' in p or p == '.touchfs')
    }
    
    return json.dumps(filtered_structure, indent=2)
