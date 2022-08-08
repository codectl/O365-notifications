import random

import pytest
import pytest_cases
from O365 import Account, MSGraphProtocol, MSOffice365Protocol
from pytest_cases import fixture_ref

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


@pytest.fixture
def folder(account):
    return account.mailbox().inbox_folder()


@pytest.fixture(scope="class")
def subscriber(account):
    return O365StreamingSubscriber(parent=account)


@pytest_cases.fixture
@pytest_cases.parametrize("resource", [fixture_ref("folder")])
@pytest_cases.parametrize("events", [[O365EventType.CREATED]])
def subscribe(resource, events, subscriber, requests_mock):
    proto_url = f"{subscriber.protocol.service_url}{subscriber.main_resource}"
    sub_type = subscriber.namespace.O365SubscriptionType.STREAMING_SUBSCRIPTION
    random_id = str(random.randint(1000, 9999))
    response = {
        "@odata.context": f"{proto_url}/...",
        "@odata.type": sub_type.value,
        "@odata.id": f"{proto_url}/users/foo@bar.com/Subscriptions('{random_id}')",
        "Id": random_id,
        "Resource": f"{proto_url}/me/mailfolders('inbox')/Messages",
        "ChangeType": ",".join(e.value for e in events)
    }
    requests_mock.register_uri("POST", f"{proto_url}/subscriptions", json=response)
    subscriber.subscribe(resource=resource, events=events)


class TestMailbox:

    @pytest_cases.parametrize("subscription", [fixture_ref("subscribe")])
    def test_subscription(self, subscription, subscriber):
        assert len(subscriber.subscriptions) == 1
        assert subscriber.subscriptions[0].events == [O365EventType.CREATED]

    # @pytest_cases.parametrize("subscription", [fixture_ref("subscribe")])
    # def test_renew_subscription(self, subscription, subscriber):
    #     print(subscriber.subscriptions[0].id)
    #     subscriber.renew_subscriptions()
    #     print(subscriber.subscriptions[0].id)
    #     assert len(subscriber.subscriptions) == 1
    #     assert subscriber.subscriptions[0].id == "xyz"
    #     assert subscriber.subscriptions[0].events == [O365EventType.CREATED]
