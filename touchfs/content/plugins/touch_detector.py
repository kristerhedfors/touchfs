"""Plugin for detecting and handling system touch command operations."""
import os
import psutil
import logging
import time
from typing import Dict, List, Optional
from contextlib import contextmanager

from ...models.filesystem import FileNode
from .base import BaseContentGenerator, OverlayNode

@contextmanager
def find_touch_processes():
    """Find all touch processes currently running.
    
    Yields:
        List of (touch_proc, parent_proc) tuples
    """
    touch_procs = []
    try:
        for proc in psutil.process_iter(['name', 'pid', 'ppid']):
            if proc.info['name'] == 'touch':
                try:
                    parent = psutil.Process(proc.info['ppid'])
                    touch_procs.append((proc, parent))
                except psutil.NoSuchProcess:
                    continue
        yield touch_procs
    finally:
        # Process objects don't need explicit cleanup
        pass

def is_being_touched(path: str, mount_point: str, logger: Optional[logging.Logger] = None) -> bool:
    """Check if path is being accessed by a touch process.
    
    Args:
        path: FUSE path to check
        mount_point: FUSE mount point
        logger: Optional logger instance
        
    Returns:
        bool: True if a touch process is accessing this path
    """
    try:
        # Normalize all paths to absolute
        abs_mount = os.path.abspath(mount_point)
        rel_path = path.lstrip('/')  # Remove leading slash
        sys_path = os.path.join(abs_mount, rel_path)
        sys_path = os.path.abspath(sys_path)
        
        if logger:
            logger.debug(f"Checking touch status for {path} (sys_path: {sys_path})")
        
        # Add a small delay to ensure we can catch the touch process
        time.sleep(0.1)
        
        # Use context manager to safely handle process resources
        with find_touch_processes() as touch_procs:
            if logger:
                logger.debug(f"Found {len(touch_procs)} touch processes")
            
            # Look for our path in touch process open files
            for touch_proc, parent_proc in touch_procs:
                if logger:
                    try:
                        logger.debug(f"Examining touch process {touch_proc.pid}")
                        logger.debug(f"Parent process: {parent_proc.pid} ({parent_proc.name()})")
                    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                        logger.debug(f"Error accessing process info: {e}")
                        continue
                
                try:
                    # Check if touch command targets our file
                    cmdline = touch_proc.cmdline()
                    if logger:
                        logger.debug(f"Touch process cmdline: {cmdline}")
                        logger.debug(f"Touch process status: {touch_proc.status()}")
                        logger.debug(f"Touch process create time: {touch_proc.create_time()}")
                    
                    # Look for our path in command line args
                    try:
                        # Get the touch process's current working directory
                        touch_cwd = touch_proc.cwd()
                        if logger:
                            logger.debug(f"Touch process {touch_proc.pid} cwd: {touch_cwd}")
                        
                        # Handle paths relative to the mount point
                        for arg in cmdline[1:]:  # Skip the 'touch' command itself
                            try:
                                # Get absolute path of touch target
                                abs_target = os.path.abspath(os.path.join(touch_cwd, arg))
                                
                                if logger:
                                    logger.debug(f"Processing touch target: {arg}")
                                    logger.debug(f"Absolute target path: {abs_target}")
                                    logger.debug(f"System path to check: {sys_path}")
                                    logger.debug(f"Touch CWD: {touch_cwd}")
                                    logger.debug(f"Mount point: {abs_mount}")
                                
                                # Check if either:
                                # 1. The touch command is targeting our exact file
                                # 2. The touch command is run from inside mount point and targets match
                                if sys_path == abs_target:
                                    if logger:
                                        logger.debug(f"Touch command targets our file: {sys_path}")
                                    return True
                                
                                # Convert both paths to be relative to mount point for comparison
                                if touch_cwd.startswith(abs_mount):
                                    try:
                                        # Get target path relative to mount point
                                        target_rel = os.path.relpath(abs_target, abs_mount)
                                        if logger:
                                            logger.debug(f"Comparing relative paths: {rel_path} vs {target_rel}")
                                        if rel_path == target_rel:
                                            if logger:
                                                logger.debug(f"Touch command targets our file via relative path")
                                            return True
                                    except ValueError as e:
                                        if logger:
                                            logger.debug(f"Error calculating relative path: {e}")
                            except (ValueError, OSError) as e:
                                # Handle case where target is outside mount point or other path errors
                                if logger:
                                    logger.debug(f"Error processing path {arg}: {e}")
                                continue
                    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                        if logger:
                            logger.debug(f"Error getting touch process cwd: {e}")
                    
                    # Also check open files as backup
                    open_files = touch_proc.open_files() + parent_proc.open_files()
                    if logger:
                        logger.debug(f"Open files for touch process {touch_proc.pid}: {[f.path for f in open_files]}")
                    
                    for f in open_files:
                        abs_path = os.path.abspath(f.path)
                        if abs_path == sys_path:
                            if logger:
                                logger.debug(f"Found our file in open files: {abs_path}")
                            return True
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    if logger:
                        logger.debug(f"Error accessing process {touch_proc.pid}: {e}")
                    continue
                    
    except Exception as e:
        if logger:
            logger.error(f"Error checking touch status: {e}")
    
    if logger:
        logger.debug(f"No touch operation detected for {path}")
    return False

class TouchDetectorPlugin(BaseContentGenerator):
    """Plugin that detects system touch commands and marks files for generation."""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
    
    def generator_name(self) -> str:
        """Return the unique name of this generator."""
        return "touch_detector"
    
    def can_handle(self, path: str, node: FileNode) -> bool:
        """Check if this file is being touched by a system touch command.
        
        Args:
            path: Absolute path of the file
            node: FileNode instance containing file metadata
            
        Returns:
            bool: True if this file is being touched
        """
        # Get mount point from base context
        mount_point = self.base.mount_point if self.base else None
        if not mount_point:
            self.logger.warning("No mount point available")
            return False
            
        return is_being_touched(path, mount_point, self.logger)
    
    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        """Mark file for generation when touched.
        
        Args:
            path: Absolute path of the file
            node: FileNode instance containing file metadata
            fs_structure: Complete filesystem structure
            
        Returns:
            str: Empty string since we just mark for generation
        """
        # Mark file for generation by setting generator xattr
        if node.xattrs is None:
            node.xattrs = {}
        node.xattrs["generator"] = "default"
        
        return ""
    
    def get_overlay_files(self) -> List[OverlayNode]:
        """No overlay files needed."""
        return []
    
    def get_prompt(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        """No prompt needed since we just mark for generation."""
        return ""
