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

    def test_incomplete_log(self):
        events = [
            Event(
                datetime.datetime(2025, 1, 25, 19, 19, 0), "ignored", Activity.WORKING
            ),
        ]
        d = DayResults(events)
        self.assertEqual(d.level, Level.ERROR)
        self.assertEqual(len(d.messages), 1)
        self.assertEqual(
            d.messages[0].text, "Started work at 19:19 without corresponding end!"
        )

    def test_total_is_rounded_down_down(self):
        events = [
            Event(datetime.datetime(2025, 1, 26, 19, 10, 0), "", Activity.WORKING),
            Event(datetime.datetime(2025, 1, 26, 19, 40, 29), "", Activity.IDLE),
        ]
        d = DayResults(events)
        self.assertEqual(d.total_hours, 0.5)

    def test_total_is_rounded_down_up(self):
        events = [
            Event(datetime.datetime(2025, 1, 26, 19, 10, 0), "", Activity.WORKING),
            Event(datetime.datetime(2025, 1, 26, 19, 40, 30), "", Activity.IDLE),
        ]
        d = DayResults(events)
        self.assertAlmostEqual(d.total_hours, 0.51666667)

    def test_total_is_rounded_up_down(self):
        events = [
            Event(datetime.datetime(2025, 1, 26, 19, 10, 31), "", Activity.WORKING),
            Event(datetime.datetime(2025, 1, 26, 19, 40, 0), "", Activity.IDLE),
        ]
        d = DayResults(events)
        self.assertAlmostEqual(d.total_hours, 0.4833333)

    def test_total_is_rounded_up_up(self):
        events = [
            Event(datetime.datetime(2025, 1, 26, 19, 10, 59), "", Activity.WORKING),
            Event(datetime.datetime(2025, 1, 26, 19, 40, 30), "", Activity.IDLE),
        ]
        d = DayResults(events)
        self.assertEqual(d.total_hours, 0.5)
