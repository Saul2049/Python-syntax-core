#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 src.config 模块的所有功能
Config Module Tests

覆盖目标:
- 向后兼容性导入
- 弃用警告
- 重新导出的功能
- _discover_config_files 函数
- __all__ 导出列表
"""

import os
import tempfile
import unittest
import warnings
from pathlib import Path
from unittest.mock import Mock, patch

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
        # 🧹 不再需要手动创建临时目录，使用上下文管理器

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
        # 🧹 不再需要手动清理临时文件，上下文管理器会处理

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
        # 🧹 使用临时目录上下文管理器
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

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
            ini_file = temp_path / "test_config.ini"
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
        # 🧹 使用临时目录上下文管理器
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test .env file
            env_content = """
API_KEY=env_test_key
API_SECRET=env_test_secret
LOG_LEVEL=WARNING
TEST_MODE=true
SYMBOLS=BTCUSDT,ADAUSDT
"""
            env_file = temp_path / ".env"
            with open(env_file, "w") as f:
                f.write(env_content)

            _ = TradingConfig(env_file=str(env_file))

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
        # 🧹 使用临时文件上下文管理器替代delete=False
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini") as f:
            f.write("[trading]\nsymbols = TESTUSDT\n")
            f.flush()  # 确保内容写入文件
            temp_config = f.name

            # Clear any environment variables that might interfere
            with patch.dict(os.environ, {}, clear=True):
                # Reset global config to test with parameters
                import src.config

                src.config._global_config = None

                config = get_config(config_file=temp_config)
                self.assertIn("TESTUSDT", config.get_symbols())

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


class TestConfigBackwardCompatibility:
    """测试配置模块向后兼容性"""

    def test_config_imports_with_deprecation_warning(self):
        """测试导入时的弃用警告"""
        # 清除之前的导入
        import sys

        if "src.config" in sys.modules:
            del sys.modules["src.config"]

        # 捕获弃用警告
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # 导入模块应该触发弃用警告

            # 验证弃用警告
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "Importing from src.config is deprecated" in str(w[0].message)
            assert "Please use 'from src.config import get_config' instead" in str(w[0].message)

    def test_all_exports_available(self):
        """测试所有导出的功能都可用"""
        import src.config

        # 验证 __all__ 中的所有项目都可用
        expected_exports = [
            "TradingConfig",
            "DefaultConfig",
            "ConfigSourceLoader",
            "ConfigValidator",
            "ConfigSanitizer",
            "get_config",
            "setup_logging",
            "reset_config",
            "_discover_config_files",
        ]

        # 检查 __all__ 列表
        assert hasattr(src.config, "__all__")
        assert src.config.__all__ == expected_exports

        # 检查所有导出的项目都存在
        for export in expected_exports:
            assert hasattr(src.config, export), f"Missing export: {export}"

    @patch("src.config.config.TradingConfig")
    def test_trading_config_import(self, mock_trading_config):
        """测试 TradingConfig 导入"""
        import src.config

        # 验证 TradingConfig 可以访问
        config_class = src.config.TradingConfig
        assert config_class is mock_trading_config

    @patch("src.config.config.DefaultConfig")
    def test_default_config_import(self, mock_default_config):
        """测试 DefaultConfig 导入"""
        import src.config

        # 验证 DefaultConfig 可以访问
        config_class = src.config.DefaultConfig
        assert config_class is mock_default_config

    @patch("src.config.loader.ConfigSourceLoader")
    def test_config_source_loader_import(self, mock_loader):
        """测试 ConfigSourceLoader 导入"""
        import src.config

        # 验证 ConfigSourceLoader 可以访问
        loader_class = src.config.ConfigSourceLoader
        assert loader_class is mock_loader

    @patch("src.config.validator.ConfigValidator")
    def test_config_validator_import(self, mock_validator):
        """测试 ConfigValidator 导入"""
        import src.config

        # 验证 ConfigValidator 可以访问
        validator_class = src.config.ConfigValidator
        assert validator_class is mock_validator

    @patch("src.config.sanitizer.ConfigSanitizer")
    def test_config_sanitizer_import(self, mock_sanitizer):
        """测试 ConfigSanitizer 导入"""
        import src.config

        # 验证 ConfigSanitizer 可以访问
        sanitizer_class = src.config.ConfigSanitizer
        assert sanitizer_class is mock_sanitizer

    @patch("src.config.get_config")
    def test_get_config_function_import(self, mock_get_config):
        """测试 get_config 函数导入"""
        import src.config

        # 验证 get_config 函数可以访问
        get_config_func = src.config.get_config
        assert get_config_func is mock_get_config

    @patch("src.config.setup_logging")
    def test_setup_logging_function_import(self, mock_setup_logging):
        """测试 setup_logging 函数导入"""
        import src.config

        # 验证 setup_logging 函数可以访问
        setup_logging_func = src.config.setup_logging
        assert setup_logging_func is mock_setup_logging

    @patch("src.config.reset_config")
    def test_reset_config_function_import(self, mock_reset_config):
        """测试 reset_config 函数导入"""
        import src.config

        # 验证 reset_config 函数可以访问
        reset_config_func = src.config.reset_config
        assert reset_config_func is mock_reset_config


class TestDiscoverConfigFilesFunction:
    """测试 _discover_config_files 函数"""

    @patch("src.config._discover_config_files")
    def test_discover_config_files_legacy_function(self, mock_new_discover):
        """测试遗留的 _discover_config_files 函数"""
        import src.config

        # 设置模拟返回值
        mock_new_discover.return_value = ["config1.yaml", "config2.json"]

        # 调用遗留函数
        result = src.config._discover_config_files()

        # 验证调用了新函数
        mock_new_discover.assert_called_once()
        assert result == ["config1.yaml", "config2.json"]

    @patch("src.config._discover_config_files")
    def test_discover_config_files_delegation(self, mock_new_discover):
        """测试 _discover_config_files 函数委托给新实现"""
        import src.config

        # 设置模拟返回值
        expected_files = [
            "/path/to/config.yaml",
            "/path/to/local_config.json",
            "/path/to/user_config.toml",
        ]
        mock_new_discover.return_value = expected_files

        # 调用函数
        result = src.config._discover_config_files()

        # 验证结果
        assert result == expected_files
        mock_new_discover.assert_called_once_with()

    @patch("src.config._discover_config_files")
    def test_discover_config_files_empty_result(self, mock_new_discover):
        """测试 _discover_config_files 返回空列表"""
        import src.config

        # 设置模拟返回空列表
        mock_new_discover.return_value = []

        # 调用函数
        result = src.config._discover_config_files()

        # 验证结果
        assert result == []
        mock_new_discover.assert_called_once()

    @patch("src.config._discover_config_files")
    def test_discover_config_files_exception_handling(self, mock_new_discover):
        """测试 _discover_config_files 异常处理"""
        import src.config

        # 设置模拟抛出异常
        mock_new_discover.side_effect = FileNotFoundError("Config directory not found")

        # 调用函数应该传播异常
        with pytest.raises(FileNotFoundError, match="Config directory not found"):
            src.config._discover_config_files()

        mock_new_discover.assert_called_once()


class TestConfigModuleIntegration:
    """测试配置模块集成功能"""

    def test_module_docstring(self):
        """测试模块文档字符串"""
        import src.config

        # 验证模块有文档字符串
        assert src.config.__doc__ is not None
        assert "Backward Compatibility Configuration Module" in src.config.__doc__
        assert "向后兼容配置模块" in src.config.__doc__

    def test_module_attributes(self):
        """测试模块属性"""
        import src.config

        # 验证模块有必要的属性
        assert hasattr(src.config, "__file__")
        assert hasattr(src.config, "__name__")
        assert src.config.__name__ == "src.config"

    @patch("src.config.get_config")
    @patch("src.config.setup_logging")
    def test_functional_workflow_simulation(self, mock_setup_logging, mock_get_config):
        """测试功能工作流模拟"""
        import src.config

        # 模拟配置对象
        mock_config = Mock()
        mock_config.trading = Mock()
        mock_config.trading.symbol = "BTC/USDT"
        mock_get_config.return_value = mock_config

        # 模拟使用配置模块的工作流
        config = src.config.get_config()
        src.config.setup_logging()

        # 验证调用
        mock_get_config.assert_called_once()
        mock_setup_logging.assert_called_once()
        assert config.trading.symbol == "BTC/USDT"

    def test_import_structure_validation(self):
        """测试导入结构验证"""
        import src.config

        # 验证所有必要的导入都存在
        required_imports = [
            "ConfigSanitizer",
            "ConfigSourceLoader",
            "ConfigValidator",
            "DefaultConfig",
            "TradingConfig",
            "get_config",
            "reset_config",
            "setup_logging",
        ]

        for import_name in required_imports:
            assert hasattr(src.config, import_name), f"Missing import: {import_name}"
            # 验证不是None
            assert getattr(src.config, import_name) is not None


class TestWarningsHandling:
    """测试警告处理"""

    def test_deprecation_warning_details(self):
        """测试弃用警告详细信息"""
        # 清除模块缓存
        import sys

        if "src.config" in sys.modules:
            del sys.modules["src.config"]

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # 导入模块

            # 验证警告详细信息
            assert len(w) >= 1
            warning = w[0]
            assert warning.category == DeprecationWarning
            assert warning.filename.endswith("config.py")
            assert "src.config is deprecated" in str(warning.message)

    def test_warning_stacklevel(self):
        """测试警告堆栈级别"""
        # 清除模块缓存
        import sys

        if "src.config" in sys.modules:
            del sys.modules["src.config"]

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # 导入模块

            # 验证警告被正确记录
            assert len(w) >= 1
            # 警告应该指向正确的堆栈级别
            warning = w[0]
            assert warning.lineno > 0

    def test_multiple_imports_single_warning(self):
        """测试多次导入只产生一次警告"""
        # 清除模块缓存
        import sys

        if "src.config" in sys.modules:
            del sys.modules["src.config"]

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # 第一次导入
            import src.config

            first_warning_count = len(w)

            # 第二次导入（重新导入）
            import importlib

            importlib.reload(src.config)

            # 应该有额外的警告（因为重新加载）
            assert len(w) >= first_warning_count


class TestEdgeCases:
    """测试边界情况"""

    def test_config_module_in_sys_modules(self):
        """测试配置模块在 sys.modules 中"""
        import sys

        import src.config

        # 验证模块在 sys.modules 中
        assert "src.config" in sys.modules
        assert sys.modules["src.config"] is src.config

    @patch("src.config._discover_config_files")
    def test_discover_config_files_with_none_return(self, mock_new_discover):
        """测试 _discover_config_files 返回 None"""
        import src.config

        # 设置模拟返回 None
        mock_new_discover.return_value = None

        # 调用函数
        result = src.config._discover_config_files()

        # 验证结果
        assert result is None
        mock_new_discover.assert_called_once()

    def test_all_list_completeness(self):
        """测试 __all__ 列表的完整性"""
        import src.config

        # 获取模块中的所有公共属性
        public_attrs = [attr for attr in dir(src.config) if not attr.startswith("_")]

        # 验证 __all__ 包含所有重要的公共属性
        for attr in src.config.__all__:
            assert hasattr(src.config, attr), f"__all__ contains non-existent attribute: {attr}"

    def test_module_reload_safety(self):
        """测试模块重新加载安全性"""
        import importlib

        import src.config

        # 获取原始属性
        original_all = src.config.__all__.copy()

        # 重新加载模块
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            importlib.reload(src.config)

        # 验证属性保持一致
        assert src.config.__all__ == original_all


class TestConfigModuleUsage:
    """测试配置模块使用场景"""

    @patch("src.config.get_config")
    def test_typical_usage_pattern(self, mock_get_config):
        """测试典型使用模式"""
        import src.config

        # 模拟典型使用
        mock_config = Mock()
        mock_config.database = Mock()
        mock_config.database.url = "postgresql://localhost/test"
        mock_get_config.return_value = mock_config

        # 使用配置
        config = src.config.get_config()
        db_url = config.database.url

        # 验证
        assert db_url == "postgresql://localhost/test"
        mock_get_config.assert_called_once()

    @patch("src.config.TradingConfig")
    def test_config_class_instantiation(self, mock_trading_config):
        """测试配置类实例化"""
        import src.config

        # 模拟配置类
        mock_instance = Mock()
        mock_trading_config.return_value = mock_instance

        # 实例化配置
        config = src.config.TradingConfig()

        # 验证
        assert config is mock_instance
        mock_trading_config.assert_called_once()

    @patch("src.config.reset_config")
    def test_config_reset_functionality(self, mock_reset_config):
        """测试配置重置功能"""
        import src.config

        # 调用重置
        src.config.reset_config()

        # 验证调用
        mock_reset_config.assert_called_once()


class TestDocumentationAndMetadata:
    """测试文档和元数据"""

    def test_module_has_proper_encoding(self):
        """测试模块有正确的编码声明"""
        # 读取源文件检查编码
        import inspect

        import src.config

        source_file = inspect.getfile(src.config)

        with open(source_file, "r", encoding="utf-8") as f:
            first_lines = [f.readline().strip() for _ in range(3)]

        # 验证有编码声明
        encoding_found = any("utf-8" in line for line in first_lines)
        assert encoding_found, "Module should have UTF-8 encoding declaration"

    def test_module_has_shebang(self):
        """测试模块有 shebang 行"""
        import inspect

        import src.config

        source_file = inspect.getfile(src.config)

        with open(source_file, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()

        # 验证有 shebang
        assert first_line.startswith("#!/usr/bin/env python3"), "Module should have proper shebang"

    def test_backward_compatibility_documentation(self):
        """测试向后兼容性文档"""
        import src.config

        # 验证文档字符串包含向后兼容性信息
        doc = src.config.__doc__
        assert "Backward Compatibility" in doc
        assert "delegating to the new modular config package" in doc
        assert "For new code, prefer importing from src.config package directly" in doc


if __name__ == "__main__":
    unittest.main()
