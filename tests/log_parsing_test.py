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
    
        