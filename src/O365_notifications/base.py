import logging
from abc import abstractmethod
from enum import Enum

from O365.utils import ApiComponent

logger = logging.getLogger(__name__)


class O365Notification(ApiComponent):
    class Type(Enum):
        O365_NOTIFICATION = "#Microsoft.OutlookServices.Notification"
        O365_STREAMING_SUBSCRIPTION = "#Microsoft.OutlookServices.StreamingSubscription"
        O365_KEEP_ALIVE_NOTIFICATION = (
            "#Microsoft.OutlookServices.KeepAliveNotification"
        )

    class ResourceType(Enum):
        O365_MESSAGE = "#Microsoft.OutlookServices.Message"
        O365_EVENT = "#Microsoft.OutlookServices.Event"

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
    """O365 Notifications"""

    def __init__(self, *, parent=None, con=None, **kwargs):
        # connection is only needed if you want to communicate with the api provider
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
        """Renew subscriptions"""
        logger.info(f"Renew subscription for {str(self.subscribed_resources)}")
        subscriptions = [
            self.subscribe(resource=resource) for resource in self.subscribed_resources
        ]
        logger.info(f"Renewed subscriptions are {str(subscriptions)}")
        return subscriptions


class O365NotificationsHandler:
    """Handler meant to deal with incoming notifications"""

    @abstractmethod
    def process(self, notification):
        """
        Process a notification.
        Override as this function simply prints the given notification.
        """
        logger.debug(vars(notification))
