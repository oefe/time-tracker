import datetime
from typing import List
import unittest

from time_tracker import *

class TestSpan(unittest.TestCase):

    def test_duration(self):
        s = Span(datetime.datetime(2021, 4, 11, 11, 6, 5), datetime.datetime(2021, 4, 11, 11, 7, 21))
        self.assertEqual(s.duration(), datetime.timedelta(seconds=76))
    
    def test_format(self):
        s = Span(datetime.datetime(2021, 4, 11, 11, 6, 5), datetime.datetime(2021, 4, 11, 11, 7, 21))
        self.assertEqual(f"{s}", "11:06-11:07 (0:01)")

    def test_get_spans_empty(self):
        events: List[Event] = []
        spans = list(get_work_spans(events))
        self.assertEqual(spans, [])
    
    def test_get_spans_idle(self):
        events = [
            Event(datetime.datetime(2021, 4, 11, 17, 30), "ignored", Activity.IDLE),
        ]
        spans = list(get_work_spans(events))
        self.assertEqual(spans, [])
    
    def test_get_spans_working(self):
        events = [
            Event(datetime.datetime(2021, 4, 11, 17, 30), "", Activity.WORKING),
        ]
        now = datetime.datetime(2021, 4, 11, 20, 30)
        spans = list(get_work_spans(events, now))
        expected = [
            Span(events[0].timestamp, now)
        ]
        self.assertEqual(spans, expected)

    def test_get_spans_idle_idle(self):
        events = [
            Event(datetime.datetime(2021, 4, 11, 17, 30), "ignored", Activity.IDLE),
            Event(datetime.datetime(2021, 4, 11, 17, 40), "ignored", Activity.IDLE),
        ]
        spans = list(get_work_spans(events))
        self.assertEqual(spans, [])
    
    def test_get_spans_idle_working(self):
        events = [
            Event(datetime.datetime(2021, 4, 11, 17, 30), "ignored", Activity.IDLE),
            Event(datetime.datetime(2021, 4, 11, 17, 40), "", Activity.WORKING)
        ]
        now = datetime.datetime(2021, 4, 11, 20, 30)
        spans = list(get_work_spans(events, now))
        expected = [
            Span(events[1].timestamp, now)
        ]
        self.assertEqual(spans, expected)
        
    def test_get_spans_working_idle(self):
        events = [
            Event(datetime.datetime(2021, 4, 11, 17, 30), "", Activity.WORKING),
            Event(datetime.datetime(2021, 4, 11, 17, 40), "", Activity.IDLE)
        ]
        spans = list(get_work_spans(events))
        expected = [
            Span(events[0].timestamp, events[1].timestamp)
        ]
        self.assertEqual(spans, expected)
     
    def test_get_spans_working_working(self):
        events = [
            Event(datetime.datetime(2021, 4, 11, 17, 30), "", Activity.WORKING),
            Event(datetime.datetime(2021, 4, 11, 17, 40), "ignored", Activity.WORKING)
        ]
        now = datetime.datetime(2021, 4, 11, 20, 30)
        spans = list(get_work_spans(events, now))
        expected = [
            Span(events[0].timestamp, now)
        ]
        self.assertEqual(spans, expected)
        
    def test_get_spans_working_working_idle(self):
        events = [
            Event(datetime.datetime(2021, 4, 11, 17, 30), "", Activity.WORKING),
            Event(datetime.datetime(2021, 4, 11, 17, 40), "ignored", Activity.WORKING),
            Event(datetime.datetime(2021, 4, 11, 17, 50), "", Activity.IDLE)
        ]
        spans = list(get_work_spans(events))
        expected = [
            Span(events[0].timestamp, events[2].timestamp)
        ]
        self.assertEqual(spans, expected)
      
    def test_get_spans_working_idle_idle(self):
        events = [
            Event(datetime.datetime(2021, 4, 11, 17, 30), "", Activity.WORKING),
            Event(datetime.datetime(2021, 4, 11, 17, 40), "", Activity.IDLE),
            Event(datetime.datetime(2021, 4, 11, 17, 50), "ignored", Activity.IDLE)
        ]
        spans = list(get_work_spans(events))
        expected = [
            Span(events[0].timestamp, events[1].timestamp)
        ]
        self.assertEqual(spans, expected)
      
    def test_get_spans_working_idle_working_idle(self):
        events = [
            Event(datetime.datetime(2021, 4, 11, 17, 30), "", Activity.WORKING),
            Event(datetime.datetime(2021, 4, 11, 17, 40), "", Activity.IDLE),
            Event(datetime.datetime(2021, 4, 11, 17, 45), "", Activity.WORKING),
            Event(datetime.datetime(2021, 4, 11, 17, 50), "", Activity.IDLE)
        ]
        spans = list(get_work_spans(events))
        expected = [
            Span(events[0].timestamp, events[1].timestamp),
            Span(events[2].timestamp, events[3].timestamp),
        ]
        self.assertEqual(spans, expected)
  
