#!/usr/bin/env python
# <bitbar.title>Time Tracker</bitbar.title>
# <bitbar.version>v0.1</bitbar.version>
# <bitbar.author>Martina Oefelein</bitbar.author>
# <bitbar.author.github>oefe</bitbar.author.github>
# <bitbar.desc>Utilities to track my working hours</bitbar.desc>
# <bitbar.image></bitbar.image>
# <bitbar.dependencies>python</bitbar.dependencies>
# <bitbar.abouturl>http://oefelein.de/</bitbar.abouturl>

import datetime
import enum
import os
import os.path
import sys

BARS = " ▁▂▃▄▅▆▇█"
LOGDIR = os.path.expanduser("~/.time-tracker")

Activity = enum.Enum("Activity", "IDLE WORKING")

def get_log_filename(day=None):
    if day is None:
        day = datetime.date.today()
    return os.path.join(LOGDIR, f"{day}.log")
    
def log_event(name: str, activity: Activity):
    os.makedirs(LOGDIR, exist_ok=True)
    now = datetime.datetime.now()
    filename = get_log_filename(now.date())
    with open(filename, mode="a") as log:
        print(now, name, activity.name, sep="\t", file=log)

def parse_log_line(line: str):
    timestamp, event, *rest = line.strip().split("\t")
    if rest:
        activity = Activity[rest[0]]
    elif event == "ScreenUnlock":
        activity = Activity.WORKING
    else:
        activity = Activity.IDLE
    return datetime.datetime.fromisoformat(timestamp), event, activity

def load_log(day=None):
    filename = get_log_filename(day)
    with open(filename) as log:
        lines = log.readlines()
    return [parse_log_line(line) for line in lines]

def get_work_spans(events):
    spans = []
    working = False
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

def get_cumulative_work_today(spans):
    durations = [end - start for (start, end) in spans]
    #TODO adjust durations for required breaks
    return sum(durations, datetime.timedelta())

def format_timedelta(td):
    hours, rest = divmod(td, datetime.timedelta(hours=1))
    minutes = rest // datetime.timedelta(minutes=1)
    return f"{hours}:{minutes:02}"

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
    cumulative_work_today = get_cumulative_work_today(spans)
    hours = cumulative_work_today / datetime.timedelta(hours=1)
    print(f"{format_timedelta(cumulative_work_today)} {BARS[min(int(hours), 8)]}")
    print("---")
    for (start, end) in spans:
        print(f"{start:%H:%M}-{end:%H:%M} ({format_timedelta(end-start)})")

def run_agent():
    import AppKit
    import Foundation
    from PyObjCTools import AppHelper 
    class Observer(Foundation.NSObject):
        def onActivation_(self, notification):
            log_event(notification.name(), Activity.WORKING)    

        def onDeactivation_(self, notification):
            log_event(notification.name(), Activity.IDLE)    

    nc = Foundation.NSDistributedNotificationCenter.defaultCenter()
    observer = Observer.new()
    nc.addObserver_selector_name_object_suspensionBehavior_(
        observer,
        'onActivation:',
        'com.apple.screenIsLocked',
        None,
        Foundation.NSNotificationSuspensionBehaviorDeliverImmediately)
    nc.addObserver_selector_name_object_suspensionBehavior_(
        observer,
        'onDeactivation:',
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
