import Foundation
import Foundation

class NSWorkspace(Foundation.NSObject):
    @classmethod
    def sharedWorkspace(cls) -> NSWorkspace: ...

    def notificationCenter(self) -> Foundation.NSNotificationCenter: ...

NSWorkspaceSessionDidBecomeActiveNotification: str
NSWorkspaceDidWakeNotification: str
NSWorkspaceScreensDidWakeNotification: str        
NSWorkspaceSessionDidResignActiveNotification: str
NSWorkspaceWillPowerOffNotification: str
NSWorkspaceWillSleepNotification: str
NSWorkspaceScreensDidSleepNotification: str