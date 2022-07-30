import O365.account
import pytest

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
def subscriber(account):
    subscriber = O365StreamingSubscriber()
    inbox_folder = account.mailbox().inbox_folder()
    subscriber.subscribe(resource=inbox_folder)
    return subscriber


class TestMailbox:
    def test_subscribe(self, folder):
        subscriber = O365StreamingSubscriber()
        subscriber.subscribe(resource=folder)
