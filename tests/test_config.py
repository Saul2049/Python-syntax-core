#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Module Tests
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

# Import modules to test
try:
    from src.config import TradingConfig, get_config, setup_logging
except ImportError:
    pytest.skip("Config module not available, skipping tests", allow_module_level=True)


class TestTradingConfig(unittest.TestCase):
    """Test TradingConfig class"""

    def setUp(self):
        """Setup test environment"""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # Store original environment variables
        self.original_env = {}
        env_keys = [
            "SYMBOLS",
            "RISK_PERCENT",
            "FAST_MA",
            "SLOW_MA",
            "ATR_PERIOD",
            "CHECK_INTERVAL",
            "TEST_MODE",
            "ACCOUNT_EQUITY",
            "API_KEY",
            "API_SECRET",
            "TG_TOKEN",
            "TG_CHAT_ID",
            "LOG_LEVEL",
            "LOG_DIR",
            "TRADES_DIR",
            "USE_BINANCE_TESTNET",
            "MONITORING_PORT",
        ]

        for key in env_keys:
            if key in os.environ:
                self.original_env[key] = os.environ[key]
                del os.environ[key]

    def tearDown(self):
        """Cleanup test environment"""
        # Clean up temporary files
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

        # Remove any environment variables that were set during testing
        test_env_vars = [
            "SYMBOLS",
            "RISK_PERCENT",
            "FAST_MA",
            "SLOW_MA",
            "ATR_PERIOD",
            "CHECK_INTERVAL",
            "TEST_MODE",
            "ACCOUNT_EQUITY",
            "API_KEY",
            "API_SECRET",
            "TG_TOKEN",
            "TG_CHAT_ID",
            "LOG_LEVEL",
            "LOG_DIR",
            "TRADES_DIR",
            "USE_BINANCE_TESTNET",
            "MONITORING_PORT",
            "MONITORING_ENABLED",
        ]

        for key in test_env_vars:
            if key in os.environ:
                del os.environ[key]

        # Restore original environment variables
        for key, value in self.original_env.items():
            os.environ[key] = value

        # Reset global config
        import src.config

        src.config._global_config = None

    def test_init_default(self):
        """Test initialization with default values"""
        config = TradingConfig()

        # Test default values
        self.assertEqual(config.get_symbols(), ["BTCUSDT", "ETHUSDT"])
        self.assertEqual(config.get_risk_percent(), 0.01)
        self.assertEqual(config.get_fast_ma(), 7)
        self.assertEqual(config.get_slow_ma(), 25)
        self.assertTrue(config.is_test_mode())
        self.assertTrue(config.use_binance_testnet())

    def test_load_ini_config(self):
        """Test loading INI configuration"""
        # Create test INI file
        ini_content = """
[trading]
symbols = BTCUSDT,ETHUSDT,BNBUSDT
risk_percent = 0.02
fast_ma = 5
slow_ma = 20
test_mode = false

[account]
equity = 50000.0
api_key = test_key
api_secret = test_secret

[system]
log_level = DEBUG
log_dir = test_logs
"""
        ini_file = self.temp_path / "test_config.ini"
        with open(ini_file, "w") as f:
            f.write(ini_content)

        config = TradingConfig(config_file=str(ini_file))

        # Test loaded values
        self.assertEqual(config.get_symbols(), ["BTCUSDT", "ETHUSDT", "BNBUSDT"])
        self.assertEqual(config.get_risk_percent(), 0.02)
        self.assertEqual(config.get_fast_ma(), 5)
        self.assertEqual(config.get_slow_ma(), 20)
        self.assertFalse(config.is_test_mode())
        self.assertEqual(config.get_account_equity(), 50000.0)
        self.assertEqual(config.get_log_level(), "DEBUG")

    def test_load_env_file(self):
        """Test loading environment variables from file"""
        # Create test .env file
        env_content = """
API_KEY=env_test_key
API_SECRET=env_test_secret
LOG_LEVEL=WARNING
TEST_MODE=true
SYMBOLS=BTCUSDT,ADAUSDT
"""
        env_file = self.temp_path / ".env"
        with open(env_file, "w") as f:
            f.write(env_content)

        config = TradingConfig(env_file=str(env_file))

        # Check that environment variables were set
        self.assertEqual(os.environ.get("API_KEY"), "env_test_key")
        self.assertEqual(os.environ.get("LOG_LEVEL"), "WARNING")

    def test_load_env_vars(self):
        """Test loading configuration from environment variables"""
        # Set test environment variables
        test_env = {
            "SYMBOLS": "BTCUSDT,SOLUSDT",
            "RISK_PERCENT": "0.05",
            "FAST_MA": "10",
            "TEST_MODE": "false",
            "LOG_LEVEL": "ERROR",
        }

        with patch.dict(os.environ, test_env):
            config = TradingConfig()

            # Test environment variable override
            self.assertEqual(config.get_symbols(), ["BTCUSDT", "SOLUSDT"])
            self.assertEqual(config.get_risk_percent(), 0.05)
            self.assertEqual(config.get_fast_ma(), 10)
            self.assertFalse(config.is_test_mode())
            self.assertEqual(config.get_log_level(), "ERROR")

    def test_yaml_config_unavailable(self):
        """Test YAML config when file doesn't exist"""
        # Test with nonexistent YAML file - should not raise error
        config = TradingConfig(config_yaml="nonexistent.yaml")
        self.assertEqual(config.get_symbols(), ["BTCUSDT", "ETHUSDT"])

        # Test that configuration uses defaults when YAML file is missing
        self.assertEqual(config.get_risk_percent(), 0.01)
        self.assertTrue(config.is_test_mode())

    def test_nonexistent_files(self):
        """Test handling of nonexistent configuration files"""
        config = TradingConfig(
            config_file="nonexistent.ini",
            config_yaml="nonexistent.yaml",
            env_file="nonexistent.env",
        )

        # Should fall back to defaults
        self.assertEqual(config.get_symbols(), ["BTCUSDT", "ETHUSDT"])
        self.assertEqual(config.get_risk_percent(), 0.01)

    def test_get_api_credentials(self):
        """Test API credentials getter"""
        config = TradingConfig()
        config.set("api_key", "test_key")
        config.set("api_secret", "test_secret")

        api_key, api_secret = config.get_api_credentials()
        self.assertEqual(api_key, "test_key")
        self.assertEqual(api_secret, "test_secret")

    def test_get_telegram_config(self):
        """Test Telegram configuration getter"""
        config = TradingConfig()
        config.set("telegram_token", "test_token")
        config.set("telegram_chat_id", "test_chat_id")

        token, chat_id = config.get_telegram_config()
        self.assertEqual(token, "test_token")
        self.assertEqual(chat_id, "test_chat_id")

    def test_generic_getter_setter(self):
        """Test generic get/set methods"""
        config = TradingConfig()

        # Test setting and getting custom value
        config.set("custom_key", "custom_value")
        self.assertEqual(config.get("custom_key"), "custom_value")

        # Test default value
        self.assertEqual(config.get("nonexistent_key", "default"), "default")
        self.assertIsNone(config.get("nonexistent_key"))

    def test_to_dict(self):
        """Test configuration dictionary export"""
        config = TradingConfig()
        config_dict = config.to_dict()

        self.assertIsInstance(config_dict, dict)
        self.assertIn("symbols", config_dict)
        self.assertIn("risk_percent", config_dict)
        self.assertIn("test_mode", config_dict)

    def test_merge_dict(self):
        """Test dictionary merging functionality"""
        config = TradingConfig()

        # Test the new merge_config method
        external_config = {
            "symbols": ["BTCUSDT", "SOLUSDT"],
            "risk_percent": 0.05,
            "custom_setting": "test_value",
        }

        config.merge_config(external_config)

        # Test that values were merged
        self.assertEqual(config.get_symbols(), ["BTCUSDT", "SOLUSDT"])
        self.assertEqual(config.get_risk_percent(), 0.05)
        self.assertEqual(config.get("custom_setting"), "test_value")


