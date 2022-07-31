import abc
import dataclasses
import logging
from enum import Enum

from O365.utils import ApiComponent

from O365_notifications.utils import resolve_namespace

__all__ = (
    "O365_BASE",
    "O365Notification",
    "O365Subscriber",
    "O365NotificationsHandler",
)

logger = logging.getLogger(__name__)

# base namespace for O365 resources
O365_BASE = "#Microsoft.OutlookServices"


class O365Notification(ApiComponent):
    class Type(Enum):
        O365_NOTIFICATION = f"{O365_BASE}.Notification"
        O365_STREAMING_SUBSCRIPTION = f"{O365_BASE}.StreamingSubscription"
        O365_KEEP_ALIVE_NOTIFICATION = f"{O365_BASE}.KeepAliveNotification"

    class ResourceType(Enum):
        O365_MESSAGE = f"{O365_BASE}.Message"
        O365_EVENT = f"{O365_BASE}.Event"

    class Event(Enum):
        ACKNOWLEDGEMENT = "Acknowledgment"
        CREATED = "Created"
        DELETED = "Deleted"
        MISSED = "Missed"
        UPDATED = "Updated"

    def __init__(self, parent=None, **kwargs):
        self.parent = parent
        protocol = parent.protocol

        super().__init__(protocol=protocol, **kwargs)

        self.type = kwargs.get("@odata.type")
        self.subscription_id = kwargs.get(self._cc("id"))
        self.resource = kwargs.get(self._cc("resource"))
        self.event = kwargs.get(self._cc("changeType"))
        if kwargs.get(self._cc("resourceData")):
            self.resource_data = dict(**kwargs.get(self._cc("resourceData")))


class O365Subscriber(ApiComponent):
    _namespace = f"{O365_BASE}.Subscription"

    @dataclasses.dataclass
    class Subscription:
        id: str
        resource: ApiComponent
        events: list[O365Notification.Event]
        raw: dict

    def __init__(self, *, parent=None, con=None, **kwargs):
        # con required if communication with the api provider is needed
        self.con = getattr(parent, "con", con)
        self.parent = parent if issubclass(type(parent), self.__class__) else None

        protocol = kwargs.get("protocol", getattr(parent, "protocol", None))
        main_resource = kwargs.get(
            "main_resource", getattr(parent, "main_resource", None)
        )

        super().__init__(protocol=protocol, main_resource=main_resource)

        self.name = kwargs.get("name", getattr(parent, "name", None))
        self.subscriptions = []

    @property
    def namespace(self):
        raise self._namespace

    def subscribe(self, *, resource: ApiComponent, events: list[O365Notification.Event]):
        """
        Subscription to a given resource.

        :param resource: the resource to subscribe to
        :param events: events type for the resource subscription
        """
        subscription = next(s for s in self.subscriptions if s.resource == resource)
        if subscription:
            events = [ev for ev in events if ev not in subscription.events]
            if not events:
                raise ValueError("subscription for given resource already exists")

        normalize = ",".join(ev.value for ev in events)
        data = {
            "@odata.type": self.namespace,
            self._cc("resource"): resolve_namespace(resource),
            self._cc("changeType"): normalize,
        }

        url = self.build_url(self._endpoints.get("subscriptions"))
        response = self.con.post(url, data)
        raw = response.json()

        # register subscription
        if subscription:
            subscription.id = raw["Id"]
            subscription.events.append(events)
            subscription.raw = raw
        else:
            subscription = self.Subscription(
                raw["Id"],
                resource=resource,
                events=events,
                raw=raw
            )
            self.subscriptions.append(subscription)
        logger.debug(f"Subscribed to resource '{resource}' on events: '{events}'")

    def renew_subscriptions(self):
        names = ", ".join(f"'{s.resource}'" for s in self.subscriptions)
        logger.info(f"Renewing subscriptions for {names} ...")
        map(lambda s: self.subscribe(resource=s.resource, events=s.events), self.subscriptions)
        logger.info(f"Subscriptions renewed.")


class O365NotificationsHandler:
    @abc.abstractmethod
    def process(self, notification):
        logger.debug(vars(notification))
