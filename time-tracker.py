#!/usr/bin/env python
# <bitbar.title>Time Tracker</bitbar.title>
# <bitbar.version>v0.1</bitbar.version>
# <bitbar.author>Martina Oefelein</bitbar.author>
# <bitbar.author.github>oefe</bitbar.author.github>
# <bitbar.desc>Utilities to track my working hours</bitbar.desc>
# <bitbar.image></bitbar.image>
# <bitbar.dependencies>python</bitbar.dependencies>
# <bitbar.abouturl>http://oefelein.de/</bitbar.abouturl>

from dataclasses import dataclass
import datetime
import enum
import os
import os.path
import sys
from typing import Iterable, Optional, Sequence, Tuple

BARS = " ▁▂▃▄▅▆▇█"
LOGDIR = os.path.expanduser("~/.time-tracker")

class Activity (enum.Enum):
    IDLE = 0
    WORKING = 1

SHORT_BREAK = datetime.timedelta(minutes=3)
SHORT_WORK = datetime.timedelta(minutes=1)

Event = Tuple[datetime.datetime, str, Activity]
Span = Tuple[datetime.datetime, datetime.datetime]

def get_log_filename(day: Optional[datetime.date]=None) -> str:
    if day is None:
        day = datetime.date.today()
    return os.path.join(LOGDIR, f"{day}.log")
    
def log_event(name: str, activity: Activity):
    os.makedirs(LOGDIR, exist_ok=True)
    now = datetime.datetime.now()
    filename = get_log_filename(now.date())
    with open(filename, mode="a") as log:
        print(now, name, activity.name, sep="\t", file=log)

def parse_log_line(line: str) -> Event:
    timestamp, event, *rest = line.strip().split("\t")
    if rest:
        activity = Activity[rest[0]]
    elif event == "ScreenUnlock":
        activity = Activity.WORKING
    else:
        activity = Activity.IDLE
    return datetime.datetime.fromisoformat(timestamp), event, activity

def load_log(day: Optional[datetime.date]=None) -> Sequence[Event]:
    filename = get_log_filename(day)
    with open(filename) as log:
        lines = log.readlines()
    return [parse_log_line(line) for line in lines]

def get_work_spans(events: Sequence[Event]) -> Sequence[Span]:
    spans: list[Span] = []
    working = False
    start = datetime.datetime.now()
    for (d, _, activity) in events:
        if activity is Activity.WORKING:
            if not working:
                working = True
                start = d
        else:
            if working:
                working = False
                spans.append((start, d))
    if working:
        spans.append((start, datetime.datetime.now()))
    return spans

def filter_short_breaks(spans: Sequence[Span]) -> Iterable[Span]:
    (current_start, current_end) = spans[0]
    for (next_start, next_end) in spans[1:]:
        if next_start - current_end < SHORT_BREAK:
            current_end = next_end
        else:
            yield (current_start, current_end)
            (current_start, current_end) = (next_start, next_end)
    yield (current_start, current_end)

def filter_short_work(spans: Iterable[Span]) -> Sequence[Span]:
    return [(start, end) for (start, end) in spans if end - start > SHORT_WORK]

def get_cumulative_work_today(spans: Iterable[Span]) -> datetime.timedelta:
    durations = [end - start for (start, end) in spans]
    #TODO adjust durations for required breaks
    return sum(durations, datetime.timedelta())

def format_timedelta(td: datetime.timedelta) -> str:
    # work around https://github.com/microsoft/pyright/issues/1629
    # hours, rest = divmod(td, datetime.timedelta(hours=1))
    hours = td // datetime.timedelta(hours=1)
    rest = td % datetime.timedelta(hours=1) 
    minutes = rest // datetime.timedelta(minutes=1)
    return f"{hours}:{minutes:02}"

class Level(enum.IntEnum):
    INFO = 0
    PRAISE = 1
    WARNING = 2
    ERROR = 3

    def format(self):
        return ["", "color=green", "color=orange", "color=red"][self.value]

