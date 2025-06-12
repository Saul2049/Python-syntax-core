#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置默认值全面测试模块 (Comprehensive Config Defaults Test Module)

为 src/config/defaults.py 提供100%测试覆盖率
"""

import unittest

from src.config.defaults import DefaultConfig


class TestDefaultConfig(unittest.TestCase):
    """测试默认配置类 (Test Default Config Class)"""

    def test_get_defaults_basic(self):
        """测试基本默认配置获取"""
        defaults = DefaultConfig.get_defaults()

        # 验证返回类型
        self.assertIsInstance(defaults, dict)

        # 验证必要的配置项存在
        required_keys = [
            "symbols",
            "risk_percent",
            "fast_ma",
            "slow_ma",
            "atr_period",
            "check_interval",
            "test_mode",
            "account_equity",
            "api_key",
            "api_secret",
            "telegram_token",
            "telegram_chat_id",
            "log_level",
            "log_dir",
            "trades_dir",
            "use_binance_testnet",
            "request_timeout",
            "max_retries",
            "monitoring_enabled",
            "monitoring_port",
        ]

        for key in required_keys:
            self.assertIn(key, defaults, f"Missing required key: {key}")

    def test_get_defaults_values(self):
        """测试默认配置值的正确性"""
        defaults = DefaultConfig.get_defaults()

        # 验证交易配置
        self.assertEqual(defaults["symbols"], ["BTCUSDT", "ETHUSDT"])
        self.assertEqual(defaults["risk_percent"], 0.01)
        self.assertEqual(defaults["fast_ma"], 7)
        self.assertEqual(defaults["slow_ma"], 25)
        self.assertEqual(defaults["atr_period"], 14)
        self.assertEqual(defaults["check_interval"], 60)
        self.assertTrue(defaults["test_mode"])

        # 验证账户配置
        self.assertEqual(defaults["account_equity"], 10000.0)
        self.assertEqual(defaults["api_key"], "")
        self.assertEqual(defaults["api_secret"], "")

        # 验证通知配置
        self.assertEqual(defaults["telegram_token"], "")
        self.assertEqual(defaults["telegram_chat_id"], "")

        # 验证系统配置
        self.assertEqual(defaults["log_level"], "INFO")
        self.assertEqual(defaults["log_dir"], "logs")
        self.assertEqual(defaults["trades_dir"], "trades")

        # 验证网络配置
        self.assertTrue(defaults["use_binance_testnet"])
        self.assertEqual(defaults["request_timeout"], 30)
        self.assertEqual(defaults["max_retries"], 3)

        # 验证监控配置
        self.assertTrue(defaults["monitoring_enabled"])
        self.assertEqual(defaults["monitoring_port"], 9090)

    def test_get_trading_defaults(self):
        """测试交易相关默认配置"""
        trading_defaults = DefaultConfig.get_trading_defaults()

        # 验证返回类型
        self.assertIsInstance(trading_defaults, dict)

        # 验证只包含交易相关的配置
        expected_keys = {
            "symbols",
            "risk_percent",
            "fast_ma",
            "slow_ma",
            "atr_period",
            "check_interval",
            "test_mode",
        }
        self.assertEqual(set(trading_defaults.keys()), expected_keys)

        # 验证值的正确性
        self.assertEqual(trading_defaults["symbols"], ["BTCUSDT", "ETHUSDT"])
        self.assertEqual(trading_defaults["risk_percent"], 0.01)
        self.assertEqual(trading_defaults["fast_ma"], 7)
        self.assertEqual(trading_defaults["slow_ma"], 25)
        self.assertEqual(trading_defaults["atr_period"], 14)
        self.assertEqual(trading_defaults["check_interval"], 60)
        self.assertTrue(trading_defaults["test_mode"])

    def test_get_account_defaults(self):
        """测试账户相关默认配置"""
        account_defaults = DefaultConfig.get_account_defaults()

        # 验证返回类型
        self.assertIsInstance(account_defaults, dict)

        # 验证只包含账户相关的配置
        expected_keys = {"account_equity", "api_key", "api_secret"}
        self.assertEqual(set(account_defaults.keys()), expected_keys)

        # 验证值的正确性
        self.assertEqual(account_defaults["account_equity"], 10000.0)
        self.assertEqual(account_defaults["api_key"], "")
        self.assertEqual(account_defaults["api_secret"], "")

    def test_get_system_defaults(self):
        """测试系统相关默认配置"""
        system_defaults = DefaultConfig.get_system_defaults()

        # 验证返回类型
        self.assertIsInstance(system_defaults, dict)

        # 验证只包含系统相关的配置
        expected_keys = {
            "log_level",
            "log_dir",
            "trades_dir",
            "use_binance_testnet",
            "request_timeout",
            "max_retries",
        }
        self.assertEqual(set(system_defaults.keys()), expected_keys)

        # 验证值的正确性
        self.assertEqual(system_defaults["log_level"], "INFO")
        self.assertEqual(system_defaults["log_dir"], "logs")
        self.assertEqual(system_defaults["trades_dir"], "trades")
        self.assertTrue(system_defaults["use_binance_testnet"])
        self.assertEqual(system_defaults["request_timeout"], 30)
        self.assertEqual(system_defaults["max_retries"], 3)

    def test_defaults_consistency(self):
        """测试默认配置的一致性"""
        all_defaults = DefaultConfig.get_defaults()
        trading_defaults = DefaultConfig.get_trading_defaults()
        account_defaults = DefaultConfig.get_account_defaults()
        system_defaults = DefaultConfig.get_system_defaults()

        # 验证分类配置是全配置的子集
        for key, value in trading_defaults.items():
            self.assertIn(key, all_defaults)
            self.assertEqual(value, all_defaults[key])

        for key, value in account_defaults.items():
            self.assertIn(key, all_defaults)
            self.assertEqual(value, all_defaults[key])

        for key, value in system_defaults.items():
            self.assertIn(key, all_defaults)
            self.assertEqual(value, all_defaults[key])

    def test_defaults_immutability(self):
        """测试默认配置的不可变性"""
        # 获取两次配置，应该是独立的字典
        defaults1 = DefaultConfig.get_defaults()
        defaults2 = DefaultConfig.get_defaults()

        # 修改第一个字典不应该影响第二个
        defaults1["symbols"] = ["MODIFIED"]
        self.assertNotEqual(defaults1["symbols"], defaults2["symbols"])
        self.assertEqual(defaults2["symbols"], ["BTCUSDT", "ETHUSDT"])

    def test_trading_defaults_completeness(self):
        """测试交易默认配置的完整性"""
        trading_defaults = DefaultConfig.get_trading_defaults()

        # 验证包含所有必要的交易参数
        required_trading_keys = [
            "symbols",
            "risk_percent",
            "fast_ma",
            "slow_ma",
            "atr_period",
            "check_interval",
            "test_mode",
        ]

        for key in required_trading_keys:
            self.assertIn(key, trading_defaults)

        # 验证不包含非交易参数
        non_trading_keys = ["api_key", "api_secret", "telegram_token", "log_level"]

        for key in non_trading_keys:
            self.assertNotIn(key, trading_defaults)

    def test_account_defaults_completeness(self):
        """测试账户默认配置的完整性"""
        account_defaults = DefaultConfig.get_account_defaults()

        # 验证包含所有必要的账户参数
        required_account_keys = ["account_equity", "api_key", "api_secret"]

        for key in required_account_keys:
            self.assertIn(key, account_defaults)

        # 验证不包含非账户参数
        non_account_keys = ["symbols", "risk_percent", "telegram_token", "log_level"]

        for key in non_account_keys:
            self.assertNotIn(key, account_defaults)

    def test_system_defaults_completeness(self):
        """测试系统默认配置的完整性"""
        system_defaults = DefaultConfig.get_system_defaults()

        # 验证包含所有必要的系统参数
        required_system_keys = [
            "log_level",
            "log_dir",
            "trades_dir",
            "use_binance_testnet",
            "request_timeout",
            "max_retries",
        ]

        for key in required_system_keys:
            self.assertIn(key, system_defaults)

        # 验证不包含非系统参数
        non_system_keys = ["symbols", "risk_percent", "api_key", "telegram_token"]

        for key in non_system_keys:
            self.assertNotIn(key, system_defaults)

    def test_default_values_types(self):
        """测试默认值的数据类型"""
        defaults = DefaultConfig.get_defaults()

        # 验证数据类型
        self.assertIsInstance(defaults["symbols"], list)
        self.assertIsInstance(defaults["risk_percent"], float)
        self.assertIsInstance(defaults["fast_ma"], int)
        self.assertIsInstance(defaults["slow_ma"], int)
        self.assertIsInstance(defaults["atr_period"], int)
        self.assertIsInstance(defaults["check_interval"], int)
        self.assertIsInstance(defaults["test_mode"], bool)
        self.assertIsInstance(defaults["account_equity"], float)
        self.assertIsInstance(defaults["api_key"], str)
        self.assertIsInstance(defaults["api_secret"], str)
        self.assertIsInstance(defaults["telegram_token"], str)
        self.assertIsInstance(defaults["telegram_chat_id"], str)
        self.assertIsInstance(defaults["log_level"], str)
        self.assertIsInstance(defaults["log_dir"], str)
        self.assertIsInstance(defaults["trades_dir"], str)
        self.assertIsInstance(defaults["use_binance_testnet"], bool)
        self.assertIsInstance(defaults["request_timeout"], int)
        self.assertIsInstance(defaults["max_retries"], int)
        self.assertIsInstance(defaults["monitoring_enabled"], bool)
        self.assertIsInstance(defaults["monitoring_port"], int)

    def test_default_values_ranges(self):
        """测试默认值的合理范围"""
        defaults = DefaultConfig.get_defaults()

        # 验证数值范围
        self.assertGreater(defaults["risk_percent"], 0)
        self.assertLess(defaults["risk_percent"], 1)
        self.assertGreater(defaults["fast_ma"], 0)
        self.assertGreater(defaults["slow_ma"], defaults["fast_ma"])
        self.assertGreater(defaults["atr_period"], 0)
        self.assertGreater(defaults["check_interval"], 0)
        self.assertGreater(defaults["account_equity"], 0)
        self.assertGreater(defaults["request_timeout"], 0)
        self.assertGreater(defaults["max_retries"], 0)
        self.assertGreater(defaults["monitoring_port"], 0)
        self.assertLess(defaults["monitoring_port"], 65536)  # 有效端口范围

    def test_symbols_list_validity(self):
        """测试交易对列表的有效性"""
        defaults = DefaultConfig.get_defaults()
        symbols = defaults["symbols"]

        # 验证symbols是非空列表
        self.assertIsInstance(symbols, list)
        self.assertGreater(len(symbols), 0)

        # 验证每个symbol都是字符串
        for symbol in symbols:
            self.assertIsInstance(symbol, str)
            self.assertGreater(len(symbol), 0)

        # 验证默认symbols的格式
        self.assertIn("BTCUSDT", symbols)
        self.assertIn("ETHUSDT", symbols)


class TestDefaultConfigEdgeCases(unittest.TestCase):
    """测试默认配置边缘情况 (Test Default Config Edge Cases)"""

    def test_static_method_accessibility(self):
        """测试静态方法的可访问性"""
        # 验证可以直接通过类调用静态方法
        self.assertTrue(callable(DefaultConfig.get_defaults))
        self.assertTrue(callable(DefaultConfig.get_trading_defaults))
        self.assertTrue(callable(DefaultConfig.get_account_defaults))
        self.assertTrue(callable(DefaultConfig.get_system_defaults))

    def test_multiple_calls_independence(self):
        """测试多次调用的独立性"""
        # 多次调用应该返回独立的字典
        defaults1 = DefaultConfig.get_defaults()
        defaults2 = DefaultConfig.get_defaults()

        # 应该是不同的对象
        self.assertIsNot(defaults1, defaults2)

        # 但内容应该相同
        self.assertEqual(defaults1, defaults2)

    def test_configuration_categories_no_overlap(self):
        """测试配置分类无重叠"""
        trading = set(DefaultConfig.get_trading_defaults().keys())
        account = set(DefaultConfig.get_account_defaults().keys())
        system = set(DefaultConfig.get_system_defaults().keys())

        # 验证分类之间没有重叠
        self.assertEqual(len(trading & account), 0)
        self.assertEqual(len(trading & system), 0)
        self.assertEqual(len(account & system), 0)

    def test_all_defaults_covered_by_categories(self):
        """测试所有默认配置都被分类覆盖"""
        all_defaults = set(DefaultConfig.get_defaults().keys())
        trading = set(DefaultConfig.get_trading_defaults().keys())
        account = set(DefaultConfig.get_account_defaults().keys())
        system = set(DefaultConfig.get_system_defaults().keys())

        # 计算分类覆盖的总配置
        categorized = trading | account | system

        # 验证覆盖情况（允许有一些配置不在任何分类中）
        uncategorized = all_defaults - categorized

        # 检查未分类的配置（应该是通知和监控相关的）
        expected_uncategorized = {
            "telegram_token",
            "telegram_chat_id",
            "monitoring_enabled",
            "monitoring_port",
        }

        self.assertEqual(uncategorized, expected_uncategorized)


if __name__ == "__main__":
    unittest.main()
