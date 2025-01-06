#!/usr/bin/env python3
"""Mount command implementation for TouchFS CLI."""
import sys
import os
from typing import Optional, List
from fuse import FUSE
import subprocess

from ..core.memory import Memory
from ..content.generator import generate_filesystem
from ..config.settings import get_prompt, get_filesystem_generation_prompt, set_cache_enabled, get_fsname
from ..config.logger import setup_logging

def get_mounted_touchfs() -> List[tuple[str, str, str]]:
    """Get list of currently mounted touchfs filesystems with their PIDs and commands."""
    mounted = set()  # Use set to avoid duplicates
    try:
        with open('/proc/mounts', 'r') as f:
            for line in f:
                fields = line.split()
                # Check if it's our TouchFS mount by looking at the filesystem type
                if len(fields) >= 6 and fields[2] == 'fuse' and fields[0] == get_fsname():
                    mountpoint = fields[1]
                    # Get PID and command from /proc/*/mountinfo
                    for pid in os.listdir('/proc'):
                        if not pid.isdigit():
                            continue
                        try:
                            with open(f'/proc/{pid}/mountinfo', 'r') as mf:
                                if mountpoint not in mf.read():
                                    continue
                                # Get command line
                                with open(f'/proc/{pid}/cmdline', 'r') as cf:
                                    cmdline = cf.read().replace('\0', ' ').strip()
                                    # Only include processes that are actually running touchfs mount
                                    # and exclude temporary mounts
                                    if 'touchfs mount' in cmdline and not mountpoint.startswith('/tmp/'):
                                        mounted.add((mountpoint, pid, cmdline))
                        except (IOError, OSError):
                            continue
    except Exception as e:
        print(f"Error getting mounted filesystems: {e}", file=sys.stderr)
    return mounted

