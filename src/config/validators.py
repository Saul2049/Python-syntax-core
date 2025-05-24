#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Validators (配置验证器)

Validates configuration parameters to ensure they are correct and safe
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Configuration validator (配置验证器)"""

    def validate(self, config_data: Dict[str, Any]) -> bool:
        """
        Validate all configuration parameters

        Args:
            config_data: Configuration dictionary to validate

        Returns:
            True if validation passes, raises exception otherwise
        """
        self._validate_trading_config(config_data)
        self._validate_account_config(config_data)
        self._validate_system_config(config_data)
        self._validate_network_config(config_data)

        logger.info("Configuration validation completed successfully")
        return True

    def _validate_trading_config(self, config_data: Dict[str, Any]):
        """Validate trading configuration parameters"""
        self._validate_symbols(config_data)
        self._validate_risk_percent(config_data)
        self._validate_moving_averages(config_data)
        self._validate_atr_period(config_data)
        self._validate_check_interval(config_data)

    def _validate_symbols(self, config_data: Dict[str, Any]):
        """Validate symbols configuration"""
        symbols = config_data.get("symbols", [])
        if not isinstance(symbols, list) or not symbols:
            raise ValueError("symbols must be a non-empty list")

        for symbol in symbols:
            if not isinstance(symbol, str) or not symbol.strip():
                raise ValueError(f"Invalid symbol: {symbol}")

    def _validate_risk_percent(self, config_data: Dict[str, Any]):
        """Validate risk percent configuration"""
        risk_percent = config_data.get("risk_percent", 0.01)
        if not isinstance(risk_percent, (int, float)) or risk_percent <= 0 or risk_percent > 1:
            raise ValueError("risk_percent must be between 0 and 1")

    def _validate_moving_averages(self, config_data: Dict[str, Any]):
        """Validate moving average period configuration"""
        fast_ma = config_data.get("fast_ma", 7)
        slow_ma = config_data.get("slow_ma", 25)

        if not isinstance(fast_ma, int) or fast_ma <= 0:
            raise ValueError("fast_ma must be a positive integer")

        if not isinstance(slow_ma, int) or slow_ma <= 0:
            raise ValueError("slow_ma must be a positive integer")

        if fast_ma >= slow_ma:
            raise ValueError("fast_ma must be less than slow_ma")

    def _validate_atr_period(self, config_data: Dict[str, Any]):
        """Validate ATR period configuration"""
        atr_period = config_data.get("atr_period", 14)
        if not isinstance(atr_period, int) or atr_period <= 0:
            raise ValueError("atr_period must be a positive integer")

    def _validate_check_interval(self, config_data: Dict[str, Any]):
        """Validate check interval configuration"""
        check_interval = config_data.get("check_interval", 60)
        if not isinstance(check_interval, int) or check_interval <= 0:
            raise ValueError("check_interval must be a positive integer")

    def _validate_account_config(self, config_data: Dict[str, Any]):
        """Validate account configuration parameters"""
        # Validate account equity
        account_equity = config_data.get("account_equity", 10000.0)
        if not isinstance(account_equity, (int, float)) or account_equity <= 0:
            raise ValueError("account_equity must be a positive number")

        # API credentials can be empty strings (for testing), but must be strings
        api_key = config_data.get("api_key", "")
        api_secret = config_data.get("api_secret", "")

        if not isinstance(api_key, str):
            raise ValueError("api_key must be a string")

        if not isinstance(api_secret, str):
            raise ValueError("api_secret must be a string")

    def _validate_system_config(self, config_data: Dict[str, Any]):
        """Validate system configuration parameters"""
        # Validate log level
        log_level = config_data.get("log_level", "INFO")
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        if not isinstance(log_level, str) or log_level.upper() not in valid_log_levels:
            raise ValueError(f"log_level must be one of: {valid_log_levels}")

        # Normalize log level to uppercase
        config_data["log_level"] = log_level.upper()

        # Validate directories (can be strings, will be created if needed)
        log_dir = config_data.get("log_dir", "logs")
        trades_dir = config_data.get("trades_dir", "trades")

        if not isinstance(log_dir, str) or not log_dir.strip():
            raise ValueError("log_dir must be a non-empty string")

        if not isinstance(trades_dir, str) or not trades_dir.strip():
            raise ValueError("trades_dir must be a non-empty string")

    def _validate_network_config(self, config_data: Dict[str, Any]):
        """Validate network configuration parameters"""
        # Validate timeout
        request_timeout = config_data.get("request_timeout", 30)
        if not isinstance(request_timeout, int) or request_timeout <= 0:
            raise ValueError("request_timeout must be a positive integer")

        # Validate max retries
        max_retries = config_data.get("max_retries", 3)
        if not isinstance(max_retries, int) or max_retries < 0:
            raise ValueError("max_retries must be a non-negative integer")

        # Validate monitoring port
        monitoring_port = config_data.get("monitoring_port", 9090)
        if not isinstance(monitoring_port, int) or not (1024 <= monitoring_port <= 65535):
            raise ValueError("monitoring_port must be between 1024 and 65535")

    def _validate_telegram_config(self, config_data: Dict[str, Any]):
        """Validate Telegram configuration parameters"""
        telegram_token = config_data.get("telegram_token", "")
        telegram_chat_id = config_data.get("telegram_chat_id", "")

        # Both can be empty (notifications disabled), but must be strings
        if not isinstance(telegram_token, str):
            raise ValueError("telegram_token must be a string")

        if not isinstance(telegram_chat_id, str):
            raise ValueError("telegram_chat_id must be a string")

        # If one is provided, both should be provided
        if bool(telegram_token) != bool(telegram_chat_id):
            logger.warning(
                "Both telegram_token and telegram_chat_id should be provided for notifications"
            )


class ConfigSanitizer:
    """Configuration sanitizer (配置清理器)"""

    @staticmethod
    def sanitize(config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize configuration data

        Args:
            config_data: Raw configuration data

        Returns:
            Sanitized configuration data
        """
        # Create a copy to avoid modifying original
        sanitized = config_data.copy()

        # Strip whitespace from string values
        for key, value in sanitized.items():
            if isinstance(value, str):
                sanitized[key] = value.strip()
            elif isinstance(value, list):
                # For lists of strings (like symbols), strip each element
                if all(isinstance(item, str) for item in value):
                    sanitized[key] = [item.strip() for item in value]

        # Ensure symbols are uppercase
        if "symbols" in sanitized:
            sanitized["symbols"] = [s.upper() for s in sanitized["symbols"]]

        return sanitized
