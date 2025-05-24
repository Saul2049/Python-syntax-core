#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Default Configuration Values (默认配置值)

Centralized default configuration for all trading parameters
"""

from typing import Any, Dict


class DefaultConfig:
    """Default configuration values provider (默认配置值提供器)"""

    @staticmethod
    def get_defaults() -> Dict[str, Any]:
        """
        Get default configuration dictionary

        Returns:
            Dict containing all default configuration values
        """
        return {
            # Trading configuration (交易配置)
            "symbols": ["BTCUSDT", "ETHUSDT"],
            "risk_percent": 0.01,
            "fast_ma": 7,
            "slow_ma": 25,
            "atr_period": 14,
            "check_interval": 60,
            "test_mode": True,
            # Account configuration (账户配置)
            "account_equity": 10000.0,
            "api_key": "",
            "api_secret": "",
            # Notification configuration (通知配置)
            "telegram_token": "",
            "telegram_chat_id": "",
            # System configuration (系统配置)
            "log_level": "INFO",
            "log_dir": "logs",
            "trades_dir": "trades",
            # Network configuration (网络配置)
            "use_binance_testnet": True,
            "request_timeout": 30,
            "max_retries": 3,
            # Monitoring configuration (监控配置)
            "monitoring_enabled": True,
            "monitoring_port": 9090,
        }

    @staticmethod
    def get_trading_defaults() -> Dict[str, Any]:
        """Get only trading-related default values"""
        defaults = DefaultConfig.get_defaults()
        return {
            key: value
            for key, value in defaults.items()
            if key
            in [
                "symbols",
                "risk_percent",
                "fast_ma",
                "slow_ma",
                "atr_period",
                "check_interval",
                "test_mode",
            ]
        }

    @staticmethod
    def get_account_defaults() -> Dict[str, Any]:
        """Get only account-related default values"""
        defaults = DefaultConfig.get_defaults()
        return {
            key: value
            for key, value in defaults.items()
            if key in ["account_equity", "api_key", "api_secret"]
        }

    @staticmethod
    def get_system_defaults() -> Dict[str, Any]:
        """Get only system-related default values"""
        defaults = DefaultConfig.get_defaults()
        return {
            key: value
            for key, value in defaults.items()
            if key
            in [
                "log_level",
                "log_dir",
                "trades_dir",
                "use_binance_testnet",
                "request_timeout",
                "max_retries",
            ]
        }
