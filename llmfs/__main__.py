import sys
import argparse
from .llmfs import main

def parse_args():
    parser = argparse.ArgumentParser(description='LLMFS Service')
    parser.add_argument('mountpoint', help='Directory where the filesystem will be mounted')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    main(mountpoint=args.mountpoint)
