#!/usr/bin/python
'''
You must set the environment variable ``BTRSNAP_TEST_DIR`` to point to a
directory on a BTRFS filesystem.

    example:
    BTRSNAP_TEST_DIR='~/' python btrsnap_test.py

*BTRFS snapshots need to be deleted by a regular user. To allow this the
filesystem **must** be mounted with the mount option ``usr_subvol_rm_allowed``
'''
import unittest
import os
import shutil
import datetime
import subprocess

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


class Test_Path_Class(unittest.TestCase):

    test_dir = get_test_dir()

    def setUp(self):

        test_dir = self.test_dir
        os.mkdir(test_dir)

    def tearDown(self):
        test_dir = self.test_dir
        shutil.rmtree(test_dir)

    def test_path_valid_path(self):
        test_dir = os.path.join(self.test_dir, 'empty_path')
        os.mkdir(test_dir)
        path = btrsnap.Path(test_dir)
        self.assertEqual(test_dir, path.path)

    def test_path_invalid_path(self):
        test_dir = os.path.join(self.test_dir, 'not_a_dir')
        self.assertRaises(btrsnap.PathError, btrsnap.Path, test_dir)

    def test_path_userexpansion(self):
        path = btrsnap.Path('~')
        self.assertEqual(path.path, os.path.expanduser('~'))

    def test_path_relative_path(self):
        test_dir = self.test_dir
        rel_path = 'empty_path'
        os.mkdir(os.path.join(self.test_dir, 'empty_path'))
        os.chdir(test_dir)
        path = btrsnap.Path(rel_path)
        self.assertEqual(os.path.abspath(os.path.join(test_dir, rel_path)),
                         path.path)


class Test_ReceivePath_Class(unittest.TestCase):
    '''
    Most of this class's functionality is tested in other test classes as it
    is comprised of mixins.
    '''
    test_dir = get_test_dir()
    snap_dir = os.path.join(test_dir, 'snap_dir')
    timestamps = ['2012-01-01-0001',
                  '2012-01-01-0002',
                  '2012-02-01-0001',
                  '2012-02-01-0002']

    def setUp(self):
        test_dir = self.test_dir
        snap_dir = self.snap_dir
        timestamps = self.timestamps

        os.mkdir(test_dir)
        os.mkdir(snap_dir)
        for folder in timestamps:
            os.mkdir(os.path.join(snap_dir, folder))

    def tearDown(self):
        test_dir = self.test_dir
        shutil.rmtree(test_dir)

    def test_ReceivePath_list_normal(self):
        snap_dir = self.snap_dir
        timestamps = sorted(self.timestamps, reverse=True)
        snap = btrsnap.Path(snap_dir)
        self.assertEqual(timestamps, snap.snapshots())


