import pytest


@pytest.fixture
def token():
    """Dummy Telegram bot token (used only in offline tests)."""
    return "TEST_TOKEN_1234567890"


@pytest.fixture
def chat_id():
    """Dummy Telegram chat_id used by offline tests."""
    return "123456789"
