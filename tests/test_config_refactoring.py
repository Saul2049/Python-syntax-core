#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Refactoring Tests (配置重构测试)

Tests for the new modular configuration system to ensure it works correctly
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.config import (
    ConfigSanitizer,
    ConfigValidator,
    DefaultConfig,
    TradingConfig,
    get_config,
    reset_config,
)


class TestConfigRefactoring(unittest.TestCase):
    """Test configuration refactoring"""

    def setUp(self):
        """Setup test environment"""
        # Reset global config before each test
        reset_config()

        # Create temporary config files
        self.temp_dir = tempfile.mkdtemp()
        self.config_ini_path = os.path.join(self.temp_dir, "test_config.ini")
        self.config_yaml_path = os.path.join(self.temp_dir, "test_config.yaml")

        # Create test INI file
        with open(self.config_ini_path, "w") as f:
            f.write(
                """
[trading]
symbols = BTCUSDT,ETHUSDT
risk_percent = 0.02
fast_ma = 10
slow_ma = 30
test_mode = true

[account]
equity = 5000.0
api_key = test_key
api_secret = test_secret

[system]
log_level = DEBUG
log_dir = test_logs
"""
            )

        # Create test YAML file
        with open(self.config_yaml_path, "w") as f:
            f.write(
                """
trading:
  symbols: ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
  risk_percent: 0.015

monitoring:
  enabled: true
  port: 9999
"""
            )

    def tearDown(self):
        """Cleanup test environment"""
        # Clean up temp files
        try:
            os.unlink(self.config_ini_path)
            os.unlink(self.config_yaml_path)
            os.rmdir(self.temp_dir)
        except:
            pass

        # Reset config
        reset_config()

    def test_default_config(self):
        """Test default configuration values"""
        defaults = DefaultConfig.get_defaults()

        # Check required keys exist
        required_keys = [
            "symbols",
            "risk_percent",
            "fast_ma",
            "slow_ma",
            "account_equity",
            "log_level",
            "monitoring_port",
        ]

        for key in required_keys:
            self.assertIn(key, defaults)

        # Check default values
        self.assertEqual(defaults["symbols"], ["BTCUSDT", "ETHUSDT"])
        self.assertEqual(defaults["risk_percent"], 0.01)
        self.assertEqual(defaults["fast_ma"], 7)
        self.assertEqual(defaults["slow_ma"], 25)

    def test_config_validation(self):
        """Test configuration validation"""
        validator = ConfigValidator()

        # Valid config should pass
        valid_config = DefaultConfig.get_defaults()
        self.assertTrue(validator.validate(valid_config))

        # Invalid risk_percent should fail
        invalid_config = valid_config.copy()
        invalid_config["risk_percent"] = 1.5  # > 1.0

        with self.assertRaises(ValueError):
            validator.validate(invalid_config)

        # Invalid MA periods should fail
        invalid_config = valid_config.copy()
        invalid_config["fast_ma"] = 50
        invalid_config["slow_ma"] = 25  # fast >= slow

        with self.assertRaises(ValueError):
            validator.validate(invalid_config)

    def test_config_sanitizer(self):
        """Test configuration sanitization"""
        raw_config = {
            "symbols": ["  btcusdt  ", " ETHUSDT "],
            "log_level": "  info  ",
            "api_key": "  test_key  ",
        }

        sanitized = ConfigSanitizer.sanitize(raw_config)

        # Check whitespace stripped
        self.assertEqual(sanitized["log_level"], "info")
        self.assertEqual(sanitized["api_key"], "test_key")

        # Check symbols uppercase and stripped
        self.assertEqual(sanitized["symbols"], ["BTCUSDT", "ETHUSDT"])

    def test_ini_config_loading(self):
        """Test loading from INI file"""
        config = TradingConfig(config_file=self.config_ini_path)

        # Check values from INI file
        self.assertEqual(config.get_symbols(), ["BTCUSDT", "ETHUSDT"])
        self.assertEqual(config.get_risk_percent(), 0.02)
        self.assertEqual(config.get_fast_ma(), 10)
        self.assertEqual(config.get_slow_ma(), 30)
        self.assertEqual(config.get_account_equity(), 5000.0)
        self.assertEqual(config.get_log_level(), "DEBUG")
        self.assertEqual(config.get_log_dir(), "test_logs")

    def test_yaml_config_loading(self):
        """Test loading from YAML file"""
        config = TradingConfig(config_yaml=self.config_yaml_path)

        # Check values from YAML file
        self.assertEqual(config.get_symbols(), ["BTCUSDT", "ETHUSDT", "ADAUSDT"])
        self.assertEqual(config.get_risk_percent(), 0.015)
        self.assertEqual(config.get_monitoring_port(), 9999)
        self.assertTrue(config.is_monitoring_enabled())

    def test_config_priority(self):
        """Test configuration priority (YAML overrides INI)"""
        config = TradingConfig(config_file=self.config_ini_path, config_yaml=self.config_yaml_path)

        # YAML values should override INI values
        self.assertEqual(config.get_symbols(), ["BTCUSDT", "ETHUSDT", "ADAUSDT"])
        self.assertEqual(config.get_risk_percent(), 0.015)  # From YAML

        # Values not in YAML should come from INI
        self.assertEqual(config.get_fast_ma(), 10)  # From INI
        self.assertEqual(config.get_account_equity(), 5000.0)  # From INI

    def test_get_config_function(self):
        """Test global get_config function"""
        # First call should create new instance
        config1 = get_config(config_file=self.config_ini_path)
        self.assertIsInstance(config1, TradingConfig)

        # Second call should return same instance (cached)
        config2 = get_config()
        self.assertIs(config1, config2)

        # Force new instance
        reset_config()
        config3 = get_config(config_file=self.config_ini_path, use_cache=False)
        self.assertIsNot(config1, config3)

    def test_backward_compatibility(self):
        """Test backward compatibility with old config import"""
        # This should work without breaking existing code
        try:
            from src.config import TradingConfig as OldTradingConfig

            config = OldTradingConfig()
            self.assertIsInstance(config, TradingConfig)
        except ImportError:
            self.fail("Backward compatibility broken")

    def test_config_methods(self):
        """Test all configuration getter methods"""
        config = TradingConfig(config_file=self.config_ini_path)

        # Test all getter methods
        methods_to_test = [
            "get_symbols",
            "get_risk_percent",
            "get_fast_ma",
            "get_slow_ma",
            "get_atr_period",
            "get_check_interval",
            "is_test_mode",
            "get_account_equity",
            "get_api_credentials",
            "get_telegram_config",
            "get_log_level",
            "get_log_dir",
            "get_trades_dir",
            "use_binance_testnet",
            "get_monitoring_port",
            "is_monitoring_enabled",
        ]

        for method_name in methods_to_test:
            with self.subTest(method=method_name):
                method = getattr(config, method_name)
                result = method()
                self.assertIsNotNone(result)  # Should return something

    def test_config_set_get(self):
        """Test generic set/get methods"""
        config = TradingConfig()

        # Test setting and getting custom values
        config.set("custom_key", "custom_value")
        self.assertEqual(config.get("custom_key"), "custom_value")

        # Test getting with default
        self.assertEqual(config.get("nonexistent_key", "default"), "default")

        # Test to_dict
        config_dict = config.to_dict()
        self.assertIsInstance(config_dict, dict)
        self.assertIn("custom_key", config_dict)


class TestConfigPerformance(unittest.TestCase):
    """Test configuration system performance"""

    def test_config_loading_speed(self):
        """Test that config loading is reasonably fast"""
        import time

        start_time = time.time()
        for _ in range(100):
            reset_config()
            config = get_config()
        end_time = time.time()

        # Should complete 100 config loads in under 1 second
        self.assertLess(end_time - start_time, 1.0)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