class Test_SnapPath_Class(unittest.TestCase):

    test_dir = get_test_dir()
    snap_dir = os.path.join(test_dir, 'snap_dir')
    link_dir = os.path.join(test_dir, 'link_dir')
    timestamps = ['2012-01-01-0001',
                  '2012-01-01-0002',
                  '2012-02-01-0001',
                  '2012-02-01-0002']

    def setUp(self):
        test_dir = self.test_dir
        snap_dir = self.snap_dir
        link_dir = self.link_dir
        timestamps = self.timestamps

        os.mkdir(test_dir)
        os.mkdir(snap_dir)
        os.mkdir(link_dir)
        os.symlink(link_dir, os.path.join(snap_dir, 'target'))
        for folder in timestamps:
            os.mkdir(os.path.join(snap_dir, folder))

    def tearDown(self):
        test_dir = self.test_dir
        shutil.rmtree(test_dir)

    def test_SnapPath_snapshotsMixin_normal(self):
        snap_dir = self.snap_dir
        timestamps = sorted(self.timestamps, reverse=True)
        snap = btrsnap.SnapPath(snap_dir)
        self.assertEqual(timestamps, snap.snapshots())

    def test_SnapPath_snapshotsMixin_ignore_files(self):
        snap_dir = self.snap_dir
        timestamps = sorted(self.timestamps, reverse=True)
        file_with_timestamp_name = os.path.join(snap_dir, '2013-01-01-0001')
        open(file_with_timestamp_name, 'w').close()

        snap = btrsnap.SnapPath(snap_dir)
        self.assertEqual(timestamps, snap.snapshots())

    def test_SnapPath_snapshotsMixin_ignore_folders_without_timestamp(self):
        snap_dir = self.snap_dir
        timestamps = sorted(self.timestamps, reverse=True)
        os.mkdir(os.path.join(snap_dir, 'some-unrelated-dir'))

        snap = btrsnap.SnapPath(snap_dir)
        self.assertEqual(timestamps, snap.snapshots())

    def test_SnapPath_snapshotsMixin_ignore_timestamp_like_folders(self):
        snap_dir = self.snap_dir
        timestamps = sorted(self.timestamps, reverse=True)
        os.mkdir(os.path.join(snap_dir, '2013-07-11-0001-bogus'))
        os.mkdir(os.path.join(snap_dir, 'bogus-2013-07-11-002'))

        snap = btrsnap.SnapPath(snap_dir)
        self.assertEqual(timestamps, snap.snapshots(),
                         'bogus folders should be ignored')

    def test_SnapPath_ensure_symlink_exists(self):
        snap_dir = self.snap_dir
        os.unlink(os.path.join(snap_dir, 'target'))

        self.assertRaises(btrsnap.TargetError, btrsnap.SnapPath, snap_dir)

    def test_SnapPath_ensure_only_one_symlink(self):
        snap_dir = self.snap_dir
        link_dir = self.link_dir
        os.symlink(link_dir, os.path.join(snap_dir, 'target2'))
        self.assertRaises(btrsnap.TargetError, btrsnap.SnapPath, snap_dir)

    def test_SnapPath_target(self):
        snap_dir = self.snap_dir
        link_dir = self.link_dir
        snap = btrsnap.SnapPath(snap_dir)
        self.assertEqual(snap.target, link_dir)

    def test_SnapPath_timestamp(self):
        snap_dir = self.snap_dir
        today = datetime.date.today()
        timestamp = today.isoformat()
        first = timestamp + '-0001'
        second = timestamp + '-0002'

        snap = btrsnap.SnapPath(snap_dir)
        self.assertEqual(first, snap.timestamp())

        os.mkdir(os.path.join(snap_dir, first))
        self.assertEqual(second, snap.timestamp())

    def test_SnapPath_timestamp_always_older(self):
        snap_dir = self.snap_dir
        today = datetime.date.today()
        timestamp = today.isoformat()
        second = timestamp + '-0002'
        third = timestamp + '-0003'

        snap = btrsnap.SnapPath(snap_dir)
        os.mkdir(os.path.join(snap_dir, second))
        self.assertEqual(third, snap.timestamp())

    def test_SnapPath_timestamp_9999_or_less(self):
        snap_dir = self.snap_dir
        today = datetime.date.today()
        timestamp = today.isoformat()
        too_big = timestamp + '-9999'

        os.mkdir(os.path.join(snap_dir, too_big))
        snap = btrsnap.SnapPath(snap_dir)
        self.assertRaises(Exception, snap.timestamp)


