import O365
import pytest

from O365_notifications.constants import O365EventType
from O365_notifications.streaming import O365StreamingSubscriber


@pytest.fixture(scope="class")
def account(backend):
    protocol = O365.MSOffice365Protocol(api_version="beta")
    return O365.Account(
        credentials=("user", "pass"),
        tenant_id="foo",
        main_resource="foo@bar.com",
        auth_flow_type="credentials",
        protocol=protocol,
        token_backend=backend,
    )


@pytest.fixture(scope="class")
def folder(account):
    return account.mailbox().inbox_folder()


@pytest.fixture(scope="class")
def subscriber(account, folder):
    return O365StreamingSubscriber(parent=account)


@pytest.fixture(scope="class")
def outlook_subscription(account):
    base_url = "https://outlook.office.com/api/beta/"
    return {
        "@odata.context": f"{base_url}/...",
        "@odata.type": "#Microsoft.OutlookServices.StreamingSubscription",
        "@odata.id": f"{base_url}/users/foo@bar.com/Subscriptions('RUM4OEJFNUIQUQ4MQ')",
        "Id": "RUM4OEJFNUIQUQ4MQ",
        "Resource": f"{base_url}/me/mailfolders('inbox')/Messages",
        "ChangeType": "Created",
    }


class TestMailbox:
    def test_subscribe(self, subscriber, folder, outlook_subscription, requests_mock):
        response = outlook_subscription
        base_url = f"{subscriber.protocol.service_url}{subscriber.main_resource}"
        requests_mock.register_uri("POST", f"{base_url}/subscriptions", json=response)
        subscriber.subscribe(resource=folder, events=[O365EventType.CREATED])
        sub_type = subscriber.namespace.O365SubscriptionType.STREAMING_SUBSCRIPTION
        assert len(subscriber.subscriptions) == 1
        assert subscriber.subscriptions[0].type == sub_type
        assert subscriber.subscriptions[0].id == "RUM4OEJFNUIQUQ4MQ"
        assert subscriber.subscriptions[0].events == [O365EventType.CREATED]
        assert subscriber.subscriptions[0].raw == response
