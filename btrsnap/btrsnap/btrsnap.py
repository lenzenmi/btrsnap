'''
This module will one day make for easy backup from btrfs to btrfs external drive
'''

if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(prog='btrsnap', description='Manage btrfs snapshots')
    parser.add_argument('--test', action='store_true')
    parser.add_argument('dir', help='Path to root snapshot directory. This directory contains any number of subdirectories used for storing and generating snapshots. Each subdirectory must contain a single symbolic link to the btrfs subvolume you wish to create snapshots of.')
    
    args = parser.parse_args(sys.argv[1:])
    
    