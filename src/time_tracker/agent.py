import AppKit
import Foundation
from PyObjCTools import AppHelper

from time_tracker import Activity, log_event


class Observer(Foundation.NSObject):
    def onActivation_(self, notification: Foundation.NSNotification):
        log_event(notification.name(), Activity.WORKING)

    def onDeactivation_(self, notification: Foundation.NSNotification):
        log_event(notification.name(), Activity.IDLE)


def main() -> None:
    nc = Foundation.NSDistributedNotificationCenter.defaultCenter()
    observer = Observer.new()
    nc.addObserver_selector_name_object_suspensionBehavior_(
        observer,
        "onDeactivation:",
        "com.apple.screenIsLocked",
        None,
        Foundation.NSNotificationSuspensionBehaviorDeliverImmediately,
    )
    nc.addObserver_selector_name_object_suspensionBehavior_(
        observer,
        "onActivation:",
        "com.apple.screenIsUnlocked",
        None,
        Foundation.NSNotificationSuspensionBehaviorDeliverImmediately,
    )
    wnc = AppKit.NSWorkspace.sharedWorkspace().notificationCenter()
    for notification in (
        AppKit.NSWorkspaceSessionDidBecomeActiveNotification,
        AppKit.NSWorkspaceDidWakeNotification,
        AppKit.NSWorkspaceScreensDidWakeNotification,
    ):
        wnc.addObserver_selector_name_object_(
            observer, "onActivation:", notification, None
        )
    for notification in (
        AppKit.NSWorkspaceSessionDidResignActiveNotification,
        AppKit.NSWorkspaceWillPowerOffNotification,
        AppKit.NSWorkspaceWillSleepNotification,
        AppKit.NSWorkspaceScreensDidSleepNotification,
    ):
        wnc.addObserver_selector_name_object_(
            observer, "onDeactivation:", notification, None
        )
    log_event("AgentStart", Activity.WORKING)
    try:
        AppHelper.runConsoleEventLoop()
    except KeyboardInterrupt:
        log_event("AgentStop", Activity.IDLE)
    except Exception as e:
        print(e)
        log_event("AgentException", Activity.IDLE)


if __name__ == "__main__":
    main()
