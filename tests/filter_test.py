import datetime
import unittest

from time_tracker import Span, filter_spans

class TestFilter(unittest.TestCase):

    def test_short_break(self):
        input = [
            Span(datetime.datetime(2020, 4, 11, 18, 10), datetime.datetime(2020, 4, 11, 18, 20)),
            Span(datetime.datetime(2020, 4, 11, 18, 21), datetime.datetime(2020, 4, 11, 18, 40)),
        ]
        output = filter_spans(input)
        expected = [
            Span(datetime.datetime(2020, 4, 11, 18, 10), datetime.datetime(2020, 4, 11, 18, 40)),
        ]
        self.assertEqual(output, expected)

    def test_long_break(self):
        input = [
            Span(datetime.datetime(2020, 4, 11, 18, 10), datetime.datetime(2020, 4, 11, 18, 20)),
            Span(datetime.datetime(2020, 4, 11, 18, 30), datetime.datetime(2020, 4, 11, 18, 40)),
        ]
        output = filter_spans(input)
        self.assertEqual(output, input)

    def test_short_work(self):
        input = [
            Span(datetime.datetime(2020, 4, 11, 18, 10), datetime.datetime(2020, 4, 11, 18, 11)),
        ]
        output = filter_spans(input)
        self.assertEqual(output, [])        

    def test_long_work(self):
        input = [
            Span(datetime.datetime(2020, 4, 11, 18, 10), datetime.datetime(2020, 4, 11, 18, 20)),
        ]
        output = filter_spans(input)
        self.assertEqual(output, input)        
                  