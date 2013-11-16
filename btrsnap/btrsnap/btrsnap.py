'''
This module will one day make for easy backup from btrfs to btrfs external drive
'''

if __name__ == "__main__":
    import argparse
    
    def main():
        '''
        Command Line Interface.
        '''
        parser = argparse.ArgumentParser(prog='btrsnap', description='Manage btrfs snapshots')
        parser.add_argument('-S', '--snapdeep', nargs=1, metavar='PATH', help='Creates a timestamped Btrfs snapshot in each subdirectory of PATH. Each subdirectory must contain a single symbolic link to the btrfs subvolume you wish to create snapshots for.')
        parser.add_argument('-t', '--test', metavar='PATH', help='Run test suite. PATH is an empty directory on a Btrfs filesystem')
        parser.add_argument('--version', action='version', version='%(prog) 0/0.0')
        args = parser.parse_args()
        print(args)
    
    #start the program
    main()