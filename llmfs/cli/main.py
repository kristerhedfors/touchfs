"""Command line interface and main entry point."""
import sys
import argparse
from typing import Optional
from fuse import FUSE

from ..core.memory import Memory
from ..content.generator import generate_filesystem
from ..config.settings import get_prompt
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
        '--prompt',
        help='Prompt for generating the filesystem structure (alternatively use LLMFS_PROMPT env var or provide a prompt file)'
    )
    parser.add_argument(
        '--foreground', '-f',
        action='store_true',
        help='Run in foreground (default: run in background)'
    )
    return parser.parse_args()

def main(mountpoint: str, prompt_arg: Optional[str] = None, foreground: bool = True) -> int:
    """Main entry point for LLMFS.
    
    Args:
        mountpoint: Directory where the filesystem will be mounted
        prompt_arg: Optional prompt argument from command line
        foreground: Whether to run in foreground
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    if not mountpoint:
        print('usage: llmfs <mountpoint> [--prompt PROMPT] [--foreground]')
        print('   or: LLMFS_PROMPT="prompt" llmfs <mountpoint>')
        return 1

    # Setup logging (logs are always rotated for each invocation)
    logger = setup_logging()

    try:
        # Get prompt and generate filesystem if provided
        initial_data = None
        try:
            prompt = get_prompt(prompt_arg)
            print(f"Generating filesystem from prompt: {prompt[:50]}...")
            initial_data = generate_filesystem(prompt)["data"]
        except ValueError as e:
            print(f"No prompt provided, starting with empty filesystem: {e}")
        except Exception as e:
            print(f"Error generating filesystem: {e}")
            print("Starting with empty filesystem")

        # Mount filesystem
        fuse = FUSE(Memory(initial_data), mountpoint, foreground=foreground, allow_other=False)
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
        foreground=args.foreground
    ))
