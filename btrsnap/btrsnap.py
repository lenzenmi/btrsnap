#!/usr/bin/python3
'''
Writen for python 3.x
btrsnap is a BTRFS wrapper to simplify dealing with snapshots.
'''

import os
import re
import datetime
import subprocess

class PathError(Exception):
    pass

class TargetError(Exception):
    pass

class BtrfsError(Exception):
    pass


class Path:
    '''
    Base class to provide path attribute from user entered path
    '''
    def __init__(self, path):
        if os.path.isdir(os.path.expanduser(path)):
            self.path = os.path.abspath(os.path.expanduser(path))
        else:
            raise PathError('Path not valid')


class SnapshotsMixin:
    '''
    Mixin to display directories in path that match the btrsnap timestamp YYYY-MM-DD-####.
    Returned list is sorted from newest to oldest.
    '''
    
    def snapshots(self):
        pattern = re.compile('\d{4}-\d{2}-\d{2}-\d{4}')
        contents = os.listdir(path=self.path)
        contents = [ d for d in contents if os.path.isdir(os.path.join(self.path, d)) and re.search(pattern, d)]
        contents.sort(reverse=True)
        return contents
    
            
class SnapDeep(Path):
    '''
    Returns list of SnapPaths within the provided root directory.
    '''
        
    def snap_paths(self):
        snap_paths = []
        contents = os.listdir(self.path)
        contents = [ os.path.join(self.path, d) for d in contents if os.path.isdir(os.path.join(self.path, d))]
        for content in contents:
            try:
                snap_paths.append(SnapPath(content))
            except Exception:
                pass
            
        return snap_paths
                
        
class SnapPath(Path, SnapshotsMixin):
    '''
    Returns an object that has verified the path has a symlink pointing to a target directory.
    Calculates a timestamp for a new snapshot of target directory.
    '''
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
    
    def timestamp(self, counter=1):
        today = datetime.date.today()
        timestamp = None
        
        while (timestamp in self.snapshots()) or (timestamp == None):
            timestamp = '{}-{:04d}'.format(today.isoformat(), counter)
            counter += 1

        assert counter <= 9999
        return timestamp 
    

class ReceivePath(Path, SnapshotsMixin):
    pass
    
       
class Btrfs(Path):
    '''
    Wrapper class for BTRFS functions
    '''
    
    def snap(self, target, timestamp, readonly=True):
        snapshot = os.path.join(self.path, timestamp)
        if readonly:
            args = ['btrfs', 'subvolume', 'snapshot', '-r', target, snapshot]
        else:
            args = ['btrfs', 'subvolume', 'snapshot', target, snapshot]

        return_code = subprocess.call(args)
        if return_code:
            raise BtrfsError('BTRFS failed to create a snapshot of {} in \'{}\''.format(target, snapshot))
        
    def unsnap(self, timestamp):  
        snapshot = os.path.join(self.path, timestamp)
        args = ['btrfs', 'subvolume', 'delete', snapshot]
        return_code = subprocess.call(args)
        if return_code:
            raise BtrfsError('BTRFS failed to delete the subvolume. Perhaps you need root permissions')
        
    def send(self, snapshot, parent=None):
        args = ['btrfs', 'send']
        if parent:
            parent = os.path.join(self.path, parent)
            args.extend(['-p', parent])
                    
        args.append(os.path.join(self.path, snapshot))
        print(args)
        p1 = subprocess.Popen(args, stdout=subprocess.PIPE)
        return p1
    
    def receive(self, p1):
        args = ['btrfs', 'receive', self.path]
        p2 = subprocess.Popen(args, stdin=p1.stdout, stdout=subprocess.PIPE)
        p1.stdout.close()
        output = p2.communicate()
        print(output[0], output[1])
        
        
def snap(path, readonly=True):
    '''
    Creates a snapshot inside PATH with format YYYY-MM-DD-#### 
    of subvolume pointed to by a symlink inside PATH
    '''
    snappath = SnapPath(path)
    btrfs = Btrfs(snappath.path)
    btrfs.snap(snappath.target, snappath.timestamp(), readonly=readonly)
    
def unsnap(path, keep=5):
    '''
    Delete all but most recent KEEP(default 5) snapshots inside PATH
    '''
    snappath = SnapPath(path)
    btrfs = Btrfs(snappath.path)
    snapshots = snappath.snapshots()
    
    if not keep >= 0 or not isinstance(keep, int):
        raise Exception('keep must be a positive integer')        
    if len(snapshots) > keep:
        snaps_to_delete = snapshots[keep:]
        for snapshot in snaps_to_delete:
            try:
                btrfs.unsnap(snapshot)
                print('Deleted {} snapshot(s) from "{}". {} kept'.format(
                    len(snaps_to_delete), snappath.path, keep)
                    )
            except BtrfsError as error:
                print('Error: {}'.format(error))
    
    else:
        print('There are less than {} snapshot(s) in "{}"... not deleting any'.format(keep, snappath.path))