class TestGlobalConfig(unittest.TestCase):
    """Test global configuration functionality"""

    def setUp(self):
        """Setup test environment"""
        # Reset global config before each test
        import src.config

        src.config._global_config = None

    def tearDown(self):
        """Cleanup test environment"""
        # Reset global config after each test
        import src.config

        src.config._global_config = None

    def test_get_config_singleton(self):
        """Test that get_config returns singleton instance"""
        config1 = get_config()
        config2 = get_config()

        # Should be the same instance
        self.assertIs(config1, config2)

    def test_get_config_with_params(self):
        """Test get_config with parameters"""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
            f.write("[trading]\nsymbols = TESTUSDT\n")
            temp_config = f.name

        try:
            # Clear any environment variables that might interfere
            with patch.dict(os.environ, {}, clear=True):
                # Reset global config to test with parameters
                import src.config

                src.config._global_config = None

                config = get_config(config_file=temp_config)
                self.assertIn("TESTUSDT", config.get_symbols())
        finally:
            os.unlink(temp_config)

    @patch("src.config.Path")
    def test_get_config_auto_discovery(self, mock_path):
        """Test automatic configuration file discovery"""
        # Mock file existence
        mock_path.return_value.exists.side_effect = lambda: True

        config = get_config()
        self.assertIsInstance(config, TradingConfig)


class TestLoggingSetup(unittest.TestCase):
    """Test logging setup functionality"""

    def test_setup_logging_default(self):
        """Test logging setup with default configuration"""
        config = TradingConfig()

        # Should not raise exception
        setup_logging(config)

    def test_setup_logging_no_config(self):
        """Test logging setup without configuration"""
        # Should create default config and setup logging
        setup_logging()

    @patch("src.config.logging.getLogger")
    @patch("src.config.logging.FileHandler")
    @patch("src.config.logging.StreamHandler")
    def test_setup_logging_handlers(self, mock_stream, mock_file, mock_logger):
        """Test that logging handlers are properly configured"""
        config = TradingConfig()
        config.set("log_level", "DEBUG")
        config.set("log_dir", "test_logs")

        setup_logging(config)

        # Verify handlers were created
        mock_stream.assert_called()
        mock_file.assert_called()


if __name__ == "__main__":
    unittest.main()
