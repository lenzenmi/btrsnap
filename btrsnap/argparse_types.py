'''
Contains functions to be used as types with the command parser argparse
'''
import argparse
import re
import collections
import datetime

from dateutil.relativedelta import relativedelta


def date_parser(string):
    '''
    Parses a string and returns a datetime.relativedelta.relativedelta
    object.

    :Args:
        * string(str): two formats are accepted
            1. yyyy-mm-dd eg: ``2014-01-05``
            2. ?y?m?d eg: ``0y2m1d``

    :Returns:
        * dateutil.relativedelta:
            set by the input string
    '''
    ymd_pattern = re.compile(r'(\d+)([y,m,d,w])', re.IGNORECASE)
    iso_pattern = re.compile(r'^(\d{4})-(\d{2})-(\d{2})$')
    iso_match = re.search(iso_pattern, string)
    ymd_match = re.findall(ymd_pattern, string)

    if (ymd_match
        and len(ymd_match) <= 4
        and not iso_match):

        counter = collections.Counter(period[1] for period
                                      in ymd_match)
        if counter.most_common()[0][1] > 1:
            raise argparse.ArgumentTypeError('\'{}\' was specified more'
                      ' than once'.format(counter.most_common()[0][0]))

        ymd = {'y': 0, 'm': 0, 'd': 0, 'w': 0}
        for item in ymd_match:
            num, period = item
            if int(num) < 0:
                raise argparse.ArgumentTypeError('\'{}{}\can not be negative'
                                                 .format(num, period))
            ymd[period.lower()] += int(num)

        return relativedelta(years=ymd['y'], months=ymd['m'],
                             days=ymd['d'], weeks=ymd['w'])

    elif iso_match:
        year, month, day = iso_match.groups()
        # Check to make sure the date is valid and in the future
        today = datetime.date.today()
        try:
            date = datetime.date(int(year), int(month), int(day))
            if date > today:
                raise argparse.ArgumentTypeError('{}-{}-{} is in the future'
                                                 .format(year, month, day))
        except ValueError as e:
            raise argparse.ArgumentTypeError(e)

        return relativedelta(year=int(year),
                             month=int(month),
                             day=int(day))

    raise argparse.ArgumentTypeError('\'{}\' is not a recognized date'
                                         ' format'.format(string))
