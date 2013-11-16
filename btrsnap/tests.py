'''
Created on Nov 15, 2013

@author: mike
'''
import unittest
import os
import shutil

import btrsnap


class Test_Path_Class(unittest.TestCase):

    test_dir = ''

    def setUp(self):
        try:
            environ_path = os.path.expanduser(os.environ['BTRSNAP_TEST_DIR'])
            self.test_dir = os.path.join(os.path.realpath(os.path.abspath(environ_path)), 'btrsnap_test_dir')
            
        except Exception:
            print('you must assign the environment variable BTRSNAP_TEST_DIR=PATH\n'
                  + 'Where path = a path on a btrfs filesystem')
        
        test_dir = self.test_dir
        if os.path.isdir(test_dir):
            print('{} exists. Please remove it and re-run tests'.format(test_dir))
            exit(1)
        os.mkdir(test_dir)
        print(test_dir)
                
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


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()