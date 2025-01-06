"""Command for safely unmounting TouchFS filesystems."""
import os
import sys
import subprocess
import psutil
from pathlib import Path
from ..config.logger import setup_logging

def find_mount_processes(mount_point: str):
    """Find processes using the mount point.
    
    Args:
        mount_point: Path to the mount point
        
    Returns:
        List of (pid, process_name) tuples
    """
    using_processes = []
    mount_point = os.path.abspath(mount_point)
    
    for proc in psutil.process_iter(['pid', 'name', 'cwd', 'open_files']):
        try:
            # Check current working directory
            if proc.info['cwd'] == mount_point:
                using_processes.append((proc.pid, proc.info['name']))
                continue
                
            # Check open files
            for file in proc.info['open_files'] or []:
                if file.path.startswith(mount_point):
                    using_processes.append((proc.pid, proc.info['name']))
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
            
    return using_processes

def is_touchfs_mount(mount_point: str) -> bool:
    """Check if path is a TouchFS mount point.
    
    Args:
        mount_point: Path to check
        
    Returns:
        True if mount_point is a TouchFS mount, False otherwise
    """
    try:
        # Read /proc/mounts to check filesystem type
        with open('/proc/mounts', 'r') as f:
            for line in f:
                if mount_point in line and 'fuse' in line:
                    return True
    except Exception:
        pass
    return False

def unmount(mount_point: str, force: bool = False, debug: bool = False) -> int:
    """Safely unmount a TouchFS filesystem.
    
    Args:
        mount_point: Path to the mount point
        force: Force unmount even if filesystem is busy
        debug: Enable debug logging
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    logger = setup_logging(debug_stdout=debug)
    logger.info(f"Attempting to unmount {mount_point}")
    
    # Normalize path
    mount_point = os.path.abspath(mount_point)
    
    # Check if path exists
    if not os.path.exists(mount_point):
        logger.error(f"Mount point does not exist: {mount_point}")
        return 1
        
    # Check if it's actually mounted
    if not os.path.ismount(mount_point):
        logger.error(f"Not a mount point: {mount_point}")
        return 1
        
    # Verify it's a TouchFS mount
    if not is_touchfs_mount(mount_point):
        logger.error(f"Not a TouchFS mount point: {mount_point}")
        return 1
    
    # Check for processes using the mount
    using_processes = find_mount_processes(mount_point)
    if using_processes:
        msg = f"Found processes using mount point:"
        for pid, name in using_processes:
            msg += f"\n  - {name} (PID: {pid})"
        logger.warning(msg)
        
        if not force:
            logger.error("Use --force to unmount anyway")
            return 1
        else:
            logger.warning("Forcing unmount despite busy mount point")
    
    # Attempt unmount
    try:
        if force:
            cmd = ['fusermount', '-uz', mount_point]
        else:
            cmd = ['fusermount', '-u', mount_point]
            
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Unmount failed: {result.stderr}")
            return result.returncode
            
        logger.info("Successfully unmounted TouchFS")
        return 0
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Unmount failed with error: {e}")
        return e.returncode
    except Exception as e:
        logger.error(f"Unexpected error during unmount: {e}")
        return 1

def main():
    """Main entry point for touchfs_umount command."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Safely unmount a TouchFS filesystem'
    )
    parser.add_argument(
        'mountpoints',
        nargs='+',
        help='One or more TouchFS mount points to unmount'
    )
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force unmount even if filesystem is busy'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    # Process each mountpoint
    exit_code = 0
    for mountpoint in args.mountpoints:
        result = unmount(mountpoint, args.force, args.debug)
        if result != 0:
            exit_code = result
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
