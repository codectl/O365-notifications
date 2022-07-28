import logging
from abc import abstractmethod
from enum import Enum

from O365.utils import ApiComponent

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

    class ChangeType(Enum):
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
        self.change_type = kwargs.get(self._cc("changeType"))
        if kwargs.get(self._cc("resourceData")):
            self.resource_data = dict(**kwargs.get(self._cc("resourceData")))


class O365Notifications(ApiComponent):
    def __init__(self, *, parent=None, con=None, **kwargs):
        # con required if communication with the api provider is needed
        self.con = getattr(parent, "con", con)
        self.parent = parent if issubclass(type(parent), O365Notifications) else None

        protocol = kwargs.get("protocol") or getattr(parent, "protocol", None)
        main_resource = kwargs.get("main_resource") or getattr(
            parent, "main_resource", None
        )

        super().__init__(protocol=protocol, main_resource=main_resource)

        self.name = kwargs.get("name", getattr(parent, "name", None))
        self.change_type = kwargs.get(
            "change_type", getattr(parent, "change_type", None)
        )
        self.subscribed_resources = []

    @property
    def request_type(self):
        raise NotImplementedError("Subclasses must implement this method.")

    def subscribe(self, *, resource):
        raise NotImplementedError("Subclasses must implement this method.")

    def renew_subscriptions(self):
        logger.info(f"Renew subscription for {str(self.subscribed_resources)}")
        resources = self.subscribed_resources
        subscriptions = [self.subscribe(resource=resource) for resource in resources]
        logger.info(f"Renewed subscriptions are {str(subscriptions)}")
        return subscriptions


class O365NotificationsHandler:
    @abstractmethod
    def process(self, notification):
        logger.debug(vars(notification))
