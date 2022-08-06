import O365.account
import pytest

from O365_notifications.constants import O365EventType
from O365_notifications.streaming import O365StreamingSubscriber


@pytest.fixture(scope="class")
def account():
    return O365.Account(
        credentials=("user", "pass"),
        main_resource="me@test.com",
    )


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
