import datetime
import unittest

from time_tracker import *

class TestSpan(unittest.TestCase):

    def test_duration(self):
        s = Span(datetime.datetime(2021, 4, 11, 11, 6, 5), datetime.datetime(2021, 4, 11, 11, 7, 21))
        self.assertEqual(s.duration(), datetime.timedelta(seconds=76))
    
    def test_format(self):
        s = Span(datetime.datetime(2021, 4, 11, 11, 6, 5), datetime.datetime(2021, 4, 11, 11, 7, 21))
        self.assertEqual(f"{s}", "11:06-11:07 (0:01)")