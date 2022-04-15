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
from typing import Iterable, List, NamedTuple, Optional, Sequence, TextIO

BARS = " ▁▂▃▄▅▆▇█"
LOGDIR = os.path.expanduser("~/.time-tracker")

ANSI_RESET="\033[0m"
ANSI_RED="\033[31m"
ANSI_ORANGE="\033[33m"
ANSI_GREEN="\033[32m"
ANSI_BOLD="\033[1m"
ANSI_SHADE_EVEN="\033[48;5;255m"
ANSI_SHADE_ODD=""
ANSI_SHADES = [ANSI_SHADE_EVEN, ANSI_SHADE_ODD]

class Activity (enum.Enum):
    IDLE = 0
    WORKING = 1

ONE_HOUR = datetime.timedelta(hours=1)
SHORT_BREAK = datetime.timedelta(minutes=3)
SHORT_WORK = datetime.timedelta(minutes=1)

class Event(NamedTuple):
    timestamp: datetime.datetime
    name: str
    activity: Activity

class Span(NamedTuple):
    start: datetime.datetime
    end: datetime.datetime

    def duration(self) -> datetime.timedelta:
        return self.end - self.start
    
    def __str__(self) -> str:
        return f"{self.start:%H:%M}-{self.end:%H:%M} ({self.duration() / ONE_HOUR:.2f})"

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
    timestamp, name, *rest = line.strip().split("\t")
    if rest:
        activity = Activity[rest[0]]
    elif name == "ScreenUnlock":
        activity = Activity.WORKING
    else:
        activity = Activity.IDLE
    return Event(datetime.datetime.fromisoformat(timestamp), name, activity)

def parse_log(log: TextIO):
    lines = log.readlines()
    return [parse_log_line(line) for line in lines]

def load_log(day: Optional[datetime.date]=None) -> Sequence[Event]:
    filename = get_log_filename(day)
    with open(filename) as log:
        return parse_log(log)

def get_work_spans(
        events: Sequence[Event],
        now: datetime.datetime=datetime.datetime.now()) -> Iterable[Span]:
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
                yield Span (start, d)
    if working:
        yield Span(start, now)

def filter_short_breaks(spans: Iterable[Span]) -> Iterable[Span]:
    it = iter(spans)
    try:
        current = next(it)
    except StopIteration:
        return ()
        
    for nxt in it:
        if nxt.start - current.end < SHORT_BREAK:
            current = Span(current.start, nxt.end)
        else:
            yield current
            current = nxt
    yield current

def filter_short_work(spans: Iterable[Span]) -> Iterable[Span]:
    return (s for s in spans if s.duration() > SHORT_WORK)

def filter_spans(spans: Iterable[Span]) -> List[Span]:
    return list(filter_short_work(filter_short_breaks(spans)))

def get_cumulative_work(spans: Iterable[Span]) -> float:
    #TODO adjust durations for required breaks
    total = sum((s.duration() for s in spans), datetime.timedelta())
    return total / ONE_HOUR

class Level(enum.IntEnum):
    INFO = 0
    PRAISE = 1
    WARNING = 2
    ERROR = 3
    
    def ansi_color_code(self) -> str:
        return [ANSI_RESET, ANSI_GREEN, ANSI_ORANGE, ANSI_RED][self.value]
    
    def ansi_format(self, text: str) -> str:
        return f"{self.ansi_color_code()}{text}{ANSI_RESET}"

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

class DayResults:
    spans: List[Span] = []
    total_hours: float = 0.0
    messages: List[Message] = []
    level: Level= Level.ERROR

    def __init__(self, day: Optional[datetime.date]=None) -> None:

        try:
            events = load_log(day)
            self.spans = filter_spans(get_work_spans(events))
            self.total_hours = get_cumulative_work(self.spans)
            self.messages = list(get_messages(self.spans, self.total_hours))
            self.level = max([m.level for m in self.messages], default=Level.INFO) 
        except FileNotFoundError:
            self.messages = [Message(Level.ERROR, "No log file")]
        except Exception as e:
            self.messages = [Message(Level.ERROR, str(e))]
             

def write_menu():
    results = DayResults()

    print(results.level.ansi_format(f"{results.total_hours:.2f} {BARS[min(int(results.total_hours), 8)]}") + "|ansi=True")
    print("---")
    for message in results.messages:
        print(f"{message.level.ansi_format(message.text)}|ansi=True")
    for s in results.spans:
        print(s)
    print(f"Report|bash={sys.argv[0]} param0=report")

def write_report():
    today = datetime.date.today()
    a_week_ago = today - datetime.timedelta(days=7)
    day = datetime.date(a_week_ago.year, a_week_ago.month, 1)
    while day < today:
        if day.isoweekday() < 6:
            results = DayResults(day=day)
            print()
            print(f"{ANSI_BOLD}{day:%d.%m.%Y - %A}: {results.total_hours:.2f}{ANSI_RESET}")
            for i, s in enumerate(results.spans):
                print(f"{ANSI_SHADES[i % 2]}{s}{ANSI_RESET}")
            for message in results.messages:
                print(message.level.ansi_format(message.text))
        day += datetime.timedelta(days=1)
    
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

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "agent":
            run_agent()
        elif sys.argv[1] == "report":
            write_report()
        else:
            print(f"Unknown command: {sys.argv[1]}")
    else:
        write_menu()

if __name__ == "__main__":
    main()
