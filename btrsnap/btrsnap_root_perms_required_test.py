#!/usr/bin/python
'''
**These tests must be run with root permissions**

You must set the environment variable ``BTRSNAP_TEST_DIR`` to point to
a directory in the *root* BTRFS volume. If a non-root subvolume is specified,
the Send and Receive tests will fail.

    example:
    export BTRSNAP_TEST_DIR='/mnt/BTRFSROOT/'
    python btrsnap_root_perms_required_test.py
'''
import unittest
import os
import shutil
import datetime
import subprocess
import re
import glob

from dateutil.relativedelta import relativedelta

import btrsnap


def get_test_dir():
    try:
        environ_path = os.path.expanduser(os.environ['BTRSNAP_TEST_DIR'])
        test_dir = os.path.join(
            os.path.realpath(os.path.abspath(environ_path)),
            'btrsnap_test_dir'
            )
    except Exception:
        print(__doc__)
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

        btrsnap.send_receive(send_path, receive_path)
        pattern = re.compile('\d{4}-\d{2}-\d{2}-\d{4}')

        r_snaps = [x for x in os.listdir(receive_path) if os.path.isdir(os.path.join(receive_path, x)) and re.search(pattern, x)]
        s_snaps = [x for x in os.listdir(send_path) if os.path.isdir(os.path.join(send_path, x)) and re.search(pattern, x)]
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

        btrsnap.send_receive_deep(send_paths, receive_path)

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

    def test_unsnap_deep_keep(self):
        parent_path = self.parent_snap_dir
        first_send_path = self.snap_dir1
        second_send_path = self.snap_dir2
        link_path = self.link_dir
        timestamp = self.timestamp

        # create some snapshots
        count = 1
        while count <= 5:
            subprocess.call(['btrfs', 'subvolume', 'snap', '-r', link_path, os.path.join(first_send_path, '{}-000{}'.format(timestamp, count))])
            subprocess.call(['btrfs', 'subvolume', 'snap', '-r', link_path, os.path.join(second_send_path, '{}-000{}'.format(timestamp, count))])
            count += 1

        def unsnap_deep_tester(keep):

            btrsnap.unsnap_deep(parent_path, keep=keep)

            pattern = re.compile('\d{4}-\d{2}-\d{2}-\d{4}')

            walker = os.walk(parent_path)
            folders = [walk[1] for walk in walker]

            snaps = []
            for folder in folders:  # Flatten List of Lists
                snaps.extend(folder)
            snaps = [snap for snap in snaps if re.search(pattern, snap)]
            self.assertEqual(len(snaps), 2 * keep,
                             "Wrong number of snapshots survived")

        for keep in range(5, -1, -1):
            unsnap_deep_tester(keep)

    def test_unsnap_deep_date(self):
        parent_path = self.parent_snap_dir
        first_send_path = self.snap_dir1
        second_send_path = self.snap_dir2
        link_path = self.link_dir
        timestamp_today = self.timestamp
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        timestamp_yesterday = yesterday.isoformat()

        # create some snapshots
        count = 1
        while count <= 5:
            subprocess.call(['btrfs', 'subvolume', 'snap', '-r', link_path, os.path.join(first_send_path, '{}-000{}'.format(timestamp_today, count))])
            subprocess.call(['btrfs', 'subvolume', 'snap', '-r', link_path, os.path.join(second_send_path, '{}-000{}'.format(timestamp_yesterday, count))])
            count += 1

        def assert_snap_count(expected):
            pattern = re.compile('\d{4}-\d{2}-\d{2}-\d{4}')
            walker = os.walk(parent_path)
            folders = [walk[1] for walk in walker]
            snaps = []
            for folder in folders:  # Flatten List of Lists
                snaps.extend(folder)
            snaps = [snap for snap in snaps if re.search(pattern, snap)]
            self.assertEqual(len(snaps), expected,
                             "Wrong number of snapshots survived")
        # delete yesterday's
        btrsnap.unsnap_deep(parent_path, keep=None, date=relativedelta(days=1))
        assert_snap_count(5)

        # delete today's
        btrsnap.unsnap_deep(parent_path, keep=None, date=relativedelta(days=0))
        assert_snap_count(0)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
