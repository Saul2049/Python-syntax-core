#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core Configuration Manager (配置管理器核心模块)

Provides the main TradingConfig class with simplified initialization
"""

import logging
from typing import Any, Dict, Optional

from .defaults import DefaultConfig
from .sources import ConfigSourceLoader
from .utils import merge_dict
from .validators import ConfigValidator

logger = logging.getLogger(__name__)


class TradingConfig:
    """Unified trading configuration manager (统一交易配置管理器)"""

    def __init__(
        self,
        config_file: Optional[str] = None,
        config_yaml: Optional[str] = None,
        env_file: Optional[str] = None,
    ):
        """
        Initialize configuration manager

        Args:
            config_file: INI configuration file path
            config_yaml: YAML configuration file path
            env_file: Environment variables file path
        """
        self.config_data = {}
        self._loader = ConfigSourceLoader()
        self._validator = ConfigValidator()
        self._load_config(config_file, config_yaml, env_file)

    def _load_config(
        self,
        config_file: Optional[str] = None,
        config_yaml: Optional[str] = None,
        env_file: Optional[str] = None,
    ):
        """Load configuration from multiple sources"""
        # Start with defaults
        self.config_data = DefaultConfig.get_defaults()

        # Load from various sources
        self._loader.load_all_sources(self.config_data, config_file, config_yaml, env_file)

        # Validate final configuration
        self._validator.validate(self.config_data)

        logger.info("Configuration loading completed")

    # Trading configuration getters
    def get_symbols(self) -> list:
        """Get trading symbols list"""
        return self.config_data.get("symbols", ["BTCUSDT", "ETHUSDT"])

    def get_risk_percent(self) -> float:
        """Get risk percentage per trade"""
        return self.config_data.get("risk_percent", 0.01)

    def get_fast_ma(self) -> int:
        """Get fast moving average period"""
        return self.config_data.get("fast_ma", 7)

    def get_slow_ma(self) -> int:
        """Get slow moving average period"""
        return self.config_data.get("slow_ma", 25)

    def get_atr_period(self) -> int:
        """Get ATR calculation period"""
        return self.config_data.get("atr_period", 14)

    def get_check_interval(self) -> int:
        """Get check interval in seconds"""
        return self.config_data.get("check_interval", 60)

    def is_test_mode(self) -> bool:
        """Check if running in test mode"""
        return self.config_data.get("test_mode", True)

    # Account configuration getters
    def get_account_equity(self) -> float:
        """Get account equity"""
        return self.config_data.get("account_equity", 10000.0)

    def get_api_credentials(self) -> tuple:
        """Get API credentials"""
        return (self.config_data.get("api_key", ""), self.config_data.get("api_secret", ""))

    def get_telegram_config(self) -> tuple:
        """Get Telegram configuration"""
        return (
            self.config_data.get("telegram_token", ""),
            self.config_data.get("telegram_chat_id", ""),
        )

    # System configuration getters
    def get_log_level(self) -> str:
        """Get logging level"""
        return self.config_data.get("log_level", "INFO")

    def get_log_dir(self) -> str:
        """Get log directory"""
        return self.config_data.get("log_dir", "logs")

    def get_trades_dir(self) -> str:
        """Get trades directory"""
        return self.config_data.get("trades_dir", "trades")

    def use_binance_testnet(self) -> bool:
        """Check if using Binance testnet"""
        return self.config_data.get("use_binance_testnet", True)

    def get_monitoring_port(self) -> int:
        """Get monitoring port"""
        return self.config_data.get("monitoring_port", 9090)

    def is_monitoring_enabled(self) -> bool:
        """Check if monitoring is enabled"""
        return self.config_data.get("monitoring_enabled", True)

    # Generic getters/setters
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        return self.config_data.get(key, default)

    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.config_data[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Get all configuration as dictionary"""
        return self.config_data.copy()

    def merge_config(self, config: Dict[str, Any]):
        """
        Merge external configuration into current configuration

        Args:
            config: Configuration dictionary to merge
        """
        merge_dict(self.config_data, config)