class Test_SnapDeep_Class(unittest.TestCase):
    test_dir = get_test_dir()
    link_dir = os.path.join(test_dir, 'link_dir')
    snap_dirs = []
    for number in range(5):
        name = 'snap_dir{}'.format(number)
        snap_dir = os.path.join(test_dir, name)
        snap_dirs.append(snap_dir)

    def setUp(self):
        test_dir = self.test_dir
        link_dir = self.link_dir
        snap_dirs = self.snap_dirs

        os.mkdir(test_dir)
        subprocess.call(['btrfs', 'subvolume', 'create', link_dir])
        for snap_dir in snap_dirs:
            os.mkdir(snap_dir)
            os.symlink(link_dir, os.path.join(snap_dir, 'target'))

    def tearDown(self):
        test_dir = self.test_dir
        link_dir = self.link_dir
        subprocess.call(['btrfs', 'subvolume', 'delete', link_dir])
        shutil.rmtree(test_dir)

    def test_Snapdeep_snap_paths(self):
        test_dir = self.test_dir
        snap_dirs = self.snap_dirs
        snap_deep = btrsnap.Path(test_dir)
        sub_snap_paths_list = snap_deep.sub_snap_paths_list()
        sub_snap_paths_list = [snap_path.path for snap_path in sub_snap_paths_list]

        self.assertEqual(len(snap_dirs), len(sub_snap_paths_list))
        for snap_path in sub_snap_paths_list:
            self.assertIn(snap_path, snap_dirs)


class Test_ReceiveDeep_Class(unittest.TestCase):
    test_dir = get_test_dir()
    timestamps = ['2012-01-01-0001',
                  '2012-01-01-0002',
                  '2012-02-01-0001',
                  '2012-02-01-0002']
    snap_dirs = []
    for number in range(5):
        name = 'snap_dir{}'.format(number)
        snap_dir = os.path.join(test_dir, name)
        snap_dirs.append(snap_dir)

    def setUp(self):
        test_dir = self.test_dir
        snap_dirs = self.snap_dirs
        timestamps = self.timestamps

        os.mkdir(test_dir)
        for snap_dir in snap_dirs:
            os.mkdir(snap_dir)
            for timestamp in timestamps:
                os.mkdir(os.path.join(snap_dir, timestamp))

    def tearDown(self):
        test_dir = self.test_dir
        shutil.rmtree(test_dir)

    def test_ReceiveDeep_snapshots(self):
        test_dir = self.test_dir
        snap_dirs = self.snap_dirs
        receive_deep = btrsnap.Path(test_dir)
        sub_paths_list = receive_deep.sub_paths_list()
        sub_paths_list = [receive_path.path for receive_path in sub_paths_list]

        self.assertEqual(len(snap_dirs), len(sub_paths_list))
        for receive_path in sub_paths_list:
            self.assertIn(receive_path, snap_dirs)

        for receive_path in receive_deep.sub_paths_list():
            self.assertIsInstance(receive_path, btrsnap.Path,
                                  'Did not receive a list of Receive Paths'
                                  )


class Test_Btrfs_Class(unittest.TestCase):
    test_dir = get_test_dir()
    snap_dir = os.path.join(test_dir, 'snap_dir')
    link_dir = os.path.join(test_dir, 'link_dir')
    receive_dir = os.path.join(test_dir, 'receive_dir')

    def setUp(self):
        test_dir = self.test_dir
        snap_dir = self.snap_dir
        link_dir = self.link_dir
        receive_dir = self.receive_dir

        os.mkdir(test_dir)
        os.mkdir(snap_dir)
        os.mkdir(receive_dir)
        subprocess.call(['btrfs', 'subvolume', 'create', link_dir])
        os.symlink(link_dir, os.path.join(snap_dir, 'target'))

    def tearDown(self):
        test_dir = self.test_dir
        link_dir = self.link_dir
        subprocess.call(['btrfs', 'subvolume', 'delete', link_dir])
        shutil.rmtree(test_dir)

    def test_Btrfs_snap(self):
        snap_dir = self.snap_dir
        link_dir = self.link_dir
        snap_name = 'test'

        btrfs = btrsnap.Btrfs(snap_dir)
        btrfs.snap(link_dir, snap_name, readonly=False)

        self.assertTrue(os.path.isdir(os.path.join(snap_dir, snap_name)))

        # cleanup
        subprocess.call(['btrfs', 'subvolume', 'delete',
                         os.path.join(snap_dir, snap_name)])

    def test_Btrfs_snap_Exception(self):
        test_dir = self.test_dir
        snap_dir = self.snap_dir
        snap_name = 'test'
        bogus_dir = os.path.join(test_dir, 'bogus_dir')

        btrfs = btrsnap.Btrfs(snap_dir)
        self.assertRaises(btrsnap.BtrfsError, btrfs.snap, bogus_dir, snap_name)

    def test_Btrfs_unsnap(self):
        snap_dir = self.snap_dir
        snap_name = 'test'
        subprocess.call(['btrfs', 'subvolume', 'create',
                         os.path.join(snap_dir, snap_name)])

        btrfs = btrsnap.Btrfs(snap_dir)
        btrfs.unsnap(snap_name)

        self.assertFalse(os.path.isdir(os.path.join(snap_dir, snap_name)))

    def test_Btrfs_unsnap_Exception(self):
        snap_dir = self.snap_dir
        bogus = 'bogus_dir'

        btrfs = btrsnap.Btrfs(snap_dir)
        self.assertRaises(btrsnap.BtrfsError, btrfs.unsnap, bogus)


