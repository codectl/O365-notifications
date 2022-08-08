import random

import pytest
import pytest_cases
from O365 import Account, MSGraphProtocol, MSOffice365Protocol
from pytest_cases import fixture_ref

from O365_notifications.constants import O365EventType
from O365_notifications.streaming import O365StreamingSubscriber


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
        keep_alive_t = subscriber.namespace.O365NotificationType.KEEP_ALIVE_NOTIFICATION
        notif_t = subscriber.namespace.O365NotificationType.NOTIFICATION
        message_t = subscriber.namespace.O365ResourceDataType.MESSAGE
        data = {
            "@odata.context": f"{proto_url}/metadata#Notifications",
            "value": [
                {
                    "@odata.type": keep_alive_t.value,
                    "Status": "OK",
                },
                {
                    "@odata.type": notif_t.value,
                    "Id": "null",
                    "SubscriptionId": subscription.id,
                    "SubscriptionExpirationDateTime": "2016-09-09T18:36:42.3454926Z",
                    "SequenceNumber": 9,
                    "ChangeType": O365EventType.CREATED.value,
                    "Resource": f"{base_url}/Messages('XYZ')",
                    "ResourceData": {
                        "@odata.type": message_t.value,
                        "@odata.id": f"{base_url}/Messages('XYZ')",
                        "@odata.etag": "XYZ000",
                        "Id": "ABC",
                    },
                },
            ],
        }
        requests_mock.register_uri("POST", f"{base_url}/GetNotifications", json=data)
        subscriber.create_event_channel()
        assert len(subscriber.subscriptions) == 1
