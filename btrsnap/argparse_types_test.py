'''
Created on Jun 18, 2014

@author: mike
'''
import unittest
import datetime
import argparse

from dateutil.relativedelta import relativedelta

import argparse_types as at


class Test_DateParser_Function(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_ymd_format(self):
        string = '4y4m1d2w'
        result = at.date_parser(string)

        self.assertIsInstance(result, relativedelta, 'should return a datetime.timedelta object')

    def test_ymd_large_values(self):
        string = '1000y55m71d'
        result = at.date_parser(string)

        self.assertIsInstance(result, relativedelta, 'should return a datetime.timedelta object')

    def test_ymd_one_value(self):
        string = '4y'
        result = at.date_parser(string)
        self.assertIsInstance(result, relativedelta, 'should return a datetime.timedelta object')

    def test_ymd_duplicate_value(self):
        string = '99y98y'
        self.assertRaises(argparse.ArgumentTypeError, at.date_parser, string)

    def test_ymd_result_should_match_timedelta(self):
        today = datetime.date.today()
        delta = datetime.timedelta(days=1)
        string = '1d'

        result = at.date_parser(string)
        expected = today - delta
        got = today - result
        self.assertEqual(expected, got, 'should be equal')


    def test_iso_format(self):
        today = datetime.date.today()
        string = datetime.date.today().isoformat()
        result = at.date_parser(string)
        self.assertIsInstance(result, relativedelta, 'should return a datetime.timedelta object')

        expected = today - datetime.timedelta()  # timedelta should be 0 for today
        got = today - result
        self.assertEqual(expected, got, 'should be the same')

    def test_iso_invalid_date(self):
        string = '5555-55-55'
        self.assertRaises(argparse.ArgumentTypeError, at.date_parser, string)

    def test_iso_future_date(self):
        today = datetime.date.today()
        delta = datetime.timedelta(days=1)
        future = today + delta
        string = future.isoformat()
        self.assertRaises(argparse.ArgumentTypeError, at.date_parser, string)

    def test_format_not_recogonized(self):
        string = 'garbally-gook'
        self.assertRaises(argparse.ArgumentTypeError, at.date_parser, string)


if __name__ == '__main__':
        unittest.main()
