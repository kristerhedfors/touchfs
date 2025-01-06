#!/usr/bin/env python3
import sys
import argparse
from touchfs.cli.context_command import run as context_run
from touchfs.config.settings import DEFAULT_MAX_TOKENS
from touchfs.cli.generate_command import run as generate_run
from touchfs.cli.mount_command import add_mount_parser

def main():
    parser = argparse.ArgumentParser(
        description='TouchFS - A filesystem that generates content on touch',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Add mount and umount subcommands
    add_mount_parser(subparsers)

    # Context subcommand (previously touchfs_context)
    context_parser = subparsers.add_parser('context', help='Generate context from files')
    context_parser.add_argument('path', nargs='?', help='Path to generate context from')
    context_parser.add_argument('--max-tokens', type=int, default=DEFAULT_MAX_TOKENS, help=f'Maximum token count (default: {DEFAULT_MAX_TOKENS})')
    context_parser.add_argument('--exclude', action='append', help='Patterns to exclude')
    context_parser.add_argument('--debug-stdout', action='store_true', help='Enable debug output to stdout')
    context_parser.set_defaults(func=context_run)

    # Generate subcommand (previously touchfs_generate)
    generate_parser = subparsers.add_parser('generate', help='Mark files for content generation')
    generate_parser.add_argument('files', nargs='+', help='Files to mark for generation')
    generate_parser.add_argument('-p', '--parents', action='store_true', help='Create parent directories if needed')
    generate_parser.add_argument('-f', '--force', action='store_true', help='Skip confirmation for non-TouchFS paths')
    generate_parser.add_argument('--debug-stdout', action='store_true', help='Enable debug output to stdout')
    generate_parser.set_defaults(func=generate_run)

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1

    # Call the appropriate command function
    return args.func(args)

if __name__ == '__main__':
    sys.exit(main())