def snapdeep(path, readonly=True):
    '''
    Create snapshots in each subdirectory in PATH.
    '''
    snapdeep = SnapDeep(path)
    snap_paths = snapdeep.snap_paths()
    if len(snap_paths) == 0:
        print('No snapshot directories found in \'{}\''.format(snapdeep.path))
    for snap_path in snap_paths:
        snap(snap_path.path, readonly=readonly)

def show_snaps(path):
    '''
    List snapshots inside PATH.
    '''
    receive_path = ReceivePath(path)
    snapshots = receive_path.snapshots()
    
    for snapshot in snapshots:
        print(snapshot)
    print('\n"{}" contains {} snapshot(s)'.format(receive_path.path, len(snapshots)))
    
def sendreceive(send_path, receive_path):
    send = SnapPath(send_path)
    receive = ReceivePath(receive_path)
    send_btr = Btrfs(send.path)
    receive_btr = Btrfs(receive.path)
    
    send_set = set(send.snapshots())
    receive_set = set(receive.snapshots())
    diff = send_set - receive_set
    diff = list(diff)
    diff.sort()
    union = send_set & receive_set
    union = list(union)
    union.sort()
    
    if diff:
        if union:
            parent, snapshot = union.pop(), diff.pop(0)
            p1 = send_btr.send(snapshot, parent)
            receive_btr.receive(p1)
        else:
            parent, snapshot = None, diff.pop(0)
            p1 = send_btr.send(snapshot, parent)
            receive_btr.receive(p1)
                    
        while diff:
            if len(diff) > 1:
                parent, snapshot = diff.pop(0), diff.pop(0)
            else: 
                parent, snapshot = None, diff.pop(0)
            
            p1 = send_btr.send(snapshot, parent)
            receive_btr.receive(p1)
            
        
    else:
        print('No new snapshots to copy from {} to {}').format(send.path, receive.path)
        
if __name__ == "__main__":
    
    def main():
        '''
        Command Line Interface.
        '''
        
        import argparse

        parser = argparse.ArgumentParser(prog='btrsnap',
                                        formatter_class=argparse.RawDescriptionHelpFormatter,
                                        description='''
    btrsnap is a BTRFS wrapper to simplify dealing with snapshots.
    You will need root privileges for actions involving the removal of snapshots.


    To use, create a root directory on a BTRFS filesystem where you will keep your snapshots.
    within this directory create any number of subdirectories. Each subdirectory must contain a 
    symbolic link pointing to a valid BTRFS subvolume.\n\n

    For example:
    
            /snapshots
                -/music
                    target (symbolic link pointing to => /srv/music)
                -/photos
                    target (symbolic link pointing to => /srv/photos)
        
    Note:
            You can create a symbolic link using:
            ln -s /srv/music /snapshots/music/target
        ...         ''')
        parser.add_argument('-s', '--snap', nargs=1, metavar='PATH', help='Creates a new timestamped BTRFS snapshot in PATH')
        parser.add_argument('-S', '--snapdeep', nargs=1, metavar='PATH', help='Creates a timestamped BTRFS snapshot in each subdirectory of PATH.')
        parser.add_argument('-l', '--list', nargs=1, metavar='PATH', help='List snapshots in PATH')
        parser.add_argument('-d', '--delete', nargs=1, metavar='PATH', help='Delete all but 5 snapshots in PATH. May be modified by -k, --keep')
        parser.add_argument('-k', '--keep', nargs=1, type=int, metavar='NUMBER', help='Number of snapshots to keep with -d, --delete ')
        parser.add_argument('--send-receive', dest='send_receive', nargs=2, metavar='PATH', help='Send snapshots from PATH to PATH using btrfs send and receive')
        parser.add_argument('--version', action='version', version='btrsnap 0.0.0')
        args = parser.parse_args()
        
        if args.snap:
            try:
                snap(args.snap[0])
            except Exception as err:
                print('Error:', err)
        
        if args.snapdeep:
            try:
                snapdeep(args.snapdeep[0])
            except Exception as err:
                print('Error:', err)
                
        if args.delete:
            keep = 5
            if args.keep:
                keep = args.keep[0]
            try:
                unsnap(args.delete[0], keep=keep)
            except Exception as err:
                print('Error:', err)
                
        if args.list:
            show_snaps(args.list[0])
                
        if args.send_receive:
            #try:
                sendreceive(args.send_receive[0], args.send_receive[1])
            #except Exception as err:
            #    print('Error:', err)
            
           
    #start the program
    main()