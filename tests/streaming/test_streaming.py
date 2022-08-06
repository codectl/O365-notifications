import O365.account
import pytest

from O365_notifications.constants import O365EventType
from O365_notifications.streaming import O365StreamingSubscriber


@pytest.fixture(scope="class")
def account(backend):
    account = O365.Account(
        credentials=("user", "pass"),
        tenant_id="foo",
        main_resource="foo@bar.com",
        auth_flow_type="credentials",
        token_backend=backend
    )
    account.authenticate()
    return account


@pytest.fixture(scope="class")
def folder(account):
    return account.mailbox().inbox_folder()


@pytest.fixture(scope="class")
def subscriber(account, folder):
    subscriber = O365StreamingSubscriber(parent=account)
    events = [O365EventType.CREATED]
    subscriber.subscribe(resource=folder, events=events)
    return subscriber


class TestMailbox:
    def test_subscribe(self, account, folder):
        subscriber = O365StreamingSubscriber(parent=account)
        subscriber.subscribe(resource=folder, events=[O365EventType.CREATED])
