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


class TestMailbox:
    def test_subscribe(self, subscriber, folder, requests_mock):
        proto_url = "https://outlook.office.com/api/beta/"
        response = {
            "@odata.context": f"{proto_url}/...",
            "@odata.type": "#Microsoft.OutlookServices.StreamingSubscription",
            "@odata.id": f"{proto_url}/users/foo@bar.com/Subscriptions('xyz')",
            "Id": "xyz",
            "Resource": f"{proto_url}/me/mailfolders('inbox')/Messages",
            "ChangeType": "Created",
        }
        req_url = f"{subscriber.protocol.service_url}{subscriber.main_resource}"
        requests_mock.register_uri("POST", f"{req_url}/subscriptions", json=response)
        subscriber.subscribe(resource=folder, events=[O365EventType.CREATED])
        sub_type = subscriber.namespace.O365SubscriptionType.STREAMING_SUBSCRIPTION
        assert len(subscriber.subscriptions) == 1
        assert subscriber.subscriptions[0].type == sub_type
        assert subscriber.subscriptions[0].id == "xyz"
        assert subscriber.subscriptions[0].events == [O365EventType.CREATED]
        assert subscriber.subscriptions[0].raw == response
