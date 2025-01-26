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
    project: str = ""

class Span(NamedTuple):
    start: datetime.datetime
    end: datetime.datetime
    project: str = ""

    def duration(self) -> datetime.timedelta:
        return self.end - self.start
    
    def __str__(self) -> str:
        return f"{self.start:%H:%M}-{self.end:%H:%M} ({self.duration() / ONE_HOUR:.2f}){' ' if self.project else ''}{self.project}"

def get_log_filename(day: Optional[datetime.date]=None) -> str:
    if day is None:
        day = datetime.date.today()
    return os.path.join(LOGDIR, f"{day}.log")
    
def log_event(name: str, activity: Activity, project: str="", now: Optional[datetime.datetime] = None):
    os.makedirs(LOGDIR, exist_ok=True)
    if not now:
        now = datetime.datetime.now()
    filename = get_log_filename(now.date())
    with open(filename, mode="a") as log:
        print(now, name, activity.name, project, sep="\t", file=log)

def parse_log_line(line: str) -> Event:
    timestamp, name, activity, *rest = line.strip().split("\t")
    project = rest[0] if rest else ""
    return Event(datetime.datetime.fromisoformat(timestamp), name, Activity[activity], project)

def parse_log(log: TextIO) -> Sequence[Event]:
    lines = log.readlines()
    return [parse_log_line(line) for line in lines]

def load_log(day: Optional[datetime.date]=None) -> Sequence[Event]:
    filename = get_log_filename(day)
    try:
        with open(filename) as log:
            return parse_log(log)
    except FileNotFoundError:
        return []

@dataclass
class Project:
    name: str
    symbol: str

def load_projects()->List[Project]:
    try:
        with open(os.path.join(LOGDIR, "projects.txt"), "rt") as f:
            lines = f.readlines()
            projects = [Project(*l.split()) for l in lines]
            return projects
    except FileNotFoundError:
        return []

def get_work_spans(
        events: Sequence[Event],
        now: datetime.datetime=datetime.datetime.now()) -> Iterable[Span]:
    working = False
    start = datetime.datetime.now()
    project = ""
    for e in events:
        if e.activity is Activity.WORKING:
            if not working:
                working = True
                start = e.timestamp
            if e.project and e.project != project:
                if e.timestamp > start:
                    yield Span(start, e.timestamp, project)
                    start = e.timestamp
                project = e.project
        else:
            if working:
                working = False
                yield Span (start, e.timestamp, project)
    if working:
        yield Span(start, now, project)

def filter_short_breaks(spans: Iterable[Span]) -> Iterable[Span]:
    it = iter(spans)
    try:
        current = next(it)
    except StopIteration:
        return ()
        
    for nxt in it:
        if nxt.start - current.end < SHORT_BREAK and nxt.project == current.project:
            current = Span(current.start, nxt.end, current.project)
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
    
    if spans:    
        _start, end, _project = spans[-1]
        if end.hour >= 22:
            yield Message(Level.ERROR, "Stop working now, it's after 10pm!")
        elif end.hour >= 21:
            yield Message(Level.WARNING, "Time to stop working?")


class DayResults:
    spans: List[Span] = []
    total_hours: float = 0.0
    messages: List[Message] = []
    level: Level= Level.ERROR

    def __init__(self, events: Sequence[Event]):
        if events:
            try:
                self.spans = filter_spans(get_work_spans(events))
                self.total_hours = get_cumulative_work(self.spans)
                self.messages = list(get_messages(self.spans, self.total_hours))
                self.level = max([m.level for m in self.messages], default=Level.INFO)
            except Exception as e:
                self.messages = [Message(Level.ERROR, str(e))]
        else:
            self.messages= [Message(Level.ERROR, "No log file")]
             

def write_menu():
    results = DayResults(load_log())
    projects = load_projects()

    project_symbol = "questionmark.circle"
    last_project_name = ""
    todays_projects = [s.project for s in results.spans if s.project]
    if todays_projects:
        last_project_name = todays_projects[-1]
        project_symbol = [p.symbol for p in projects if p.name == last_project_name][0]
    print(results.level.ansi_format(f"{results.total_hours:.2f} {BARS[min(int(results.total_hours), 8)]}") + f"|ansi=True sfimage={project_symbol}")
    print("---")
    for message in results.messages:
        print(f"{message.level.ansi_format(message.text)}|ansi=True")
    for s in results.spans:
        print(s)
    print(f"Report|bash={sys.argv[0]} param0=report")
    print("---")
    for p in projects:
        print(f"{p.name}|checked={p.name == last_project_name} bash={sys.argv[0]} param0=project param1={p.name} terminal=False refresh=True sfimage={p.symbol}")
        print(f"{p.name} (back)|bash={sys.argv[0]} param0=project-back param1={p.name} terminal=False refresh=True sfimage={p.symbol} alternate=True")

def write_report():
    today = datetime.date.today()
    a_week_ago = today - datetime.timedelta(days=7)
    day = datetime.date(a_week_ago.year, a_week_ago.month, 1)
    while day < today:
        if day.isoweekday() < 6:
            results = DayResults(load_log(day=day))
            print()
            print(f"{ANSI_BOLD}{day:%d.%m.%Y - %A}: {results.total_hours:.2f}{ANSI_RESET}")
            for i, s in enumerate(results.spans):
                print(f"{ANSI_SHADES[i % 2]}{s}{ANSI_RESET}")
            for message in results.messages:
                print(message.level.ansi_format(message.text))
        day += datetime.timedelta(days=1)

def log_project(project: str):
    log_event("project", Activity.WORKING, project)

def log_project_back(project: str):
    events = load_log()
    timestamp = events[0].timestamp if events else None
    log_event("project-back", Activity.WORKING, project, now=timestamp)


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "report":
            write_report()
        elif sys.argv[1] == "project":
            log_project(sys.argv[2])
        elif sys.argv[1] == "project-back":
            log_project_back(sys.argv[2])
        else:
            print(f"Unknown command: {sys.argv[1]}")
    else:
        write_menu()

if __name__ == "__main__":
    main()