@dataclass
class Message:
    level: Level
    text: str

def get_messages(spans: Sequence[Span], total_hours: float) -> Iterable[Message]:
    if total_hours > 10.0:
        yield Message(Level.ERROR, "Your worked already longer than allowed")
    elif total_hours > 9.0:
        yield Message(Level.WARNING, "You really worked enough for today")
    elif 7.75 < total_hours < 8.25:
        yield Message(Level.PRAISE, "You worked enough for today")
    _, end = spans[-1]
    if end.hour >= 22:
        yield Message(Level.ERROR, "Stop working now, it's after 10pm!")
    elif end.hour >= 21:
        yield Message(Level.WARNING, "Time to stop working?")

def write_menu():
    try:
        events = load_log()
    except FileNotFoundError:
        print ("❓")
        print("---")
        print("No log file")
        return
    except Exception as e:
        print ("⁉️")
        print("---")
        print(e)
        return
    spans = get_work_spans(events)
    spans = filter_short_breaks(spans)
    spans = filter_short_work(spans)
    cumulative_work_today = get_cumulative_work_today(spans)
    hours = cumulative_work_today / datetime.timedelta(hours=1)
    messages = list(get_messages(spans, hours))
    level = max([m.level for m in messages], default=Level.INFO)
    print(f"{format_timedelta(cumulative_work_today)} {BARS[min(int(hours), 8)]}|{level.format()}")
    print("---")
    for message in messages:
        print(f"{message.text}|{message.level.format()}")
    for (start, end) in spans:
        print(f"{start:%H:%M}-{end:%H:%M} ({format_timedelta(end-start)})")
    
def run_agent():
    import AppKit
    import Foundation
    from PyObjCTools import AppHelper
    class Observer(Foundation.NSObject):
        def onActivation_(self, notification: Foundation.NSNotification):
            log_event(notification.name(), Activity.WORKING)    

        def onDeactivation_(self, notification: Foundation.NSNotification):
            log_event(notification.name(), Activity.IDLE)    

    nc = Foundation.NSDistributedNotificationCenter.defaultCenter()
    observer = Observer.new()
    nc.addObserver_selector_name_object_suspensionBehavior_(
        observer,
        'onDeactivation:',
        'com.apple.screenIsLocked',
        None,
        Foundation.NSNotificationSuspensionBehaviorDeliverImmediately)
    nc.addObserver_selector_name_object_suspensionBehavior_(
        observer,
        'onActivation:',
        'com.apple.screenIsUnlocked',
        None,
        Foundation.NSNotificationSuspensionBehaviorDeliverImmediately)
    wnc = AppKit.NSWorkspace.sharedWorkspace().notificationCenter()
    for notification in (
        AppKit.NSWorkspaceSessionDidBecomeActiveNotification,
        AppKit.NSWorkspaceDidWakeNotification,
        AppKit.NSWorkspaceScreensDidWakeNotification,        
    ):
        wnc.addObserver_selector_name_object_(
            observer,
            'onActivation:',
            notification,
            None)
    for notification in (
        AppKit.NSWorkspaceSessionDidResignActiveNotification,
        AppKit.NSWorkspaceWillPowerOffNotification,
        AppKit.NSWorkspaceWillSleepNotification,
        AppKit.NSWorkspaceScreensDidSleepNotification,
    ):
        wnc.addObserver_selector_name_object_(
            observer,
            'onDeactivation:',
            notification,
            None)
    log_event("AgentStart", Activity.WORKING)
    try:
        AppHelper.runConsoleEventLoop()
    except KeyboardInterrupt:
        log_event("AgentStop", Activity.IDLE)
    except Exception as e:
        print(e)
        log_event("AgentException", Activity.IDLE)

if len(sys.argv) > 1:
    if sys.argv[1] == "agent":
        run_agent()
    else:
        print(f"Unknown command: {sys.argv[1]}")
else:
    write_menu()
