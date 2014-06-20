#!/usr/bin/env python3
'''
Writen for python 3.x
btrsnap simplifies working with btrfs snapshots.
'''

import os
import re
import datetime
import subprocess
import sys

try:
    from dateutil.relativedelta import relativedelta
except ImportError:
    print('You are missing some required packages!\n'
          'try:'
          '\n\tpip install python-dateutil')
    sys.exit(1)


class BtrsnapError(Exception):
    '''
    Root error for the btrsnap module
    '''
    pass


class PathError(BtrsnapError):
    '''
    Path does not exist on the filesystem
    '''
    pass


class TargetError(BtrsnapError):
    '''
    There is not exactly 1 symlink inside the snapshot directory
    '''
    pass


class BtrfsError(BtrsnapError):
    '''
    btrfs-progs returned a non zero exit code
    '''
    pass


class Path:
    '''
    Base Class for working with filesystem folders
    '''
    def __init__(self, path):
        '''
        Verifies that a path exists.

        Args:
            * path (str): a path on a filesystem.

        Attributes:
            * path (str): absolute path.

        Raises:
            * PathError: invalid path.
        '''
        if os.path.isdir(os.path.expanduser(path)):
            self.path = os.path.abspath(os.path.expanduser(path))
        else:
            raise PathError('{} is not a valid folder name'.format(path))

    def snapshots(self):
        '''
        List all folders in *self.path* whose name matches the
        btrsnap timestamp format: yyyy-mm-dd-####.

        Returns:
            * list(str): a list of directories inside self.path that
              match the btrsnap timestamp YYYY-MM-DD-####
        '''
        pattern = re.compile(r'^\d{4}-\d{2}-\d{2}-\d{4}$')
        contents = os.listdir(path=self.path)
        contents = [d for d in contents
                    if os.path.isdir(os.path.join(self.path, d))
                    and re.search(pattern, d)]
        contents.sort(reverse=True)
        return contents

    def sub_snap_paths_list(self):
        '''
        Returns:
            * list(SnapPath): a list of SnapPath objects for each subdirectory
            inside of self.path.
        '''
        return self._list_of_objects(SnapPath)

    def sub_paths_list(self):
        '''
        Returns:
            * list(Path): a list of Path objects for each subdirectory
            inside of self.path.
        '''
        return self._list_of_objects(Path)

    def _list_of_objects(self, obj):
        objects = []
        contents = os.listdir(self.path)
        contents = [directory for directory in contents
                    if os.path.isdir(os.path.join(self.path, directory))]
        for content in contents:
            try:
                objects.append(obj(os.path.join(
                    self.path, content)))
            except Exception:
                pass
        return objects


