'''
This module will one day make for easy backup from btrfs to btrfs external drive
'''

import os
import re

class PathError(Exception):
    pass
class TargetError(Exception):
    pass

class Path:
    
    def __init__(self, path):
        if os.path.isdir(os.path.expanduser(path)):
            self.path = os.path.abspath(os.path.expanduser(path))
        else:
            raise PathError('Path not valid')
        
class SnapPath(Path):
    
    def __init__(self, path):
        Path.__init__(self, path)
        self.target = 'initiate'
    
    @property    
    def target(self):
        return self._target
    
    @target.setter
    def target(self, garbage):
        contents = os.listdir(path=self.path)
        contents = [ link for link in contents if os.path.islink(os.path.join(self.path, link))]
        if not len(contents) == 1:
            raise TargetError('there must be exactly 1 symlink pointing to a target btrfs subvolume'
            + ' in snapshot directory {}'.format(self.path))
        self._target = os.path.realpath(os.path.abspath(os.path.join(self.path, contents[0])))
    
    def list(self):
        pattern = re.compile('\d{4}-\d{2}-\d{2}-\d{4}')
        contents = os.listdir(path=self.path)
        contents = [ d for d in contents if os.path.isdir(os.path.join(self.path, d)) and re.search(pattern, d)]
        return sorted(contents)        
        

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