def mount_main(mountpoint: Optional[str] = None, prompt_arg: Optional[str] = None, 
             filesystem_generation_prompt: Optional[str] = None, 
             foreground: bool = False, unmount: bool = False, 
             allow_other: bool = False, allow_root: bool = False, 
             nothreads: bool = False, nonempty: bool = False, 
             force: bool = False) -> int:
    """Main entry point for TouchFS mount command.
    
    Args:
        mountpoint: Directory where the filesystem will be mounted
        prompt_arg: Optional prompt argument from command line
        filesystem_generation_prompt: Optional prompt for filesystem generation
        foreground: Whether to run in foreground (also enables debug output to stdout)
        unmount: Whether to unmount instead of mount
        allow_other: Allow other users to access the mount
        allow_root: Allow root to access the mount
        nothreads: Disable multi-threading
        nonempty: Allow mounting over non-empty directory
        force: Force unmount even if busy
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    # If no mountpoint provided, list mounted filesystems
    if not mountpoint:
        mounted = get_mounted_touchfs()
        if mounted:
            print("Currently mounted touchfs filesystems:")
            for mp, pid, cmd in sorted(mounted):  # Sort for consistent output
                print(f"{mp} {pid} {cmd}")
        else:
            print("No touchfs filesystems currently mounted")
        return 0

    # Check if mountpoint exists (skip check for unmount)
    if not unmount and not os.path.exists(mountpoint):
        print(f"{mountpoint}: No such file or directory", file=sys.stderr)
        sys.exit(1)  # Use sys.exit to ensure non-zero exit code propagates
        
    # Handle unmount request
    if unmount:
        from .umount_command import unmount as unmount_fs
        return unmount_fs(mountpoint, force=force)

    # Setup logging (logs are always rotated for each invocation)
    try:
        if foreground:
            print("Starting TouchFS with debug logging to stdout...", file=sys.stdout)
        # Check for test tag
        test_tag = os.environ.get('TOUCHFS_TEST_TAG')
        logger = setup_logging(test_tag=test_tag, debug_stdout=foreground)
        
        # Force some initial debug output
        logger.debug("==== TouchFS Debug Logging Started ====")
        logger.debug(f"Process ID: {os.getpid()}")
        logger.debug(f"Python version: {sys.version}")
        logger.debug(f"Arguments: mountpoint={mountpoint}, foreground={foreground}")
        logger.debug("Checking log file...")
        
        # Verify logging is working by checking log file
        log_file = "/var/log/touchfs/touchfs.log"
        if not os.path.exists(log_file):
            if foreground:
                print(f"ERROR: Log file {log_file} was not created", file=sys.stdout)
            return 1
            
        # Read log file to verify initial log message was written
        with open(log_file, 'r') as f:
            log_content = f.read()
            if "Logger initialized with rotation" not in log_content:
                if foreground:
                    print("ERROR: Failed to verify log file initialization", file=sys.stdout)
                return 1
        
        logger.info(f"Main process started with PID: {os.getpid()}")
        logger.info("Setting up FUSE mount...")
    except Exception as e:
        if foreground:
            print(f"ERROR: Failed to initialize logging: {str(e)}", file=sys.stdout)
        return 1

    # Import settings module
    from ..config.settings import set_current_filesystem_prompt

    try:
        # Get prompts and generate filesystem
        initial_data = None
        
        # Only use filesystem generation if explicitly provided via arg or env var
        fs_prompt = get_filesystem_generation_prompt(filesystem_generation_prompt)
        if fs_prompt:
            print(f"Generating filesystem from prompt: {fs_prompt[:50]}...", file=sys.stdout)
            sys.stdout.flush()  # Ensure output is visible immediately
            try:
                initial_data = generate_filesystem(fs_prompt)["data"]
                set_current_filesystem_prompt(fs_prompt)
            except Exception as e:
                print(f"Error generating filesystem: {e}", file=sys.stderr)
                print("Starting with empty filesystem", file=sys.stdout)
                initial_data = generate_filesystem("")["data"]
                set_current_filesystem_prompt("")
        else:
            print("No filesystem generation prompt provided, starting with empty filesystem", file=sys.stdout)
            sys.stdout.flush()  # Ensure output is visible immediately
            initial_data = generate_filesystem("")["data"]
            set_current_filesystem_prompt("")

        # Mount filesystem
        test_tag = os.environ.get('TOUCHFS_TEST_TAG', '')
        tag_info = f" [{test_tag}]" if test_tag else ""
        
        logger.info(f"Mounting filesystem{tag_info} at {mountpoint} (foreground={foreground})")
        memory = Memory(initial_data, mount_point=mountpoint)
        logger.info("Memory filesystem instance created")
        
        # Configure FUSE options
        fuse_opts = {
            'foreground': foreground,
            'allow_other': allow_other,
            'allow_root': allow_root,
            'nothreads': nothreads,
            'nonempty': nonempty,
            'fsname': get_fsname()
        }
        
        fuse = FUSE(memory, mountpoint, **fuse_opts)
        logger.info("FUSE mount completed")
        return 0
    except RuntimeError as e:
        print(f"Error mounting filesystem: {e}")
        print("Note: You may need to create the mountpoint directory first")
        return 1

def add_mount_parser(subparsers):
    """Add mount-related parser to the CLI argument parser."""
    mount_parser = subparsers.add_parser('mount', help='Mount a touchfs filesystem')
    mount_parser.add_argument('mountpoint', type=str, help='Directory to mount the filesystem', metavar='mountpoint', nargs='?')
    mount_parser.add_argument('-F', '--filesystem-generation-prompt', type=str, 
                            help='Prompt used for filesystem generation')
    mount_parser.add_argument('-p', '--prompt', type=str,
                            help='Default prompt for file content generation')
    mount_parser.add_argument('--allow-other', action='store_true', help='Allow other users to access the mount')
    mount_parser.add_argument('--allow-root', action='store_true', help='Allow root to access the mount')
    mount_parser.add_argument('-f', '--foreground', action='store_true', help='Run in foreground with debug output')
    mount_parser.add_argument('--nothreads', action='store_true', help='Disable multi-threading')
    mount_parser.add_argument('--nonempty', action='store_true', help='Allow mounting over non-empty directory')
    mount_parser.set_defaults(func=lambda args: sys.exit(mount_main(
        mountpoint=args.mountpoint,
        prompt_arg=args.prompt,
        filesystem_generation_prompt=args.filesystem_generation_prompt,
        foreground=args.foreground,
        unmount=False,
        allow_other=args.allow_other,
        allow_root=args.allow_root,
        nothreads=args.nothreads,
        nonempty=args.nonempty,
        force=False
    )))

    return mount_parser
