#!/usr/bin/python
'''
**These tests must be run with root permissions**

You must set the environment variable 'BTRSNAP_TEST_DIR' to a directory on a
BTRFS subvolume where you want the tests to run.

    example:
    export BTRSNAP_TEST_DIR='~/'
    python btrsnap_root_perms_required_test.py

BTRFS snapshots are created using the readonly=False flag. This is to allow the
test modules to delete readonly snapshots
'''
import unittest
import os
import shutil
import datetime
import subprocess
import re
import glob

import btrsnap


def get_test_dir():
    try:
        environ_path = os.path.expanduser(os.environ['BTRSNAP_TEST_DIR'])
        test_dir = os.path.join(
            os.path.realpath(os.path.abspath(environ_path)),
            'btrsnap_test_dir'
            )
    except Exception:
        print('you must assign the environment variable BTRSNAP_TEST_DIR=PATH\n'
              'Where path = a path on a btrfs filesystem\n'
              '\tExample:\n\t\t export BTRSNAP_TEST_DIR=\'~\''
              )
        exit(1)
    if os.path.isdir(test_dir):
        print('{} exists. Please remove it and re-run tests'.format(test_dir))
        exit(1)
    return test_dir


class Test_functions_(unittest.TestCase):
    test_dir = get_test_dir()
    parent_snap_dir = os.path.join(test_dir, 'parent_snap')
    snap_dir1 = os.path.join(parent_snap_dir, 'snap_dir1')
    snap_dir2 = os.path.join(parent_snap_dir, 'snap_dir2')
    link_dir = os.path.join(test_dir, 'link_dir')
    receive_dir = os.path.join(test_dir, 'receive_dir')
    today = datetime.date.today()
    timestamp = today.isoformat()

    def setUp(self):
        test_dir = self.test_dir
        parent_snap_dir = self.parent_snap_dir
        snap_dir1 = self.snap_dir1
        snap_dir2 = self.snap_dir2
        link_dir = self.link_dir
        receive_dir = self.receive_dir

        os.mkdir(test_dir)
        os.mkdir(parent_snap_dir)
        os.mkdir(snap_dir1)
        os.mkdir(snap_dir2)
        os.mkdir(receive_dir)
        subprocess.call(['btrfs', 'subvolume', 'create', link_dir])
        os.symlink(link_dir, os.path.join(snap_dir1, 'target'))
        os.symlink(link_dir, os.path.join(snap_dir2, 'target'))

    def tearDown(self):
        test_dir = self.test_dir
        snap_dir1 = self.snap_dir1
        snap_dir2 = self.snap_dir2
        link_dir = self.link_dir
        receive_dir = self.receive_dir

        r_snap_dir1 = os.path.join(receive_dir, 'snap_dir1')
        r_snap_dir2 = os.path.join(receive_dir, 'snap_dir2')

        dirs_with_btrfs_subvolumes = (
                                      snap_dir1,
                                      snap_dir2,
                                      r_snap_dir1,
                                      r_snap_dir2,
                                      receive_dir,
                                      link_dir
                                      )

        for folder in dirs_with_btrfs_subvolumes:
            g = glob.glob(folder + r'/*')
            for f in g:
                subprocess.call(['btrfs', 'subvolume', 'delete', f])
            subprocess.call(['btrfs', 'subvolume', 'delete', folder])

        shutil.rmtree(test_dir)

    def test_sendreceive(self):
        send_path = self.snap_dir1
        receive_path = self.receive_dir
        link_path = self.link_dir
        timestamp = self.timestamp

        # create some snapshots
        count = 1
        while count <= 5:
            subprocess.call(['btrfs', 'subvolume', 'snap', '-r',
                             link_path,
                             os.path.join(send_path, '{}-000{}'.format(timestamp, count))])
            count += 1

        btrsnap.sendreceive(send_path, receive_path)

        pattern = re.compile('\d{4}-\d{2}-\d{2}-\d{4}')

        r_snaps = [x for x in os.listdir(receive_path) if os.path.isdir(os.path.join(receive_path, x)) and re.search(pattern, x)]
        s_snaps = [x for x in os.listdir(send_path) if os.path.isdir(os.path.join(send_path, x)) and re.search(pattern, x)]
        print(r_snaps)
        print(s_snaps)
        print(send_path)
        input('?')
        self.assertTrue(len(r_snaps) == len(s_snaps), 'not all paths were transfered')
        for snapshot in s_snaps:
            self.assertIn(snapshot, r_snaps, '{} snapshot was not received'.format(snapshot))

    def test_sendreceive_deep(self):
        send_paths = self.parent_snap_dir
        send_path = self.snap_dir1
        second_send_path = self.snap_dir2
        receive_path = self.receive_dir
        link_path = self.link_dir
        timestamp = self.timestamp

        # create some snapshots
        count = 1
        while count <= 5:
            subprocess.call(['btrfs', 'subvolume', 'snap', '-r', link_path, os.path.join(send_path, '{}-000{}'.format(timestamp, count))])
            subprocess.call(['btrfs', 'subvolume', 'snap', '-r', link_path, os.path.join(second_send_path, '{}-000{}'.format(timestamp, count))])
            count += 1

        btrsnap.sendreceive_deep(send_paths, receive_path)

        pattern = re.compile('\d{4}-\d{2}-\d{2}-\d{4}')

        walker = os.walk(receive_path)
        walker = [walk[1] for walk in walker]

        r_snaps = []  # Flatten List of Lists
        for subs in walker:
            r_snaps.extend(subs)
        r_snaps = [snap for snap in r_snaps if re.search(pattern, snap)]

        walker = os.walk(send_paths)
        walker = [walk[1] for walk in walker]
        s_snaps = []
        for subs in walker:
            s_snaps.extend(subs)
        s_snaps = [snap for snap in s_snaps if re.search(pattern, snap)]

        self.assertTrue(len(r_snaps) == len(s_snaps), 'not all paths were transfered')
        for sub in s_snaps:
            self.assertIn(sub, r_snaps, '{} snapshot was not received'.format(sub))

    def test_unsnap_deep(self):
        send_paths = self.parent_snap_dir
        send_path = self.snap_dir1
        second_send_path = self.snap_dir2
        receive_path = self.receive_dir
        link_path = self.link_dir
        timestamp = self.timestamp

        # create some snapshots
        count = 1
        while count <= 5:
            subprocess.call(['btrfs', 'subvolume', 'snap', '-r', link_path, os.path.join(send_path, '{}-000{}'.format(timestamp, count))])
            subprocess.call(['btrfs', 'subvolume', 'snap', '-r', link_path, os.path.join(second_send_path, '{}-000{}'.format(timestamp, count))])
            count += 1

        def unsnap_deep_tester(keep):

            btrsnap.unsnap_deep(send_paths, keep=keep)

            pattern = re.compile('\d{4}-\d{2}-\d{2}-\d{4}')

            walker = os.walk(send_paths)
            walker = [walk[1] for walk in walker]

            snaps = []
            for subs in walker:  # Flatten List of Lists
                snaps.extend(subs)
            snaps = [snap for snap in snaps if re.search(pattern, snap)]

            self.assertEqual(len(snaps), 2 * keep,
                             "Wrong number of snapshots survived")

        for keep in range(5, -1, -1):
            unsnap_deep_tester(keep)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
