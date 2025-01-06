#!/usr/bin/env python3
import sys
import argparse
from touchfs.cli.context_command import add_context_parser
from touchfs.cli.generate_command import add_generate_parser
from touchfs.cli.mount_command import add_mount_parser
from touchfs.cli.umount_command import add_umount_parser

def main():
    parser = argparse.ArgumentParser(
        description='TouchFS - A filesystem that generates content on touch',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Add context and generate subcommands first
    add_context_parser(subparsers)
    add_generate_parser(subparsers)
    
    # Add mount and umount subcommands
    add_mount_parser(subparsers)
    add_umount_parser(subparsers)

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1

    # Call the appropriate command function
    return args.func(args)

if __name__ == '__main__':
    sys.exit(main())
