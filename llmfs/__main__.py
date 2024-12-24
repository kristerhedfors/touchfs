import sys
import argparse
from llmfs.llmfs import main

def parse_args():
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
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    if args.prompt:
        # Set prompt in environment for llmfs.py to use
        import os
        os.environ['LLMFS_PROMPT'] = args.prompt
    sys.exit(main(args.mountpoint, foreground=args.foreground, debug=args.debug))
