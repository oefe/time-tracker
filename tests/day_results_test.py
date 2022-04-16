import datetime
import unittest

from time_tracker import Activity, DayResults, Event, Level

class TestDayResults(unittest.TestCase):

    def test_empty(self):
        d = DayResults([])
        self.assertEqual(d.level, Level.ERROR)
        self.assertEqual(d.total_hours, 0.0)
        self.assertEqual(len(d.messages), 1)
        self.assertEqual(d.messages[0].text, "No log file")

    def test_just_started(self):
        events = [
            Event(datetime.datetime.now(), "ignored", Activity.WORKING),
        ]
        d = DayResults(events)
        self.assertEqual(d.level, Level.INFO)
        self.assertEqual(d.total_hours, 0.0)
        self.assertEqual(d.messages, [])
       