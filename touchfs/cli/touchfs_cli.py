#!/usr/bin/env python3
import sys
import argparse
from touchfs.__main__ import run as mount_run
from touchfs.cli.context_command import run as context_run
from touchfs.cli.generate_command import run as generate_run

def main():
    parser = argparse.ArgumentParser(
        description='TouchFS - A filesystem that generates content on touch',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Mount subcommand (previously touchfs_mount)
    mount_parser = subparsers.add_parser('mount', help='Mount or unmount a touchfs filesystem')
    mount_parser.add_argument('mountpoint', type=str, help='Directory to mount/unmount the filesystem')
    mount_parser.add_argument('-u', '--unmount', action='store_true', help='Unmount the filesystem')
    mount_parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    mount_parser.add_argument('--allow-other', action='store_true', help='Allow other users to access the mount')
    mount_parser.add_argument('--allow-root', action='store_true', help='Allow root to access the mount')
    mount_parser.add_argument('--foreground', action='store_true', help='Run in foreground')
    mount_parser.add_argument('--nothreads', action='store_true', help='Disable multi-threading')
    mount_parser.add_argument('--nonempty', action='store_true', help='Allow mounting over non-empty directory')
    mount_parser.add_argument('--force', action='store_true', help='Force unmount even if busy')
    mount_parser.set_defaults(func=mount_run)

    # Umount subcommand (alternative to mount -u)
    umount_parser = subparsers.add_parser('umount', help='Unmount a touchfs filesystem')
    umount_parser.add_argument('mountpoint', type=str, help='Directory to unmount')
    umount_parser.add_argument('--force', action='store_true', help='Force unmount even if busy')
    umount_parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    umount_parser.set_defaults(func=mount_run)

    # Context subcommand (previously touchfs_context)
    context_parser = subparsers.add_parser('context', help='Generate context from files')
    context_parser.add_argument('path', nargs='?', help='Path to generate context from')
    context_parser.add_argument('--max-tokens', type=int, help='Maximum token count')
    context_parser.add_argument('--exclude', action='append', help='Patterns to exclude')
    context_parser.set_defaults(func=context_run)

    # Generate subcommand (previously touchfs_generate)
    generate_parser = subparsers.add_parser('generate', help='Mark files for content generation')
    generate_parser.add_argument('files', nargs='+', help='Files to mark for generation')
    generate_parser.add_argument('-p', '--parents', action='store_true', help='Create parent directories if needed')
    generate_parser.add_argument('-f', '--force', action='store_true', help='Skip confirmation for non-TouchFS paths')
    generate_parser.set_defaults(func=generate_run)

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1

    # Call the appropriate command function
    return args.func(args)

if __name__ == '__main__':
    sys.exit(main())
