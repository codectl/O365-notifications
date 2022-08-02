from enum import Enum

from O365 import Protocol

__all__ = ("O365Namespace", "O365EventType")


class O365Namespace:
    class O365Protocol(Enum):
        MSGraphProtocol = "#Microsoft.Graph"
        MSOffice365Protocol = "#Microsoft.OutlookServices"

    class O365SubscriptionType(Enum):
        PUSH_SUBSCRIPTION = "{base}.PushSubscription"
        STREAMING_SUBSCRIPTION = "{base}.StreamingSubscription"

    class O365NotificationType(Enum, O365SubscriptionType):
        NOTIFICATION = "{base}.Notification"
        KEEP_ALIVE_NOTIFICATION = "{base}.KeepAliveNotification"

    class O365ResourceDataType(Enum):
        CALENDAR = "{base}.Calendar"
        EVENT = "{base}.Event"
        MESSAGE = "{base}.Message"

    def __init__(self, protocol: Protocol):
        base = self.O365Protocol[protocol.__class__.__name__].value
        attrs = (getattr(self, attr) for attr in dir(self))
        enums = (a for a in attrs if isinstance(a, type) and issubclass(a, Enum))
        for enum in enums:
            kv = {e.name: e.value.format(base=base) for e in enum}
            setattr(self, enum.__name__, Enum(enum.__name__, kv))


class O365EventType(Enum):
    ACKNOWLEDGEMENT = "Acknowledgment"
    CREATED = "Created"
    DELETED = "Deleted"
    MISSED = "Missed"
    UPDATED = "Updated"
