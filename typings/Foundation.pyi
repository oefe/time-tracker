from enum import Enum
from typing import Any, Optional


class NSObject:
    @classmethod
    def new(cls) -> Any: ...

class NSNotificationCenter (NSObject):
    def addObserver_selector_name_object_(self, observer: NSObject, selector: str, name: str, object: Optional[NSObject]) -> None: ...

class NSNotificationSuspensionBehavior(Enum):
    NSNotificationSuspensionBehaviorDeliverImmediately = 4

NSNotificationSuspensionBehaviorDeliverImmediately = NSNotificationSuspensionBehavior.NSNotificationSuspensionBehaviorDeliverImmediately

class NSDistributedNotificationCenter (NSNotificationCenter):
    @classmethod
    def defaultCenter(cls) -> NSDistributedNotificationCenter: ...
    def addObserver_selector_name_object_suspensionBehavior_(self, observer: NSObject, selector: str, name: str, object: Optional[NSObject], suspensionBehavior: NSNotificationSuspensionBehavior) -> None: ...

class NSNotification(NSObject):
    def name(self) -> str: ...