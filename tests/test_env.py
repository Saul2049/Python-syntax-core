#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Environment Setup

Provides mock environment variables for testing purposes
"""

import os
import unittest
from unittest.mock import patch


class TestEnvironment:
    """Test environment variable manager"""

    TEST_ENV_VARS = {
        # Telegram Configuration for Testing
        "TG_TOKEN": "test_token_123456789",
        "TG_CHAT_ID": "test_chat_id_123",
        "TG_CHAT": "test_chat_id_123",
        # Binance API Configuration for Testing
        "API_KEY": "test_api_key",
        "API_SECRET": "test_api_secret",
        # Trading Configuration for Testing
        "SYMBOLS": "BTCUSDT,ETHUSDT",
        "RISK_PERCENT": "0.01",
        "FAST_MA": "7",
        "SLOW_MA": "25",
        "TEST_MODE": "true",
        "ACCOUNT_EQUITY": "10000.0",
        # System Configuration for Testing
        "LOG_LEVEL": "INFO",
        "LOG_DIR": "test_logs",
        "TRADES_DIR": "test_trades",
        "USE_BINANCE_TESTNET": "true",
        "MONITORING_PORT": "9091",
    }

    @classmethod
    def setup_test_env(cls):
        """Setup test environment variables"""
        for key, value in cls.TEST_ENV_VARS.items():
            os.environ[key] = value

    @classmethod
    def cleanup_test_env(cls):
        """Cleanup test environment variables"""
        for key in cls.TEST_ENV_VARS.keys():
            if key in os.environ:
                del os.environ[key]

    @classmethod
    def get_env_patch(cls):
        """Get environment patch for mocking"""
        return patch.dict(os.environ, cls.TEST_ENV_VARS)


class BaseTestCase(unittest.TestCase):
    """Base test case with environment setup"""

    def setUp(self):
        """Setup test environment"""
        TestEnvironment.setup_test_env()

    def tearDown(self):
        """Cleanup test environment"""
        TestEnvironment.cleanup_test_env()


# Pytest fixture for environment setup
def pytest_setup_env():
    """Pytest fixture to setup test environment"""
    TestEnvironment.setup_test_env()
    yield
    TestEnvironment.cleanup_test_env()