class Test_functions_(unittest.TestCase):
    test_dir = get_test_dir()
    snap_dir = os.path.join(test_dir, 'snap_dir')
    link_dir = os.path.join(test_dir, 'link_dir')
    receive_dir = os.path.join(test_dir, 'receive_dir')
    timestmaps = ['2012-01-01-0001',
                  '2012-01-01-0002',
                  '2012-02-01-0001',
                  '2012-02-01-0002']

    def setUp(self):
        test_dir = self.test_dir
        snap_dir = self.snap_dir
        link_dir = self.link_dir
        receive_dir = self.receive_dir

        os.mkdir(test_dir)
        os.mkdir(snap_dir)
        os.mkdir(receive_dir)
        subprocess.call(['btrfs', 'subvolume', 'create', link_dir])
        os.symlink(link_dir, os.path.join(snap_dir, 'target'))

    def tearDown(self):
        test_dir = self.test_dir
        link_dir = self.link_dir
        subprocess.call(['btrfs', 'subvolume', 'delete', link_dir])
        shutil.rmtree(test_dir)

    def test_snap(self):
        snap_dir = self.snap_dir
        today = datetime.date.today()
        timestamp = today.isoformat()
        first = os.path.join(snap_dir, timestamp + '-0001')
        second = os.path.join(snap_dir, timestamp + '-0002')

        btrsnap.snap(snap_dir, readonly=False)
        self.assertTrue(os.path.isdir(first))
        btrsnap.snap(snap_dir, readonly=False)
        self.assertTrue(os.path.isdir(second))

        # cleanup
        subprocess.call(['btrfs', 'subvolume', 'delete', first])
        subprocess.call(['btrfs', 'subvolume', 'delete', second])

    def test_unsnap_keep(self):
        snap_dir = self.snap_dir
        link_dir = self.link_dir
        today = datetime.date.today()
        timestamp = today.isoformat()
        first = os.path.join(snap_dir, timestamp + '-0001')
        second = os.path.join(snap_dir, timestamp + '-0002')
        subprocess.call(['btrfs', 'subvolume', 'snap', link_dir, first])
        subprocess.call(['btrfs', 'subvolume', 'snap', link_dir, second])

        btrsnap.unsnap(snap_dir, keep=1)
        self.assertFalse(os.path.isdir(first))
        self.assertTrue(os.path.isdir(second))

        btrsnap.unsnap(snap_dir, keep=0)
        self.assertFalse(os.path.isdir(first))
        self.assertFalse(os.path.isdir(second))

    def test_unsnap_invalid_keep(self):
        snap_dir = self.snap_dir
        self.assertRaises(Exception, btrsnap.unsnap, snap_dir, keep=-1)
        self.assertRaises(Exception, btrsnap.unsnap, snap_dir, keep=1.5)

    def test_unsnap_keep_too_high(self):
        snap_dir = self.snap_dir
        link_dir = self.link_dir
        today = datetime.date.today()
        timestamp = today.isoformat()
        first = os.path.join(snap_dir, timestamp + '-0001')
        second = os.path.join(snap_dir, timestamp + '-0002')

        subprocess.call(['btrfs', 'subvolume', 'snap', link_dir, first])
        subprocess.call(['btrfs', 'subvolume', 'snap', link_dir, second])

        btrsnap.unsnap(snap_dir, keep=10)
        self.assertTrue(os.path.isdir(first))
        self.assertTrue(os.path.isdir(second))

        # cleanup
        btrsnap.unsnap(snap_dir, keep=0)

    def test_unsnap_date(self):
        snap_dir = self.snap_dir
        link_dir = self.link_dir
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        timestamp_today = today.isoformat()
        timestamp_yesterday = yesterday.isoformat()
        first = os.path.join(snap_dir, timestamp_today + '-0001')
        second = os.path.join(snap_dir, timestamp_yesterday + '-0002')
        subprocess.call(['btrfs', 'subvolume', 'snap', link_dir, first])
        subprocess.call(['btrfs', 'subvolume', 'snap', link_dir, second])

        btrsnap.unsnap(snap_dir, date=relativedelta(days=1))
        self.assertTrue(os.path.isdir(first))
        self.assertFalse(os.path.isdir(second))

        btrsnap.unsnap(snap_dir, date=relativedelta(days=0))
        self.assertFalse(os.path.isdir(first))
        self.assertFalse(os.path.isdir(second))

    def test_snapdeep(self):
        test_dir = self.test_dir
        snap_dir = self.snap_dir
        today = datetime.date.today()
        timestamp = today.isoformat()
        first = os.path.join(snap_dir, timestamp + '-0001')

        btrsnap.snap_deep(test_dir, readonly=False)
        self.assertTrue(os.path.isdir(first))

        # cleanup
        subprocess.call(['btrfs', 'subvolume', 'delete', first])

    def test_snapdeep_no_snappaths(self):
        test_dir = self.test_dir
        snap_dir = self.snap_dir
        today = datetime.date.today()
        timestamp = today.isoformat()
        first = os.path.join(snap_dir, timestamp + '-0001')

        os.unlink(os.path.join(snap_dir, 'target'))

        btrsnap.snap_deep(test_dir, readonly=False)
        self.assertFalse(os.path.isdir(first))

    def test_show_snaps(self):
        snap_dir = self.snap_dir
        link_dir = self.link_dir
        today = datetime.date.today()
        timestamp = today.isoformat()
        first = os.path.join(snap_dir, timestamp + '-0001')
        second = os.path.join(snap_dir, timestamp + '-0002')
        subprocess.call(['btrfs', 'subvolume', 'snap', link_dir, first])
        subprocess.call(['btrfs', 'subvolume', 'snap', link_dir, second])

        output = btrsnap.show_snaps(snap_dir)

        self.assertIn(os.path.split(first)[-1], output,
                      'first snapshot should be listed')
        self.assertIn(os.path.split(second)[-1], output,
                      'second snapshot should be listed')

        # cleanup
        subprocess.call(['btrfs', 'subvolume', 'delete', first])
        subprocess.call(['btrfs', 'subvolume', 'delete', second])

    def test_show_snaps_deep(self):
        test_dir = self.test_dir
        snap_dir = self.snap_dir
        receive_dir = self.receive_dir
        link_dir = self.link_dir
        timestamps = self.timestmaps
        for timestamp in timestamps:
            os.mkdir(os.path.join(snap_dir, timestamp))

        output = btrsnap.show_snaps_deep(test_dir)

        should_be_in_output = timestamps
        should_be_in_output.extend([test_dir, snap_dir, receive_dir, link_dir])
        for item in should_be_in_output:
            self.assertIn(item, output,
                          'More items should be listed in output')


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
