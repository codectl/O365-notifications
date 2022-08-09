import random
from datetime import datetime

import pytest
import pytest_cases
from O365 import Account, MSGraphProtocol, MSOffice365Protocol
from pytest_cases import fixture_ref

from O365_notifications.base import O365BaseNotificationsHandler, O365Notification
from O365_notifications.constants import O365EventType
from O365_notifications.streaming import (
    O365KeepAliveNotification,
    O365StreamingSubscriber,
)


@pytest.fixture(scope="class", params=[MSOffice365Protocol, MSGraphProtocol])
def account(backend, request):
    protocol = request.param(api_version="beta")
    return Account(
        credentials=("user", "pass"),
        tenant_id="foo",
        main_resource="foo@bar.com",
        auth_flow_type="credentials",
        protocol=protocol,
        token_backend=backend,
    )


@pytest.fixture
def inbox(account):
    return account.mailbox().inbox_folder()


@pytest.fixture(scope="class")
def subscriber(account):
    return O365StreamingSubscriber(parent=account)


@pytest_cases.fixture
@pytest_cases.parametrize("resource", [fixture_ref("inbox")])
@pytest_cases.parametrize("events", [[O365EventType.CREATED]])
def subscribe(resource, events, subscriber, requests_mock):
    base_url = f"{subscriber.protocol.service_url}{subscriber.main_resource}"
    sub_type = subscriber.namespace.O365SubscriptionType.STREAMING_SUBSCRIPTION
    random_id = str(random.randint(1000, 9999))
    response = {
        "@odata.context": f"{base_url}/...",
        "@odata.type": sub_type.value,
        "@odata.id": f"{base_url}/users/foo@bar.com/Subscriptions('{random_id}')",
        "Id": random_id,
        "Resource": f"{base_url}/me/mailfolders('inbox')/Messages",
        "ChangeType": ",".join(e.value for e in events),
    }
    requests_mock.register_uri("POST", f"{base_url}/subscriptions", json=response)
    subscriber.subscribe(resource=resource, events=events)
    return next(iter(subscriber.subscriptions))


class TestMailbox:
    @pytest_cases.parametrize("subscription", [fixture_ref("subscribe")])
    def test_subscription(self, subscription, subscriber):
        assert len(subscriber.subscriptions) == 1
        assert subscriber.subscriptions[0].events == [O365EventType.CREATED]

    @pytest_cases.parametrize("subscription", [fixture_ref("subscribe")])
    def test_renew_subscription(self, subscription, subscriber):
        subscriber.renew_subscriptions()
        assert len(subscriber.subscriptions) == 1
        assert subscriber.subscriptions[0].events == [O365EventType.CREATED]

    @pytest_cases.parametrize("subscription", [fixture_ref("subscribe")])
    def test_streaming_connection(self, subscription, subscriber, requests_mock):
        proto_url = subscriber.protocol.service_url
        base_url = f"{proto_url}{subscriber.main_resource}"
        ns = subscriber.namespace
        types = {
            "keep_alive": ns.O365NotificationType.KEEP_ALIVE_NOTIFICATION,
            "notif": ns.O365NotificationType.NOTIFICATION,
            "message": ns.O365ResourceDataType.MESSAGE
        }
        data = {
            "@odata.context": f"{proto_url}/metadata#Notifications",
            "value": [
                {
                    "@odata.type": types["keep_alive"].value,
                    "Status": "OK",
                },
                {
                    "@odata.type": types["notif"].value,
                    "Id": "null",
                    "SubscriptionId": subscription.id,
                    "SubscriptionExpirationDateTime": datetime.now().isoformat(),
                    "SequenceNumber": 1,
                    "ChangeType": O365EventType.CREATED.value,
                    "Resource": f"{base_url}/Messages('XYZ')",
                    "ResourceData": {
                        "@odata.type": types["message"].value,
                        "@odata.id": f"{base_url}/Messages('XYZ')",
                        "@odata.etag": "XYZ000",
                        "Id": "ABC",
                    },
                },
                {
                    "@odata.type": types["keep_alive"].value,
                    "Status": "OK",
                },
            ],
        }
        requests_mock.register_uri("POST", f"{base_url}/GetNotifications", json=data)

        class DummyHandler(O365BaseNotificationsHandler):
            def __init__(self):
                self.notifications = []

            def process(self, notification):
                self.notifications.append(notification)

        handler = DummyHandler()
        subscriber.create_event_channel(notification_handler=handler)
        assert len(handler.notifications) == 3
        assert type(handler.notifications[0]) == O365KeepAliveNotification
        assert type(handler.notifications[1]) == O365Notification
        assert type(handler.notifications[2]) == O365KeepAliveNotification
        assert handler.notifications[1].type == types["notif"]
        assert handler.notifications[1].sequence == 1
        assert handler.notifications[1].event == O365EventType.CREATED
        assert handler.notifications[1].resource.type == types["message"]
