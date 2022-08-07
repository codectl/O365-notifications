import pytest
from O365 import Account, MSGraphProtocol, MSOffice365Protocol

from O365_notifications.constants import O365EventType
from O365_notifications.streaming import O365StreamingSubscriber


@pytest.fixture(scope="class", params=(MSOffice365Protocol, MSGraphProtocol))
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


@pytest.fixture(scope="class")
def folder(account):
    return account.mailbox().inbox_folder()


@pytest.fixture(scope="class")
def subscriber(account, folder):
    return O365StreamingSubscriber(parent=account)


class TestMailbox:
    def test_subscription(self, subscriber, folder, requests_mock):
        proto_url = f"{subscriber.protocol.service_url}{subscriber.main_resource}"
        sub_type = subscriber.namespace.O365SubscriptionType.STREAMING_SUBSCRIPTION
        response = {
            "@odata.context": f"{proto_url}/...",
            "@odata.type": sub_type.value,
            "@odata.id": f"{proto_url}/users/foo@bar.com/Subscriptions('xyz')",
            "Id": "xyz",
            "Resource": f"{proto_url}/me/mailfolders('inbox')/Messages",
            "ChangeType": "Created",
        }
        requests_mock.register_uri("POST", f"{proto_url}/subscriptions", json=response)
        subscriber.subscribe(resource=folder, events=[O365EventType.CREATED])
        assert len(subscriber.subscriptions) == 1
        assert subscriber.subscriptions[0].type == sub_type
        assert subscriber.subscriptions[0].id == "xyz"
        assert subscriber.subscriptions[0].events == [O365EventType.CREATED]
        assert subscriber.subscriptions[0].raw == response
