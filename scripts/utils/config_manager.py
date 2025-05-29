#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器 - 读取和管理配置信息
Configuration Manager - Read and manage configuration settings
"""

import configparser
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger("config_manager")


class ConfigManager:
    """配置管理器类"""

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器

        参数:
            config_file: 配置文件路径，如果为None，则尝试在默认位置查找
        """
        self.config = configparser.ConfigParser()

        # 如果未指定配置文件，则查找默认位置
        if config_file is None:
            # 优先查找项目根目录
            possible_locations = [
                "config.ini",
                "scripts/config.ini",
                "../config.ini",
            ]

            # 尝试所有可能位置
            for location in possible_locations:
                if os.path.exists(location):
                    config_file = location
                    break

        # 如果找到配置文件，则读取它
        if config_file and os.path.exists(config_file):
            try:
                self.config.read(config_file)
                logger.info(f"已加载配置文件: {config_file}")
                self.config_file = config_file
            except Exception as e:
                logger.error(f"读取配置文件时出错: {e}")
                self.config_file = None
        else:
            logger.warning("未找到配置文件，将使用默认设置")
            self.config_file = None

        # 设置默认值
        self._set_defaults()

    def _set_defaults(self):
        """设置默认配置值"""
        # 定义默认配置结构
        default_config = {
            "general": {
                "symbols": "BTC/USDT,ETH/USDT",
                "risk_percent": "0.5",
                "check_interval": "60",
                "test_mode": "true",
            },
            "data_sources": {
                "use_binance_testnet": "true",
                "auto_fallback": "true",
                "min_switch_interval": "300",
            },
            "binance_testnet": {},
            "logging": {"level": "INFO", "log_dir": "logs/stability_test"},
        }

        # 应用默认配置
        self._apply_default_config(default_config)

    def _apply_default_config(self, default_config: dict):
        """应用默认配置"""
        for section_name, section_defaults in default_config.items():
            self._ensure_section_exists(section_name)
            self._apply_section_defaults(section_name, section_defaults)

    def _ensure_section_exists(self, section_name: str):
        """确保配置段存在"""
        if section_name not in self.config:
            self.config[section_name] = {}

    def _apply_section_defaults(self, section_name: str, defaults: dict):
        """为指定段应用默认值"""
        for key, default_value in defaults.items():
            if key not in self.config[section_name]:
                self.config[section_name][key] = default_value

    def get_symbols(self) -> List[str]:
        """获取交易对列表"""
        symbols_str = self.config["general"]["symbols"]
        return [s.strip() for s in symbols_str.split(",")]

    def get_risk_percent(self) -> float:
        """获取风险百分比"""
        return float(self.config["general"]["risk_percent"])

    def get_check_interval(self) -> int:
        """获取检查间隔(秒)"""
        return int(self.config["general"]["check_interval"])

    def is_test_mode(self) -> bool:
        """是否为测试模式"""
        return self.config["general"].getboolean("test_mode")

    def use_binance_testnet(self) -> bool:
        """是否使用币安测试网"""
        return self.config["data_sources"].getboolean("use_binance_testnet")

    def auto_fallback(self) -> bool:
        """数据源不可用时是否自动切换"""
        return self.config["data_sources"].getboolean("auto_fallback")

    def get_min_switch_interval(self) -> int:
        """获取数据源切换的最小间隔(秒)"""
        return int(self.config["data_sources"]["min_switch_interval"])

    def get_binance_testnet_api_key(self) -> Optional[str]:
        """获取币安测试网API密钥"""
        # 优先从环境变量获取
        api_key = os.environ.get("BINANCE_TESTNET_API_KEY")
        if api_key:
            return api_key

        # 否则从配置文件获取
        if "binance_testnet" in self.config and "api_key" in self.config["binance_testnet"]:
            api_key = self.config["binance_testnet"]["api_key"]
            # 检查是否为模板值
            if api_key and api_key != "YOUR_BINANCE_TESTNET_API_KEY":
                return api_key

        return None

    def get_binance_testnet_api_secret(self) -> Optional[str]:
        """获取币安测试网API密钥密钥"""
        # 优先从环境变量获取
        api_secret = os.environ.get("BINANCE_TESTNET_API_SECRET")
        if api_secret:
            return api_secret

        # 否则从配置文件获取
        if "binance_testnet" in self.config and "api_secret" in self.config["binance_testnet"]:
            api_secret = self.config["binance_testnet"]["api_secret"]
            # 检查是否为模板值
            if api_secret and api_secret != "YOUR_BINANCE_TESTNET_API_SECRET":
                return api_secret

        return None

    def get_log_level(self) -> str:
        """获取日志级别"""
        return self.config["logging"]["level"]

    def get_log_dir(self) -> str:
        """获取日志目录"""
        return self.config["logging"]["log_dir"]

    def get_as_dict(self) -> Dict[str, Dict[str, Any]]:
        """将配置转换为字典"""
        result = {}
        for section in self.config.sections():
            result[section] = {}
            for key, value in self.config[section].items():
                result[section][key] = value
        return result

    def save(self, config_file: Optional[str] = None) -> bool:
        """
        保存配置到文件

        参数:
            config_file: 要保存到的文件路径，如果为None则保存到原文件

        返回:
            是否保存成功
        """
        if config_file is None:
            config_file = self.config_file

        if config_file is None:
            logger.error("未指定配置文件，无法保存")
            return False

        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(config_file)), exist_ok=True)

            # 写入文件
            with open(config_file, "w") as f:
                self.config.write(f)

            logger.info(f"配置已保存到: {config_file}")
            return True
        except Exception as e:
            logger.error(f"保存配置文件时出错: {e}")
            return False


# 创建全局配置管理器实例
config_manager = ConfigManager()


# 提供便捷的访问函数
def get_config() -> ConfigManager:
    """获取全局配置管理器实例"""
    return config_manager
