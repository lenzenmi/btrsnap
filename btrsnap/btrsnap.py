'''
This module will one day make for easy backup from btrfs to btrfs external drive
'''

import os

class PathError(Exception):
    pass

class Path:
    def __init__(self, path):
        if os.path.isdir(os.path.expanduser(path)):
            self.path = os.path.abspath(os.path.expanduser(path))
        else:
            raise PathError('Path not valid')

if __name__ == "__main__":
    
    def main():
        '''
        Command Line Interface.
        '''
        
        import argparse

        parser = argparse.ArgumentParser(prog='btrsnap', description='Manage btrfs snapshots')
        parser.add_argument('-S', '--snapdeep', nargs=1, metavar='PATH', help='Creates a timestamped Btrfs snapshot in each subdirectory of PATH. Each subdirectory must contain a single symbolic link to the btrfs subvolume you wish to create snapshots for.')
        parser.add_argument('--version', action='version', version='%(prog) 0/0.0')
        args = parser.parse_args()
        
        #debug output
        print(args)
        
           
    #start the program
    main()