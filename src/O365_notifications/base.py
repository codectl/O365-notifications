import datetime
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from marshmallow import Schema, fields, post_load, pre_dump
from O365.utils import ApiComponent

from O365_notifications.constants import O365EventType, O365Namespace
from O365_notifications.utils import DeserializerMixin, build_url

__all__ = (
    "O365BaseNotification",
    "O365BaseNotificationsHandler",
    "O365BaseSubscription",
    "O365Notification",
    "O365NotificationHandler",
    "O365Subscriber",
)

logger = logging.getLogger(__name__)


@dataclass
class O365BaseNotification(DeserializerMixin, ABC):
    type: O365Namespace.O365NotificationType

    class BaseO365NotificationSchema(DeserializerMixin.DeserializerSchema):
        type = fields.Str(data_key="@odata.type")

        def __init__(self, **kwargs):
            self.namespace = kwargs.pop("namespace", None)
            super().__init__(**kwargs)

        @post_load
        def convert_types(self, data, **_):
            data["type"] = self.namespace.O365NotificationType(data["type"])
            return data

    schema = BaseO365NotificationSchema  # alias


@dataclass
class O365Notification(O365BaseNotification):
    id: str
    subscription_id: str
    subscription_expire: datetime
    sequence: int
    event: O365EventType

    @dataclass
    class O365ResourceData:
        type: O365Namespace.O365ResourceDataType
        url: str
        etag: str
        id: str

    class O365NotificationSchema(O365BaseNotification.schema):
        id = fields.Str(data_key="Id")
        subscription_id = fields.Str(data_key="SubscriptionId")
        subscription_expire = fields.DateTime(data_key="SubscriptionExpirationDateTime")
        sequence = fields.Int(data_key="SequenceNumber")
        event = fields.Str(data_key="ChangeType")
        resource = fields.Nested(
            Schema.from_dict(
                {
                    "type": fields.Str(data_key="@odata.type"),
                    "url": fields.Url(data_key="@odata.id"),
                    "etag": fields.Str(data_key="@odata.etag"),
                    "id": fields.Str(data_key="Id"),
                }
            ),
            data_key="ResourceData",
        )

        @post_load
        def convert_types(self, data, **_):
            ns = self.namespace
            data["type"] = ns.O365NotificationType.NOTIFICATION
            data["event"] = O365EventType(data["event"])
            data["resource"]["type"] = ns.O365ResourceDataType(data["resource"]["type"])
            data["resource"] = O365Notification.O365ResourceData(**data["resource"])
            return data

    resource: O365ResourceData
    schema = O365NotificationSchema  # alias


@dataclass
class O365BaseSubscription(DeserializerMixin, ABC):
    type: O365Namespace.O365SubscriptionType
    events: list[O365EventType]
    resource: ApiComponent
    resource_url: str = None
    id: str = None

    class BaseO365SubscriptionSchema(DeserializerMixin.DeserializerSchema):
        id = fields.Str(data_key="Id", load_only=True)
        type = fields.Str(data_key="@odata.type")
        resource_url = fields.Str(data_key="Resource")
        events = fields.Str(data_key="ChangeType")

        def __init__(self, **kwargs):
            self.resource = kwargs.pop("resource", None)
            self.namespace = kwargs.pop("namespace", None)
            super().__init__(**kwargs)

        @pre_dump
        def serialize(self, obj, **_):
            data = obj.__dict__
            data["type"] = data["type"].value
            data["events"] = ",".join(e.value for e in data["events"])
            data["resource_url"] = (build_url(data["resource"]),)
            return data

        @post_load
        def convert_types(self, data, **_):
            data["type"] = self.namespace.O365SubscriptionType(data["type"])
            data["events"] = [O365EventType(e) for e in data["events"].split(",")]
            data["resource"] = self.resource
            return data

    schema = BaseO365SubscriptionSchema  # alias

    def serialize(self, **kwargs):
        return self.schema(**kwargs).dump(self)


class O365Subscriber(ApiComponent, ABC):
    _endpoints = {"subscriptions": "/subscriptions"}
    subscription_cls = O365BaseSubscription

    def __init__(self, *, parent=None, con=None, **kwargs):
        protocol = kwargs.get("protocol", getattr(parent, "protocol", None))
        main_resource = kwargs.get(
            "main_resource", getattr(parent, "main_resource", None)
        )

        super().__init__(protocol=protocol, main_resource=main_resource)

        self.con = getattr(parent, "con", con)  # communication with the api provider
        self.namespace = O365Namespace.from_protocol(protocol=protocol)
        self.subscriptions = []

    def subscription_factory(self, **kwargs) -> O365BaseSubscription:
        return self.subscription_cls(**{**kwargs, "raw": kwargs})

    def subscribe(self, *, resource: ApiComponent, events: list[O365EventType]):
        """
        Subscription to a given resource.

        :param resource: the resource to subscribe to
        :param events: events type for the resource subscription
        """
        req = self.subscription_factory(resource=resource, events=events).serialize()

        url = self.build_url(self._endpoints.get("subscriptions"))
        response = self.con.post(url, req)
        raw = response.json()

        # register subscription
        subscription = self.subscription_cls.deserialize(
            data=raw, resource=resource, namespace=self.namespace
        )

        update = next((s for s in self.subscriptions if s.resource == resource), None)
        if update:
            update.id = subscription.id
            update.events = events
            update.raw = raw
        else:
            self.subscriptions.append(subscription)
        logger.debug(f"Subscribed to resource '{resource}' on events: '{events}'")

    def renew_subscriptions(self):
        names = ", ".join(f"'{s.resource}'" for s in self.subscriptions)
        logger.info(f"Renewing subscriptions for {names} ...")
        for sub in self.subscriptions:
            self.subscribe(resource=sub.resource, events=sub.events)
        logger.info("Subscriptions renewed.")


class O365BaseNotificationsHandler(ABC):
    @abstractmethod
    def process(self, notification: O365BaseNotification):
        pass


class O365NotificationHandler(O365BaseNotificationsHandler):
    def process(self, notification: O365BaseNotification):
        logger.debug(vars(notification))
