"""Command line interface and main entry point."""
import sys
import os
import argparse
from typing import Optional
from fuse import FUSE

from ..core.memory import Memory
from ..content.generator import generate_filesystem
from ..config.settings import get_prompt, get_filesystem_generation_prompt, set_cache_enabled
from ..config.logger import setup_logging

def parse_args() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description='TouchFS - A filesystem that generates content using LLMs',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '-u', '--unmount',
        action='store_true',
        help='Unmount the filesystem at the specified mountpoint'
    )
    parser.add_argument(
        'mountpoint',
        help='Directory where the filesystem will be mounted'
    )
    parser.add_argument(
        '--prompt', '-p',
        help='Prompt for file content generation (alternatively use TOUCHFS_PROMPT env var or provide a prompt file)'
    )
    parser.add_argument(
        '--filesystem-generation-prompt', '-g',
        help='Prompt for generating the filesystem structure (alternatively use TOUCHFS_FILESYSTEM_GENERATION_PROMPT env var)'
    )
    parser.add_argument(
        '--foreground', '-f',
        action='store_true',
        help='Run in foreground (default: run in background)'
    )
    parser.add_argument(
        '--cache-enabled',
        type=lambda x: str(x).lower() in ('true', '1'),
        default=True,
        help='Enable/disable caching (true/false or 1/0)'
    )
    parser.add_argument(
        '--debug-stderr',
        action='store_true',
        help='Enable debug logging to stderr'
    )
    return parser.parse_args()

def main(mountpoint: str, prompt_arg: Optional[str] = None, filesystem_generation_prompt: Optional[str] = None, foreground: bool = False, cache_enabled: bool = True, debug_stderr: bool = False, unmount: bool = False) -> int:
    """Main entry point for TouchFS.
    
    Args:
        mountpoint: Directory where the filesystem will be mounted
        prompt_arg: Optional prompt argument from command line
        foreground: Whether to run in foreground
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    if not mountpoint:
        print('usage: touchfs_mount <mountpoint> [--prompt PROMPT] [--foreground] [--unmount]')
        print('   or: TOUCHFS_PROMPT="prompt" touchfs_mount <mountpoint>')
        return 1
        
    # Handle unmount request
    if unmount:
        from .umount_command import unmount
        return unmount(mountpoint, force=True, debug=debug_stderr)

    # Setup logging (logs are always rotated for each invocation)
    try:
        if debug_stderr:
            print("Starting TouchFS with debug logging...", file=sys.stderr)
        # Check for test tag
        test_tag = os.environ.get('TOUCHFS_TEST_TAG')
        logger = setup_logging(test_tag=test_tag, debug_stderr=debug_stderr)
        
        # Force some initial debug output
        logger.debug("==== TouchFS Debug Logging Started ====")
        logger.debug(f"Process ID: {os.getpid()}")
        logger.debug(f"Python version: {sys.version}")
        logger.debug(f"Arguments: mountpoint={mountpoint}, foreground={foreground}")
        logger.debug("Checking log file...")
        
        # Verify logging is working by checking log file
        log_file = "/var/log/touchfs/touchfs.log"
        if not os.path.exists(log_file):
            if debug_stderr:
                print(f"ERROR: Log file {log_file} was not created", file=sys.stderr)
            return 1
            
        # Read log file to verify initial log message was written
        with open(log_file, 'r') as f:
            log_content = f.read()
            if "Logger initialized with rotation" not in log_content:
                if debug_stderr:
                    print("ERROR: Failed to verify log file initialization", file=sys.stderr)
                return 1
        
        logger.info(f"Main process started with PID: {os.getpid()}")
        logger.info("Setting up FUSE mount...")
    except Exception as e:
        if debug_stderr:
            print(f"ERROR: Failed to initialize logging: {str(e)}", file=sys.stderr)
        return 1
    
    # Set initial cache state
    set_cache_enabled(cache_enabled)

    try:
        # Get prompts and generate filesystem if provided
        initial_data = None
        try:
            fs_prompt = get_filesystem_generation_prompt(filesystem_generation_prompt)
            print(f"Generating filesystem from prompt: {fs_prompt[:50]}...")
            initial_data = generate_filesystem(fs_prompt)["data"]
        except ValueError as e:
            print(f"No prompt provided, starting with empty filesystem: {e}")
        except Exception as e:
            print(f"Error generating filesystem: {e}")
            print("Starting with empty filesystem")

        # Mount filesystem
        logger.info(f"Mounting filesystem at {mountpoint} (foreground={foreground})")
        memory = Memory(initial_data, mount_point=mountpoint)
        logger.info("Memory filesystem instance created")
        fuse = FUSE(memory, mountpoint, foreground=foreground, allow_other=False)
        logger.info("FUSE mount completed")
        return 0
    except RuntimeError as e:
        print(f"Error mounting filesystem: {e}")
        print("Note: You may need to create the mountpoint directory first")
        return 1

def run():
    """Entry point for the command-line script."""
    args = parse_args()
    sys.exit(main(
        mountpoint=args.mountpoint,
        prompt_arg=args.prompt,
        filesystem_generation_prompt=args.filesystem_generation_prompt,
        foreground=args.foreground,
        cache_enabled=args.cache_enabled,
        debug_stderr=args.debug_stderr,
        unmount=args.unmount
    ))
