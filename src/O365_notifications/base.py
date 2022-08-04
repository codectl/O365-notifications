import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from O365.utils import ApiComponent
from marshmallow import fields, post_load, pre_dump

from O365_notifications.utils import build_url, DeserializerSchema, Schema
from O365_notifications.constants import O365EventType, O365Namespace

__all__ = (
    "O365Notification",
    "O365Subscription",
    "O365Subscriber",
    "O365NotificationsHandler",
)

logger = logging.getLogger(__name__)


@dataclass
class O365Notification(ABC):
    type: O365Namespace.O365NotificationType
    raw: dict

    class BaseO365NotificationSchema(DeserializerSchema):
        type = fields.String(data_key="@odata.type")


@dataclass
class O365Subscription(ABC):
    type: O365Namespace.O365SubscriptionType
    resource: ApiComponent
    events: list[O365EventType]
    id: str = None
    raw: dict = None

    class BaseO365SubscriptionSchema(Schema):
        id = fields.String(data_key="Id", load_only=True)
        type = fields.String(data_key="@odata.type")
        resource = fields.String(data_key="Resource", dump_only=True)
        events = fields.String(data_key="ChangeType")

        @pre_dump
        def serialize(self, data):
            data["type"] = data["type"].value
            data["resource"] = build_url(data["resource"])
            data["events"] = ",".join(e.value for e in data["events"])
            return data

        @post_load
        def deserialize(self, data):
            data["type"] = O365Namespace.O365SubscriptionType(data["type"])
            data["events"] = [O365EventType(e) for e in data["events"].split(",")]
            return super(**data)

    schema = BaseO365SubscriptionSchema  # alias

    @classmethod
    def deserialize(cls, data: dict):
        return cls.schema().load(data)

    def serialize(self):
        return self.schema().dump(self)


class O365Subscriber(ApiComponent, ABC):
    _endpoints = {"subscriptions": "/subscriptions"}

    def __init__(self, *, parent=None, con=None, **kwargs):
        protocol = kwargs.get("protocol", getattr(parent, "protocol", None))
        main_resource = kwargs.get(
            "main_resource", getattr(parent, "main_resource", None)
        )

        super().__init__(protocol=protocol, main_resource=main_resource)

        self.con = getattr(parent, "con", con)  # communication with the api provider
        self.parent = parent if issubclass(type(parent), self.__class__) else None
        self.namespace = O365Namespace(protocol=protocol)
        self.subscriptions = []

    @abstractmethod
    def subscription_constructor(self, **kwargs) -> O365Subscription:
        pass

    def subscribe(self, *, resource: ApiComponent, events: list[O365EventType]):
        """
        Subscription to a given resource.

        :param resource: the resource to subscribe to
        :param events: events type for the resource subscription
        """
        update = next(s for s in self.subscriptions if s.resource == resource)
        if update:
            events = [ev for ev in events if ev not in update.events]
            if not events:
                raise ValueError("subscription for given resource already exists")

        data = self.subscription_constructor(
            resource=resource,
            events=events
        ).serialize()

        url = self.build_url(self._endpoints.get("subscriptions"))
        response = self.con.post(url, data)
        raw = response.json()

        # register subscription
        subscription = O365Subscription.deserialize({"resource": resource, **raw})
        if update:
            update.id = subscription.id
            update.events.append(events)
            update.raw = raw
        else:
            self.subscriptions.append(subscription)
        logger.debug(f"Subscribed to resource '{resource}' on events: '{events}'")

    def renew_subscriptions(self):
        names = ", ".join(f"'{s.resource}'" for s in self.subscriptions)
        logger.info(f"Renewing subscriptions for {names} ...")
        map(lambda s: self.subscribe(resource=s.resource, events=s.events), self.subscriptions)
        logger.info(f"Subscriptions renewed.")


class O365NotificationsHandler:
    @abstractmethod
    def process(self, notification):
        logger.debug(vars(notification))
