import datetime
from io import StringIO
import unittest

from time_tracker import *

class TestSpan(unittest.TestCase):

    def test_duration(self):
        s = Span(datetime.datetime(2021, 4, 11, 11, 6, 5), datetime.datetime(2021, 4, 11, 11, 7, 21))
        self.assertEqual(s.duration(), datetime.timedelta(seconds=76))
    
    def test_format(self):
        s = Span(datetime.datetime(2021, 4, 11, 11, 6, 5), datetime.datetime(2021, 4, 11, 11, 7, 21))
        self.assertEqual(f"{s}", "11:06-11:07 (0:01)")


class TestParsing(unittest.TestCase):

    def test_parse(self):
        e = parse_log_line("2021-03-17 08:27:26.546794\tcom.apple.screenIsUnlocked\tWORKING")
        self.assertEqual(e.timestamp, datetime.datetime(2021, 3, 17, 8, 27, 26, 546794))
        self.assertEqual(e.name, "com.apple.screenIsUnlocked")
        self.assertEqual(e.activity, Activity.WORKING)
    
    def test_parse_legacy_two_field_format_unlock(self):
        e = parse_log_line("2021-03-17 08:27:26.546794\tScreenUnlock")
        self.assertEqual(e.timestamp, datetime.datetime(2021, 3, 17, 8, 27, 26, 546794))
        self.assertEqual(e.name, "ScreenUnlock")
        self.assertEqual(e.activity, Activity.WORKING)
    
    def test_parse_legacy_two_field_format_lock(self):
        e = parse_log_line("2021-03-17 08:27:26.546794\tScreenLock")
        self.assertEqual(e.timestamp, datetime.datetime(2021, 3, 17, 8, 27, 26, 546794))
        self.assertEqual(e.name, "ScreenLock")
        self.assertEqual(e.activity, Activity.IDLE)
    
    def test_parse_invalid_date(self):
        with self.assertRaises(ValueError):
            _ = parse_log_line("2021-02-31 08:27:26.546794\tcom.apple.screenIsUnlocked\tWORKING")
    
    def test_parse_too_few_fields(self):
        with self.assertRaises(ValueError):
            _ = parse_log_line("2021-02-17 08:27:26.546794")

    def test_parse_too_many_fields_are_ignored(self):
        e = parse_log_line("2021-03-17 08:27:26.546794\tcom.apple.screenIsUnlocked\tWORKING\tfoo")
        self.assertEqual(e.timestamp, datetime.datetime(2021, 3, 17, 8, 27, 26, 546794))
        self.assertEqual(e.name, "com.apple.screenIsUnlocked")
        self.assertEqual(e.activity, Activity.WORKING)
    
    def test_parse_file(self):
        log = """
        2021-03-31 15:46:35.509057\ta\tWORKING
        2021-03-31 15:56:32.464708\tb\tIDLE
        2021-03-31 19:09:28.116408\tc\tWORKING
        2021-03-31 19:53:25.445726\td\tIDLE
        """.strip()
        expected = [
            Event(datetime.datetime(2021, 3, 31, 15, 46, 35, 509057), "a", Activity.WORKING),
            Event(datetime.datetime(2021, 3, 31, 15, 56, 32, 464708), "b", Activity.IDLE),
            Event(datetime.datetime(2021, 3, 31, 19,  9, 28, 116408), "c", Activity.WORKING),
            Event(datetime.datetime(2021, 3, 31, 19, 53, 25, 445726), "d", Activity.IDLE),
        ]
        events = parse_log(StringIO(log))
        self.assertEqual(events, expected)
    
    def test_parse_empty_file(self):
        self.assertEqual([], parse_log(StringIO("")))

        