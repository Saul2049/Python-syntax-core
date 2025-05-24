#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Sources Module (配置源模块)

Handle loading configuration from multiple sources
"""

import logging
import os
from configparser import ConfigParser
from pathlib import Path
from typing import Dict, Optional

from .utils import merge_dict

logger = logging.getLogger(__name__)


class ConfigSourceLoader:
    """配置源加载器"""

    def load_all_sources(
        self,
        config_data: Dict,
        config_file: Optional[str] = None,
        config_yaml: Optional[str] = None,
        env_file: Optional[str] = None,
    ):
        """从多个源加载配置"""
        # 1. Load INI configuration file
        if config_file and Path(config_file).exists():
            self._load_ini_config(config_data, config_file)
            logger.info(f"Loaded INI config: {config_file}")

        # 2. Load YAML configuration file
        if config_yaml and Path(config_yaml).exists():
            self._load_yaml_config(config_data, config_yaml)
            logger.info(f"Loaded YAML config: {config_yaml}")

        # 3. Load environment file first
        if env_file and Path(env_file).exists():
            self._load_env_file(env_file)
            logger.info(f"Loaded env file: {env_file}")

        # 4. Load environment variables (highest priority)
        self._load_env_vars(config_data)

    def _load_ini_config(self, config_data: Dict, config_file: str):
        """Load INI configuration file"""
        try:
            config = ConfigParser()
            config.read(config_file, encoding="utf-8")

            # Load different sections
            self._load_trading_section(config_data, config)
            self._load_account_section(config_data, config)
            self._load_system_section(config_data, config)

        except Exception as e:
            logger.error(f"Failed to load INI config: {e}")

    def _load_trading_section(self, config_data: Dict, config: ConfigParser):
        """Load trading section from INI config"""
        if not config.has_section("trading"):
            return

        trading = config["trading"]
        if "symbols" in trading:
            config_data["symbols"] = [s.strip() for s in trading["symbols"].split(",")]
        if "risk_percent" in trading:
            config_data["risk_percent"] = trading.getfloat("risk_percent")
        if "fast_ma" in trading:
            config_data["fast_ma"] = trading.getint("fast_ma")
        if "slow_ma" in trading:
            config_data["slow_ma"] = trading.getint("slow_ma")
        if "test_mode" in trading:
            config_data["test_mode"] = trading.getboolean("test_mode")

    def _load_account_section(self, config_data: Dict, config: ConfigParser):
        """Load account section from INI config"""
        if not config.has_section("account"):
            return

        account = config["account"]
        if "equity" in account:
            config_data["account_equity"] = account.getfloat("equity")
        if "api_key" in account:
            config_data["api_key"] = account["api_key"]
        if "api_secret" in account:
            config_data["api_secret"] = account["api_secret"]

    def _load_system_section(self, config_data: Dict, config: ConfigParser):
        """Load system section from INI config"""
        if not config.has_section("system"):
            return

        system = config["system"]
        if "log_level" in system:
            config_data["log_level"] = system["log_level"]
        if "log_dir" in system:
            config_data["log_dir"] = system["log_dir"]

    def _load_yaml_config(self, config_data: Dict, config_yaml: str):
        """Load YAML configuration file"""
        try:
            import yaml

            with open(config_yaml, "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f)
                if yaml_data:
                    self._merge_yaml_data(config_data, yaml_data)
        except ImportError:
            logger.warning("PyYAML not installed, skipping YAML config loading")
        except Exception as e:
            logger.error(f"Failed to load YAML config: {e}")

    def _merge_yaml_data(self, config_data: Dict, yaml_data: Dict):
        """Merge YAML data into config, handling nested structures"""
        # Define section processors
        section_processors = {
            "trading": self._merge_trading_section,
            "account": self._merge_account_section,
            "system": self._merge_system_section,
            "monitoring": self._merge_monitoring_section,
            "notification": self._merge_notification_section,
            "telegram": self._merge_notification_section,  # Handle both notification and telegram
            "network": self._merge_network_section,
        }

        # Process structured sections
        for section_name, processor in section_processors.items():
            if section_name in yaml_data:
                processor(config_data, yaml_data[section_name])

        # Process direct top-level keys
        self._merge_direct_keys(config_data, yaml_data)

    def _merge_trading_section(self, config_data: Dict, trading: Dict):
        """Merge trading section from YAML data"""
        trading_mappings = {
            "symbols": "symbols",
            "risk_percent": "risk_percent",
            "fast_ma": "fast_ma",
            "slow_ma": "slow_ma",
            "test_mode": "test_mode",
            "atr_period": "atr_period",
            "check_interval": "check_interval",
        }

        for yaml_key, config_key in trading_mappings.items():
            if yaml_key in trading:
                config_data[config_key] = trading[yaml_key]

    def _merge_account_section(self, config_data: Dict, account: Dict):
        """Merge account section from YAML data"""
        account_mappings = {
            "equity": "account_equity",
            "api_key": "api_key",
            "api_secret": "api_secret",
        }

        for yaml_key, config_key in account_mappings.items():
            if yaml_key in account:
                config_data[config_key] = account[yaml_key]

    def _merge_system_section(self, config_data: Dict, system: Dict):
        """Merge system section from YAML data"""
        system_mappings = {
            "log_level": "log_level",
            "log_dir": "log_dir",
            "trades_dir": "trades_dir",
        }

        for yaml_key, config_key in system_mappings.items():
            if yaml_key in system:
                config_data[config_key] = system[yaml_key]

    def _merge_monitoring_section(self, config_data: Dict, monitoring: Dict):
        """Merge monitoring section from YAML data"""
        monitoring_mappings = {
            "enabled": "monitoring_enabled",
            "port": "monitoring_port",
        }

        for yaml_key, config_key in monitoring_mappings.items():
            if yaml_key in monitoring:
                config_data[config_key] = monitoring[yaml_key]

    def _merge_notification_section(self, config_data: Dict, notification: Dict):
        """Merge notification/telegram section from YAML data"""
        notification_mappings = {
            "token": "telegram_token",
            "chat_id": "telegram_chat_id",
        }

        for yaml_key, config_key in notification_mappings.items():
            if yaml_key in notification:
                config_data[config_key] = notification[yaml_key]

    def _merge_network_section(self, config_data: Dict, network: Dict):
        """Merge network section from YAML data"""
        network_mappings = {
            "use_binance_testnet": "use_binance_testnet",
            "request_timeout": "request_timeout",
            "max_retries": "max_retries",
        }

        for yaml_key, config_key in network_mappings.items():
            if yaml_key in network:
                config_data[config_key] = network[yaml_key]

    def _merge_direct_keys(self, config_data: Dict, yaml_data: Dict):
        """Merge direct top-level keys that match config keys"""
        direct_keys = [
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

        for key in direct_keys:
            if key in yaml_data:
                config_data[key] = yaml_data[key]

    def _load_env_file(self, env_file: str):
        """Load environment variables file"""
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()
        except Exception as e:
            logger.error(f"Failed to load environment file: {e}")

    def _load_env_vars(self, config_data: Dict):
        """Load configuration from environment variables"""
        env_mappings = {
            "SYMBOLS": ("symbols", lambda x: [s.strip() for s in x.split(",")]),
            "RISK_PERCENT": ("risk_percent", float),
            "FAST_MA": ("fast_ma", int),
            "SLOW_MA": ("slow_ma", int),
            "ATR_PERIOD": ("atr_period", int),
            "CHECK_INTERVAL": ("check_interval", int),
            "TEST_MODE": ("test_mode", lambda x: x.lower() in ["true", "1", "yes"]),
            "ACCOUNT_EQUITY": ("account_equity", float),
            "API_KEY": ("api_key", str),
            "API_SECRET": ("api_secret", str),
            "TG_TOKEN": ("telegram_token", str),
            "TG_CHAT_ID": ("telegram_chat_id", str),
            "LOG_LEVEL": ("log_level", str),
            "LOG_DIR": ("log_dir", str),
            "TRADES_DIR": ("trades_dir", str),
            "USE_BINANCE_TESTNET": (
                "use_binance_testnet",
                lambda x: x.lower() in ["true", "1", "yes"],
            ),
            "REQUEST_TIMEOUT": ("request_timeout", int),
            "MAX_RETRIES": ("max_retries", int),
            "MONITORING_ENABLED": (
                "monitoring_enabled",
                lambda x: x.lower() in ["true", "1", "yes"],
            ),
            "MONITORING_PORT": ("monitoring_port", int),
        }

        for env_key, (config_key, converter) in env_mappings.items():
            env_value = os.environ.get(env_key)
            if env_value is not None:
                try:
                    config_data[config_key] = converter(env_value)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid env var {env_key}={env_value}: {e}")

    def merge_external_config(self, config_data: Dict, external_config: Dict):
        """
        Merge external configuration into main config

        Args:
            config_data: Main configuration dictionary
            external_config: External configuration to merge
        """
        merge_dict(config_data, external_config)
