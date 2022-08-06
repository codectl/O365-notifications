import O365
import pytest

from O365_notifications.constants import O365EventType
from O365_notifications.streaming import O365StreamingSubscriber


@pytest.fixture(scope="class")
def account(backend):
    return O365.Account(
        credentials=("user", "pass"),
        tenant_id="foo",
        main_resource="foo@bar.com",
        auth_flow_type="credentials",
        token_backend=backend
    )


@pytest.fixture(scope="class")
def folder(account):
    return account.mailbox().inbox_folder()


@pytest.fixture(scope="class")
def subscriber(account, folder):
    return O365StreamingSubscriber(parent=account)


class TestMailbox:
    def test_subscribe(self, subscriber, folder):
        # requests_mock.register_uri("POST", account.)
        url = subscriber.build_base_url(subscriber.parent.main_resource)
        subscriber.subscribe(resource=folder, events=[O365EventType.CREATED])
