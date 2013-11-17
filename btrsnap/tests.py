'''
Created on Nov 15, 2013

@author: mike
'''
import unittest
import os
import shutil
import datetime

import btrsnap


class Test_Path_Class(unittest.TestCase):

    try:
        environ_path = os.path.expanduser(os.environ['BTRSNAP_TEST_DIR'])
        test_dir = os.path.join(os.path.realpath(os.path.abspath(environ_path)), 'btrsnap_test_dir')
    except Exception:
        print('you must assign the environment variable BTRSNAP_TEST_DIR=PATH\n'
              + 'Where path = a path on a btrfs filesystem')
        exit(1)
    if os.path.isdir(test_dir):
        print('{} exists. Please remove it and re-run tests'.format(test_dir))
        exit(1)

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
        self.assertEqual(os.path.abspath(os.path.join(test_dir, rel_path)), path.path)


class Test_SnapPath_Class(unittest.TestCase):

    try:
        environ_path = os.path.expanduser(os.environ['BTRSNAP_TEST_DIR'])
        test_dir = os.path.join(os.path.realpath(os.path.abspath(environ_path)), 'btrsnap_test_dir')
    except Exception:
        print('you must assign the environment variable BTRSNAP_TEST_DIR=PATH\n'
              + 'Where path = a path on a btrfs filesystem')
        exit(1)
    if os.path.isdir(test_dir):
        print('{} exists. Please remove it and re-run tests'.format(test_dir))
        exit(1)
        
    snap_dir = os.path.join(test_dir, 'snap_dir')
    link_dir = os.path.join(test_dir, 'link_dir')
    timestamps = ['2012-01-01-0001', '2012-01-01-0002', '2012-02-01-0001', '2012-02-01-0002']


    def setUp(self):
        test_dir = self.test_dir
        snap_dir = self.snap_dir
        link_dir = self.link_dir
                
        
        
        os.mkdir(test_dir)
        os.mkdir(snap_dir)
        os.mkdir(link_dir)
        os.symlink(link_dir, os.path.join(snap_dir, 'target'))
        
        timestamps = self.timestamps
        for folder in timestamps:
            os.mkdir(os.path.join(snap_dir, folder))
                
    def tearDown(self):
        test_dir = self.test_dir
        shutil.rmtree(test_dir)
        
    def test_SnapPath_list_normal(self):
        snap_dir = self.snap_dir
        timestamps = sorted(self.timestamps, reverse=True)
        snap = btrsnap.SnapPath(snap_dir)
        self.assertEqual(timestamps, snap.snapshots())
            
    def test_SnapPath_list_ignore_files(self):
        snap_dir = self.snap_dir
        timestamps = sorted(self.timestamps, reverse=True)
        file_with_timestamp_name = os.path.join(snap_dir, '2013-01-01-0001')
        open(file_with_timestamp_name, 'w').close
        
        snap = btrsnap.SnapPath(snap_dir)
        self.assertEqual(timestamps, snap.snapshots())
    
    def test_SnapPath_list_ignore_folders_without_timestamp(self):
        snap_dir = self.snap_dir
        timestamps = sorted(self.timestamps, reverse=True)
        os.mkdir(os.path.join(snap_dir, 'some-unrelated-dir'))
      
        snap = btrsnap.SnapPath(snap_dir)
        self.assertEqual(timestamps, snap.snapshots())   
        
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
      

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()