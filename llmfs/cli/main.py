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
        description='LLMFS - A filesystem that generates content using LLMs',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        'mountpoint',
        help='Directory where the filesystem will be mounted'
    )
    parser.add_argument(
        '--prompt', '-p',
        help='Prompt for file content generation (alternatively use LLMFS_PROMPT env var or provide a prompt file)'
    )
    parser.add_argument(
        '--filesystem-generation-prompt', '-g',
        help='Prompt for generating the filesystem structure (alternatively use LLMFS_FILESYSTEM_GENERATION_PROMPT env var)'
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
    return parser.parse_args()

def main(mountpoint: str, prompt_arg: Optional[str] = None, filesystem_generation_prompt: Optional[str] = None, foreground: bool = True, cache_enabled: bool = True) -> int:
    """Main entry point for LLMFS.
    
    Args:
        mountpoint: Directory where the filesystem will be mounted
        prompt_arg: Optional prompt argument from command line
        foreground: Whether to run in foreground
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    if not mountpoint:
        print('usage: llmfs_mount <mountpoint> [--prompt PROMPT] [--foreground]')
        print('   or: LLMFS_PROMPT="prompt" llmfs_mount <mountpoint>')
        return 1

    # Setup logging (logs are always rotated for each invocation)
    try:
        logger = setup_logging()
        
        # Verify logging is working by checking log file
        log_file = "/var/log/llmfs/llmfs.log"
        if not os.path.exists(log_file):
            print(f"ERROR: Log file {log_file} was not created", file=sys.stderr)
            return 1
            
        # Read log file to verify initial log message was written
        with open(log_file, 'r') as f:
            log_content = f.read()
            if "Logger initialized with rotation" not in log_content:
                print("ERROR: Failed to verify log file initialization", file=sys.stderr)
                return 1
        
        logger.info(f"Main process started with PID: {os.getpid()}")
        logger.info("Setting up FUSE mount...")
    except Exception as e:
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
        cache_enabled=args.cache_enabled
    ))
