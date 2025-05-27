#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for notification module
"""

import os
import unittest
from unittest.mock import MagicMock, patch

import pytest

# Import modules to test
try:
    from src.notify import Notifier
except ImportError:
    pytest.skip("Notify module not available, skipping tests", allow_module_level=True)


class TestNotifier(unittest.TestCase):
    """Test Notifier class"""

    def setUp(self):
        """Setup test environment"""
        # Mock environment variables
        self.token = "test_token_123"
        self.chat_id = "123456789"

        # Set environment variables for testing
        os.environ["TG_TOKEN"] = self.token
        os.environ["TG_CHAT_ID"] = self.chat_id

    def tearDown(self):
        """Clean up test environment"""
        # Clean up environment variables
        if "TG_TOKEN" in os.environ:
            del os.environ["TG_TOKEN"]
        if "TG_CHAT_ID" in os.environ:
            del os.environ["TG_CHAT_ID"]

    def test_init_with_token(self):
        """Test initialization with token"""
        notifier = Notifier(self.token)
        self.assertEqual(notifier.token, self.token)
        self.assertEqual(notifier.chat_id, self.chat_id)

    def test_init_without_token(self):
        """Test initialization without token using env vars"""
        notifier = Notifier()
        self.assertEqual(notifier.token, self.token)
        self.assertEqual(notifier.chat_id, self.chat_id)

    def test_init_missing_token(self):
        """Test initialization with missing token"""
        del os.environ["TG_TOKEN"]
        with self.assertRaises(ValueError):
            Notifier()

    def test_init_missing_chat_id(self):
        """Test initialization with missing chat ID"""
        del os.environ["TG_CHAT_ID"]
        # Also remove the fallback TG_CHAT if it exists
        if "TG_CHAT" in os.environ:
            del os.environ["TG_CHAT"]
        with self.assertRaises(ValueError):
            Notifier()

    @patch("src.telegram.TelegramBot.send_message")
    def test_notify_success(self, mock_send):
        """Test successful notification"""
        mock_send.return_value = True

        notifier = Notifier(self.token)
        notifier.notify("Test message", "INFO")

        mock_send.assert_called_once()
        call_args = mock_send.call_args[0]
        self.assertEqual(call_args[0], self.chat_id)
        self.assertIn("Test message", call_args[1])
        self.assertIn("INFO", call_args[1])

    @patch("src.telegram.TelegramBot.send_message")
    def test_notify_trade(self, mock_send):
        """Test trade notification"""
        mock_send.return_value = True

        notifier = Notifier(self.token)
        notifier.notify_trade("BUY", "BTCUSDT", 30000.0, 0.001, "MA crossover")

        mock_send.assert_called_once()
        call_args = mock_send.call_args[0]
        message = call_args[1]
        self.assertIn("BUY", message)
        self.assertIn("BTCUSDT", message)
        self.assertIn("30000.0", message)
        self.assertIn("0.001", message)
        self.assertIn("MA crossover", message)

    @patch("src.telegram.TelegramBot.send_message")
    def test_notify_error(self, mock_send):
        """Test error notification"""
        mock_send.return_value = True

        notifier = Notifier(self.token)
        error = Exception("Test error")
        notifier.notify_error(error, "Test context")

        mock_send.assert_called_once()
        call_args = mock_send.call_args[0]
        message = call_args[1]
        self.assertIn("Test error", message)
        self.assertIn("Test context", message)

    @patch("src.telegram.TelegramBot.send_message")
    def test_notify_with_exception(self, mock_send):
        """Test notification with telegram exception"""
        mock_send.side_effect = Exception("Network error")

        notifier = Notifier(self.token)
        # Should not raise exception
        notifier.notify("Test message")

    def test_format_message(self):
        """Test message formatting"""
        notifier = Notifier(self.token)
        formatted = notifier._format_message("Test message", "WARNING")

        self.assertIn("WARNING", formatted)
        self.assertIn("Test message", formatted)
        # Should contain timestamp
        self.assertRegex(formatted, r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]")


class TestNotifierIntegration(unittest.TestCase):
    """Integration tests for Notifier"""

    def setUp(self):
        """Setup test environment"""
        os.environ["TG_TOKEN"] = "test_token_123"
        os.environ["TG_CHAT_ID"] = "123456789"

    def tearDown(self):
        """Clean up test environment"""
        if "TG_TOKEN" in os.environ:
            del os.environ["TG_TOKEN"]
        if "TG_CHAT_ID" in os.environ:
            del os.environ["TG_CHAT_ID"]

    @patch("src.telegram.TelegramBot.send_message")
    def test_full_notification_workflow(self, mock_send):
        """Test complete notification workflow"""
        mock_send.return_value = True

        notifier = Notifier()

        # Test different notification types
        notifier.notify("System started", "INFO")
        notifier.notify_trade("BUY", "ETHUSDT", 2000.0, 0.5)
        notifier.notify_error(ValueError("Invalid parameter"), "config_validation")

        # Should have been called 3 times
        self.assertEqual(mock_send.call_count, 3)

    def test_notification_without_setup(self):
        """Test notifications fail gracefully without proper setup"""
        del os.environ["TG_TOKEN"]

        with self.assertRaises(ValueError):
            Notifier()


if __name__ == "__main__":
    unittest.main()