class SnapPath(Path):
    '''
    Verifies that path exists, and that it contains exactly one symlink.

    Agruments:
        * path (str): path on filesystem

    Attributes:
        * target (str): Absolute path where the symlink points.
        * path (str): Absolute path on the filesystem

    Raises:
        * TargetError:
        * PathError:
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
        contents = [link for link in contents
                    if os.path.islink(os.path.join(self.path, link))]
        if not len(contents) == 1:
            raise TargetError('there must be exactly 1 symlink pointing to a'
                              ' target BTRFS subvolume in snapshot'
                              ' directory {}'.format(self.path))
        self._target = os.path.realpath(os.path.abspath(os.path.join(
                                        self.path, contents[0])))

    def timestamp(self, counter=1):
        '''
        Returns the next availible timestamp in self.path

        Arguments:
            * counter (int): start number for last 4 digits of timestamp.

        Returns:
            * (str): next availible timestamp
        '''
        today = datetime.date.today()
        snapshots = self.snapshots()
        if snapshots:
            last_snapshot = snapshots[0]
            is_older_than_last_snapshot = True
        else:
            last_snapshot = None
            is_older_than_last_snapshot = False
        timestamp = None

        while ((timestamp is None)
               or (timestamp in snapshots)
               or (is_older_than_last_snapshot is True)):
            timestamp = '{}-{:04d}'.format(today.isoformat(), counter)
            if is_older_than_last_snapshot is True:
                if timestamp <= last_snapshot:
                    is_older_than_last_snapshot = True
                else:
                    is_older_than_last_snapshot = False

            if counter > 9999:
                raise Exception('More than 9999 snapshots created today.'
                                ' Something is probably wrong. Aborting!')
            counter += 1
        return timestamp


class Btrfs(Path):
    '''
    Wrapper class for BTRFS functions

    Args:
        * Path (str): Path on filesystem

    Attributes:
        * path (str): absolute path

    Raises:
        * PathError:
    '''

    def snap(self, target, timestamp, readonly=True):
        '''
        Create a snapshot in self.path

        Args:
            * target (str): absolute path of BTRFS subvolume to be cloned.
            * timestamp (str): name of the snapshot to be created.
            * readonly (bool): True/False, new snapshot is readonly.

        Raises:
            * BtrfsError:
        '''
        snapshot = os.path.join(self.path, timestamp)
        if readonly:
            args = ['btrfs', 'subvolume', 'snapshot', '-r', target, snapshot]
        else:
            args = ['btrfs', 'subvolume', 'snapshot', target, snapshot]

        return_code = subprocess.call(args)
        if return_code:
            raise BtrfsError('BTRFS failed to create a snapshot'
                             ' of {} in \'{}\''.format(target, snapshot))

    def unsnap(self, timestamp):
        '''
        Delete a snapshot in self.path

        Args:
            * timestamp (str): name of the snapshot to be deleted.

        Raises:
            * BtrfsError:
        '''
        snapshot = os.path.join(self.path, timestamp)
        args = ['btrfs', 'subvolume', 'delete', snapshot]
        return_code = subprocess.call(args, stderr=subprocess.DEVNULL,
                                      stdout=subprocess.DEVNULL)
        if return_code:
            raise BtrfsError('BTRFS failed to delete the subvolume.'
                             ' Perhaps you need root permissions')

    def send(self, snapshot, parent=None):
        '''
        Send a snapshot using btrfs-progs.

        Args:
            * snapshot (str): snapshot to be sent relative to self.path.
            * parent (str): parent snapshot relative to self.path.
                **must alread be on receiving filesystem.**

        Returns:
            * (subprocess.Popen): can be used to pipe output to receive.
        '''
        args = ['btrfs', 'send']
        if parent:
            parent = os.path.join(self.path, parent)
            args.extend(['-p', parent])

        args.append(os.path.join(self.path, snapshot))
        p1 = subprocess.Popen(args, stdout=subprocess.PIPE)
        return p1

    def receive(self, p1):
        '''
        Receive a snapshot using btrfs-progs.

        Args:
            * p1 (subprocess.Popen): send process

        Raises:
            * BtrfsError:
        '''
        args = ['btrfs', 'receive', self.path]
        p2 = subprocess.Popen(args, stdin=p1.stdout,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = p2.communicate()
        p1.stdout.close()
        if p2.returncode:
            raise BtrfsError('BTRFS Failed send/receive.'
                             ' Do you have root permissions?'
                             ' Are you receiving to the top level'
                             ' of your BTRFS filesystem?',
                             output[0], output[1])


def snap(path, readonly=True):
    '''
    Creates a snapshot inside PATH with format YYYY-MM-DD-####
    of the subvolume pointed to by the symlink inside PATH.

    Args:
        * path (str): path on filesystem
        * readonly (bool): create readonly snapshot?
    '''
    snappath = SnapPath(path)
    btrfs = Btrfs(snappath.path)
    btrfs.snap(snappath.target, snappath.timestamp(), readonly=readonly)


def unsnap(path, keep=None, date=None):
    '''
    Delete all but most recent KEEP snapshots inside PATH
    OR
    Delete all snapshots created on or before DATE

    Args:
        * path (str): path on filesystem
        * keep (int): number of snapshots to keep
        * date (dateutil.relativedelta.relativedelta): set to some date
            in the past

    Returns:
        * msg (str): results
    '''
    snappath = Path(path)
    btrfs = Btrfs(snappath.path)
    snapshots = snappath.snapshots()
    msg = ""
    if keep is not None:
        if not keep >= 0 or not isinstance(keep, int):
            raise Exception('keep must be a positive integer')
        if len(snapshots) > keep:
            snaps_to_delete = snapshots[keep:]
            for snapshot in snaps_to_delete:
                btrfs.unsnap(snapshot)
            msg = 'Deleted {} snapshot(s) from "{}". {} kept'.format(
                len(snaps_to_delete), snappath.path, keep)
        else:
            msg = ('There are {} or less snapshots in "{}" ...'
                   ' not deleting any'.format(keep, snappath.path)
                   )
    if date is not None:
        today = datetime.date.today()
        delta_today = today - date

        snapshots.sort()
        snapshots_deleted = 0
        while snapshots:
            snap = snapshots.pop()
            snap_date = snap.split('-')
            year, month, day = snap_date[:-1]
            snap_datetime_date = relativedelta(year=int(year),
                                               month=int(month),
                                               day=int(day)
                                               )
            delta_snap = today - snap_datetime_date
            if delta_today >= delta_snap:
                btrfs.unsnap(snap)
                snapshots_deleted += 1
            msg = ('Deleted {} snapshot(s) from "{}"'
                   '\n\t created on or before {}'
                   .format(snapshots_deleted,
                           snappath.path,
                           delta_today.isoformat()
                           )
                   )
        if not msg:
            msg = ('There are no snapshot(s) as old or older than "{}"'
                   ' in "{}" ... not deleting any'
                   .format(delta_today.isoformat(), snappath.path))

    return msg


def unsnap_deep(path, keep=None, date=None):
    '''
    Delete all but KEEP snapshots from each directory
    inside of path

    Args:
        * path (str): path on filesystem
        * keep (int): number of snapshots to keep
        * date (dateutil.relativedelta.relativedelta): set to some date
            in the past

    Returns:
        * msg (str): results
    '''
    msg = []
    parent_path = Path(path)
    path_objects = parent_path.sub_paths_list()
    if len(path_objects) == 0:
        msg = 'No subdirectories found in \'{}\''.format(parent_path.path)
        return msg
    for path in path_objects:
        msg.append(unsnap(path.path, keep=keep, date=date))
    return '\n'.join(msg)


def snap_deep(path, readonly=True):
    '''
    Create a snapshot in each subdirectory in PATH.

    Args:
        * path (str): path on filesystem
        * readonly (bool): Create readonly snapshots?

    Returns:
        * msg (str): results
    '''
    snap_deep = Path(path)
    snap_paths = snap_deep.sub_snap_paths_list()
    if len(snap_paths) == 0:
        msg = 'No snapshot directories found in \'{}\''.format(snap_deep.path)
        return msg
    for snap_path in snap_paths:
        snap(snap_path.path, readonly=readonly)


def show_snaps(path):
    '''
    List snapshots inside PATH.

    Args:
        * path (str): path on filesystem.

    Returns:
        * msg (str): results
    '''
    path = Path(path)
    snapshots = path.snapshots()
    msg = []
    for snapshot in snapshots:
        msg.append(snapshot)
    msg.append('\n"{}" contains {} snapshot(s)'.format(
        path.path, len(snapshots)))
    return '\n'.join(msg)


def show_snaps_deep(path):
    '''
    Recursively list snapshots inside PATH.

    Args:
        * path (str): Path on filesystem.

    Returns:
        * msg (str): results
    '''
    msg = []
    overall_snapshot_count = 0
    overall_path_count = 0
    parent_path = Path(path)
    sub_paths_list = parent_path.sub_paths_list()
    for p in sub_paths_list:
        snapshots = p.snapshots()
        msg.append('\n\'{}\'/'.format(p.path))
        if snapshots:
            newest = snapshots[0]
            oldest = snapshots[-1]
            msg.append('\t{} snapshot(s): Newest = {}, Oldest = {}'.format(
                len(snapshots), newest[:-5], oldest[:-5]))
            for snapshot in snapshots:
                msg.append('\t\t{}'.format(snapshot))
                overall_snapshot_count += 1
        else:
            msg.append('\t\tNo snapshots')
        overall_path_count += 1
    msg.append('\n{:{s}^{n}}'.format(' Summary ', s='-', n=60))
    msg.append('\'{}\' contains {} snapshots in {} subdirectories'.format(
        path, overall_snapshot_count, overall_path_count))

    return '\n'.join(msg)


def send_receive(send_path, receive_path):
    '''
    Send snapshots from one BTRFS PATH to another.

    Args:
        * send_path: path to snapshot to send
        * receive_path: path to receive snapshot in.

    Returns:
        * (str): results
    '''
    send = SnapPath(send_path)
    receive = Path(receive_path)
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

    number_sent = len(diff)

    if diff:
        if (union) and (union[-1] < diff[0]):
            parent, snapshot = union[-1], diff[0]
        else:
            parent, snapshot = None, diff[0]

        p1 = send_btr.send(snapshot, parent)
        receive_btr.receive(p1)
        while diff:
            if len(diff) >= 2:
                parent, snapshot = diff.pop(0), diff[0]
                p1 = send_btr.send(snapshot, parent)
                receive_btr.receive(p1)
            else:
                diff.pop(0)
        msg = '{} snapshots copied from \'{}\' to \'{}\''.format(
            number_sent, send.path, receive.path)
    else:
        msg = 'No new snapshots to copy from \'{}\' to \'{}\''.format(
            send.path, receive.path)
    return msg


def send_receive_deep(send_path, receive_path):
    '''
    Send all snapshots in subdirectories of send_path to receive_path.

    Args:
        * send_path (str): absolute path holding one or more snapshot
                         directories.
        * receive_path (str): absolute path to receive snapshot directories in.

    Returns:
        * (str): results.
    '''
    snap_deep = Path(send_path)
    snappaths = snap_deep.sub_snap_paths_list()
    snappaths = [snappath.path for snappath in snappaths]
    receive_path = Path(receive_path)
    receive_path = receive_path.path
    receive_paths = [os.path.join(receive_path, s.split(os.path.sep)[-1]) for
                     s in snappaths]
    msg = []

    for p in receive_paths:
        if not os.path.isdir(p):
            os.mkdir(p)

    args = zip(snappaths, receive_paths)
    for send_path, receive_path in args:
        msg.append(send_receive(send_path, receive_path))
    return '\n'.join(msg)


def main():
    '''
    Command Line Interface.
    '''

    import argparse

    from . import argparse_types

    def caller(func, *args, **kargs):
        try:
            msg = func(*args, **kargs)
            if msg:
                print(msg)
        except Exception as err:
            print('Error:', err)

    def run_snap(args):
        keep = None
        date = None
        if (args.keep):
            keep = args.keep[0]
        if (args.date):
            date = args.date[0]
        if not args.recursive:
            caller(snap, args.snap_path[0])
            if (keep is not None) or (date is not None):
                caller(unsnap, args.snap_path[0], keep=keep, date=date)
        if args.recursive:
            caller(snap_deep, args.snap_path[0])
            if (keep is not None) or (date is not None):
                caller(unsnap_deep, args.snap_path[0], keep=keep, date=date)

    def run_list(args):
        if not args.recursive:
            caller(show_snaps, args.snap_path[0])
        else:
            caller(show_snaps_deep, args.snap_path[0])

    def run_send(args):
        if not args.recursive:
            caller(send_receive, args.send_path[0], args.receive_path[0])

        if args.recursive:
            caller(send_receive_deep, args.send_path[0], args.receive_path[0])

    def run_delete(args):
        keep = None
        date = None
        if args.keep:
            keep = args.keep[0]
        if args.date:
            date = args.date[0]
        if args.recursive:
            caller(unsnap_deep, args.snap_path[0], keep=keep, date=date)
        else:
            caller(unsnap, args.snap_path[0], keep=keep, date=date)

    def no_subparser(args):
        parser.parse_args([''])

    parser = argparse.ArgumentParser(
        prog='btrsnap',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''
    btrsnap is a BTRFS wrapper that simplifies dealing with snapshots.
    *You will need root privileges for some actions.*

    Before using btrsnap:

    * create a parent directory on a BTRFS filesystem where you will keep
      your snapshots.
    * Within this directory create any number of subdirectories.
    * Inside each subdirectory create **one** symbolic link that points to a
      BTRFS subvolume. The link can have any name.

    For example::

        |-- snapshots
            |
            |`-- music
            |    `-- target (symbolic link pointing to => /srv/music)
            |
             `-- photos
                 `-- target (symbolic link pointing to => /srv/photos)

    .. note::
        You can create a symbolic link using::

            ln -s

        example::

            ln -s /srv/music /snapshots/music/target
    ...         ''')
    parser.add_argument('--version', action='version',
                        version='%(prog)s 2.0.0'
                        )
    subparsers = parser.add_subparsers(title='sub-commands')

    subparser_snap = subparsers.add_parser('snap',
                                           description='Creates a new'
                                           ' timestamped BTRFS snapshot'
                                           ' inside of PATH. The snapshot will'
                                           ' be a snapshot of the BTRFS'
                                           ' subvolume pointed to by the'
                                           ' symbolic link in PATH.',
                                           help='Creates new timestamped BTRFS'
                                           ' snapshot'
                                           )
    subparser_snap.add_argument('-r', '--recursive',
                                action='store_true',
                                help='Instead, create a snapshot inside of'
                                ' each directory located inside of PATH'
                                )
    subparser_snap.add_argument('snap_path',
                                nargs=1,
                                metavar='PATH',
                                help='A directory on a BTRFS file system with'
                                ' a symlink pointing to a BTRFS subvolume'
                                )
    group_snap = subparser_snap.add_argument_group('Mutually Exclusive',
                                                   '(Optional) - Choose 1')
    mutually_exclusive_snap = group_snap.add_mutually_exclusive_group()
    mutually_exclusive_snap.add_argument('-k', '--keep',
                                         nargs=1,
                                         type=int,
                                         metavar='N',
                                         help='After creating, delete all'
                                         ' but N snapshots'
                                         )
    mutually_exclusive_snap.add_argument('-d', '--date',
                                         nargs=1,
                                         type=argparse_types.date_parser,
                                         metavar='YYYY-MM-DD or ?y?m?d?w',
                                         help='After creating, delete all'
                                         ' snapshots created on or before the'
                                         ' entered date. You may enter dates'
                                         ' as ISO format or use the alternate'
                                         ' syntax ?y?m?d?w where N can be'
                                         ' any positive intager and indicates'
                                         ' the number of years, months, days,'
                                         ' and weeks respectively.',
                                         )
    subparser_snap.set_defaults(func=run_snap)

    subparser_list = subparsers.add_parser('list',
                                           description='Show timestamped'
                                           ' snapshots in PATH',
                                           help='Show timestamped snapshots'
                                           )
    subparser_list.add_argument('snap_path',
                                nargs=1,
                                metavar='PATH',
                                help='A directory on a BTRFS filesystem'
                                ' that contains snapshots created by btrsnap.'
                                )
    subparser_list.add_argument('-r', '--recursive',
                                action='store_true',
                                help='Instead, show summary statistics for all'
                                ' subdirectories in PATH.'
                                )
    subparser_list.set_defaults(func=run_list)

    subparser_delete = subparsers.add_parser('delete',
                                             description='Delete all but KEEP'
                                             ' snapshots from PATH.'
                                             ' (Default, KEEP=5)',
                                             help='Delete snapshots'
                                             )
    subparser_delete.add_argument('-r', '--recursive',
                                  action='store_true',
                                  help='knstead delete all but KEEP snapshots'
                                  ' from each subdirectory')
    subparser_delete.add_argument('snap_path',
                                  nargs=1,
                                  metavar='PATH',
                                  help='a directory on a BTRFS filesystem'
                                  ' that contains snapshots created by'
                                  ' btrsnap'
                                  )
    group = subparser_delete.add_argument_group('Mutually Exclusive',
                                                '(Required) - Choose 1')
    mutually_exclusive = group.add_mutually_exclusive_group()
    mutually_exclusive.add_argument('-k', '--keep',
                                  nargs=1,
                                  type=int,
                                  metavar='N',
                                  help='keep N snapshots when deleting',
                                  )
    mutually_exclusive.add_argument('-d', '--date',
                                  nargs=1,
                                  type=argparse_types.date_parser,
                                  metavar='YYYY-MM-DD or ?y?m?d?w',
                                  help='delete all snapshots created on or'
                                  ' before the entered date. You may enter '
                                  ' dates as ISO format or use the'
                                  ' alternate syntax ?y?m?d?w where N can be'
                                  ' any positive intager and indicates the'
                                  ' number of years, months, days, and weeks'
                                  ' respectively.',
                                  )
    subparser_delete.set_defaults(func=run_delete)

    subparser_send = subparsers.add_parser('send',
                                           description='Send all snapshots'
                                           ' from SendPATH to ReceivePATH if'
                                           ' not present.',
                                           help='Use BTRFS send/receive to'
                                           ' smartly send snapshots from one'
                                           ' BTRFS filesystem to another.'
                                           )
    subparser_send.add_argument('-r', '--recursive',
                                action='store_true',
                                help='Instead, send snapshots from each sub'
                                ' directory of SendPATH to a subdirectory of'
                                ' the same name in ReceivePATH. Subdirectories'
                                ' are automatically created if needed.'
                                )
    subparser_send.add_argument('send_path',
                                nargs=1,
                                metavar='SendPATH',
                                help='A directory on a BTRFS filesystem that'
                                ' contains snapshots created by btrsnap.')
    subparser_send.add_argument('receive_path',
                                nargs=1,
                                metavar='ReceivePATH',
                                help='A directory on a BTRFS filesystem that'
                                ' will receive snapshots.')
    subparser_send.set_defaults(func=run_send)

    args = parser.parse_args()

    # make sure that one of the mutually_exclusive arguments is supplied
    if hasattr(args, 'func') and (args.func is run_delete):
        if (not args.date) and (not args.keep):
            parser.error('you must supply either --keep or --date')

    try:
        args.func(args)
    except AttributeError:
        no_subparser(args)

if __name__ == "__main__":

    # start the program
    main()
