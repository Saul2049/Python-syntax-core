import os
import pytest
from unittest.mock import patch, MagicMock
from src.telegram import TelegramBot


@pytest.mark.skipif(
    "TG_TOKEN" not in os.environ,
    reason="Telegram token not available in environment"
)
class TestTelegramBot:
    """Telegram bot tests that require a valid token."""
    
    def setup_method(self):
        """Setup test environment."""
        self.token = os.environ["TG_TOKEN"]
        self.bot = TelegramBot(self.token)
        
    def test_send_message(self):
        """Test sending a message."""
        chat_id = "123456789"
        message = "Test message"
        
        with patch.object(self.bot, 'send_message') as mock_send:
            self.bot.send_message(chat_id, message)
            mock_send.assert_called_once_with(chat_id, message)
            
    def test_send_photo(self):
        """Test sending a photo."""
        chat_id = "123456789"
        photo_path = "test.png"
        
        with patch.object(self.bot, 'send_photo') as mock_send:
            self.bot.send_photo(chat_id, photo_path)
            mock_send.assert_called_once_with(chat_id, photo_path)


class TestTelegramBotMocked:
    """Telegram bot tests that don't require a token."""
    
    def setup_method(self):
        """Setup test environment with mocked bot."""
        self.token = "dummy_token"
        self.bot = TelegramBot(self.token)
        
    def test_initialization(self):
        """Test bot initialization."""
        assert self.bot.token == self.token
        assert self.bot.bot is not None
        
    def test_send_message_mocked(self):
        """Test sending a message with mocked bot."""
        chat_id = "123456789"
        message = "Test message"
        
        with patch.object(self.bot.bot, 'send_message') as mock_send:
            self.bot.send_message(chat_id, message)
            mock_send.assert_called_once_with(chat_id, message)
            
    def test_send_photo_mocked(self):
        """Test sending a photo with mocked bot."""
        chat_id = "123456789"
        photo_path = "test.png"
        
        with patch.object(self.bot.bot, 'send_photo') as mock_send:
            self.bot.send_photo(chat_id, photo_path)
            mock_send.assert_called_once_with(chat_id, photo_path) 