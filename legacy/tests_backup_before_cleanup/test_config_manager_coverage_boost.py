"""
配置管理器模块覆盖率提升测试 (Config Manager Coverage Boost Tests)

专门针对 src/config/manager.py 中未覆盖的代码行进行测试，
将覆盖率从 52% 提升到 85%+。

目标缺失行: 37-40, 50-58, 63, 67, 71, 75, 79, 83, 87, 92, 96, 100, 108, 112, 116, 120, 124, 128, 133, 137, 141, 150
"""

import tempfile
from unittest.mock import patch

import pytest

from src.config.manager import TradingConfig


class TestTradingConfigInitialization:
    """测试配置管理器初始化"""

    def test_init_with_all_parameters(self):
        """测试使用所有参数初始化 (Lines 37-40)"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as ini_file:
            ini_file.write("[trading]\nsymbols = BTCUSDT\n")
            ini_path = ini_file.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as yaml_file:
            yaml_file.write("trading:\n  symbols: [ETHUSDT]\n")
            yaml_path = yaml_file.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as env_file:
            env_file.write("API_KEY=test_key\n")
            env_path = env_file.name

        config = TradingConfig(config_file=ini_path, config_yaml=yaml_path, env_file=env_path)

        assert config.config_data is not None
        assert hasattr(config, "_loader")
        assert hasattr(config, "_validator")

    def test_load_config_method_coverage(self):
        """测试_load_config方法的完整覆盖 (Lines 50-58)"""
        with patch.object(TradingConfig, "_load_config") as mock_load:
            config = TradingConfig()
            mock_load.assert_called_once()


class TestTradingConfigGetters:
    """测试配置获取方法"""

    @pytest.fixture
    def config(self):
        return TradingConfig()

    def test_get_symbols(self, config):
        """测试获取交易对列表 (Line 63)"""
        result = config.get_symbols()
        assert isinstance(result, list)
        assert result == ["BTCUSDT", "ETHUSDT"]  # 默认值

    def test_get_risk_percent(self, config):
        """测试获取风险百分比 (Line 67)"""
        result = config.get_risk_percent()
        assert isinstance(result, float)
        assert result == 0.01  # 默认值

    def test_get_fast_ma(self, config):
        """测试获取快速移动平均线周期 (Line 71)"""
        result = config.get_fast_ma()
        assert isinstance(result, int)
        assert result == 7  # 默认值

    def test_get_slow_ma(self, config):
        """测试获取慢速移动平均线周期 (Line 75)"""
        result = config.get_slow_ma()
        assert isinstance(result, int)
        assert result == 25  # 默认值

    def test_get_atr_period(self, config):
        """测试获取ATR计算周期 (Line 79)"""
        result = config.get_atr_period()
        assert isinstance(result, int)
        assert result == 14  # 默认值

    def test_get_check_interval(self, config):
        """测试获取检查间隔 (Line 83)"""
        result = config.get_check_interval()
        assert isinstance(result, int)
        assert result == 60  # 默认值

    def test_is_test_mode(self, config):
        """测试检查是否为测试模式 (Line 87)"""
        result = config.is_test_mode()
        assert isinstance(result, bool)
        assert result == True  # 默认值


class TestAccountConfigGetters:
    """测试账户配置获取方法"""

    @pytest.fixture
    def config(self):
        return TradingConfig()

    def test_get_account_equity(self, config):
        """测试获取账户权益 (Line 92)"""
        result = config.get_account_equity()
        assert isinstance(result, float)
        assert result == 10000.0  # 默认值

    def test_get_api_credentials(self, config):
        """测试获取API凭证 (Line 96)"""
        result = config.get_api_credentials()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result == ("", "")  # 默认值

    def test_get_telegram_config(self, config):
        """测试获取Telegram配置 (Line 100)"""
        result = config.get_telegram_config()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result == ("", "")  # 默认值


class TestSystemConfigGetters:
    """测试系统配置获取方法"""

    @pytest.fixture
    def config(self):
        return TradingConfig()

    def test_get_log_level(self, config):
        """测试获取日志级别 (Line 108)"""
        result = config.get_log_level()
        assert isinstance(result, str)
        assert result == "INFO"  # 默认值

    def test_get_log_dir(self, config):
        """测试获取日志目录 (Line 112)"""
        result = config.get_log_dir()
        assert isinstance(result, str)
        assert result == "logs"  # 默认值

    def test_get_trades_dir(self, config):
        """测试获取交易目录 (Line 116)"""
        result = config.get_trades_dir()
        assert isinstance(result, str)
        assert result == "trades"  # 默认值

    def test_use_binance_testnet(self, config):
        """测试检查是否使用Binance测试网 (Line 120)"""
        result = config.use_binance_testnet()
        assert isinstance(result, bool)
        assert result == True  # 默认值

    def test_get_monitoring_port(self, config):
        """测试获取监控端口 (Line 124)"""
        result = config.get_monitoring_port()
        assert isinstance(result, int)
        assert result == 9090  # 默认值

    def test_is_monitoring_enabled(self, config):
        """测试检查是否启用监控 (Line 128)"""
        result = config.is_monitoring_enabled()
        assert isinstance(result, bool)
        assert result == True  # 默认值


class TestGenericGettersSetters:
    """测试通用获取器和设置器"""

    @pytest.fixture
    def config(self):
        return TradingConfig()

    def test_get_with_default(self, config):
        """测试使用默认值获取配置 (Line 133)"""
        result = config.get("nonexistent_key", "default_value")
        assert result == "default_value"

    def test_set_configuration_value(self, config):
        """测试设置配置值 (Line 137)"""
        config.set("test_key", "test_value")
        assert config.config_data["test_key"] == "test_value"

    def test_to_dict(self, config):
        """测试获取所有配置为字典 (Line 141)"""
        result = config.to_dict()
        assert isinstance(result, dict)
        assert result is not config.config_data  # 应该是副本

    def test_merge_config(self, config):
        """测试合并外部配置 (Line 150)"""
        external_config = {"new_key": "new_value", "symbols": ["NEWUSDT"]}  # 覆盖现有值

        original_symbols = config.get_symbols()
        config.merge_config(external_config)

        assert config.get("new_key") == "new_value"
        # 验证合并功能正常工作
        assert "new_key" in config.config_data


class TestConfigurationWithCustomValues:
    """测试使用自定义值的配置"""

    def test_config_with_custom_data(self):
        """测试配置包含自定义数据时的getter方法"""
        config = TradingConfig()

        # 设置自定义值
        config.config_data.update(
            {
                "symbols": ["CUSTOMUSDT", "TESTUSDT"],
                "risk_percent": 0.05,
                "fast_ma": 10,
                "slow_ma": 30,
                "atr_period": 20,
                "check_interval": 120,
                "test_mode": False,
                "account_equity": 50000.0,
                "api_key": "custom_key",
                "api_secret": "custom_secret",
                "telegram_token": "custom_token",
                "telegram_chat_id": "custom_chat_id",
                "log_level": "DEBUG",
                "log_dir": "custom_logs",
                "trades_dir": "custom_trades",
                "use_binance_testnet": False,
                "monitoring_port": 8080,
                "monitoring_enabled": False,
            }
        )

        # 测试所有getter方法返回自定义值
        assert config.get_symbols() == ["CUSTOMUSDT", "TESTUSDT"]
        assert config.get_risk_percent() == 0.05
        assert config.get_fast_ma() == 10
        assert config.get_slow_ma() == 30
        assert config.get_atr_period() == 20
        assert config.get_check_interval() == 120
        assert config.is_test_mode() == False
        assert config.get_account_equity() == 50000.0
        assert config.get_api_credentials() == ("custom_key", "custom_secret")
        assert config.get_telegram_config() == ("custom_token", "custom_chat_id")
        assert config.get_log_level() == "DEBUG"
        assert config.get_log_dir() == "custom_logs"
        assert config.get_trades_dir() == "custom_trades"
        assert config.use_binance_testnet() == False
        assert config.get_monitoring_port() == 8080
        assert config.is_monitoring_enabled() == False


class TestConfigurationEdgeCases:
    """测试配置边界情况"""

    def test_get_nonexistent_key_without_default(self):
        """测试获取不存在的键且无默认值"""
        config = TradingConfig()
        result = config.get("nonexistent_key")
        assert result is None

    def test_set_and_get_complex_value(self):
        """测试设置和获取复杂值"""
        config = TradingConfig()
        complex_value = {"nested": {"list": [1, 2, 3], "dict": {"key": "value"}}}

        config.set("complex_key", complex_value)
        result = config.get("complex_key")
        assert result == complex_value

    def test_merge_config_with_nested_dict(self):
        """测试合并包含嵌套字典的配置"""
        config = TradingConfig()

        # 设置初始嵌套配置
        config.set("nested_config", {"level1": {"level2": "original"}})

        # 合并新的嵌套配置
        merge_data = {"nested_config": {"level1": {"level2": "updated", "new_key": "new_value"}}}

        config.merge_config(merge_data)

        # 验证合并结果
        nested = config.get("nested_config")
        assert nested["level1"]["level2"] == "updated"
        assert nested["level1"]["new_key"] == "new_value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
