import pytest

from O365.utils import BaseTokenBackend


class TestBackend(BaseTokenBackend):
    def save_token(self):
        pass

    def delete_token(self):
        pass

    def check_token(self):
        return True

    def load_token(self):
        return {
            "token_type": "Bearer",
            "expires_in": 3599,
            "ext_expires_in": 3599,
            "access_token": "token",
            "expires_at": 0,
        }


@pytest.fixture(scope="session")
def backend():
    return TestBackend()
