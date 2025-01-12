"""Mount utilities for TouchFS.

This module provides utility functions for working with mounted TouchFS filesystems.
"""

import os
import sys
from typing import List, Tuple
from ...config.settings import get_fsname

def get_mounted_touchfs() -> List[Tuple[str, str, str]]:
    """Get list of currently mounted touchfs filesystems with their PIDs and commands.
    
    Returns:
        List of tuples containing (mountpoint, pid, command) for each mounted filesystem
    """
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
    return sorted(mounted)  # Sort for consistent output
