#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强配置管理器 - 支持.env和YAML配置文件
Enhanced Configuration Manager - Supports .env and YAML configuration files
"""

import os
import sys
import logging
import copy
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# 设置日志
logger = logging.getLogger("enhanced_config")

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    logger.warning("未安装PyYAML，将不支持YAML配置")
    YAML_AVAILABLE = False

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    logger.warning("未安装python-dotenv，将不支持.env配置")
    DOTENV_AVAILABLE = False


class EnhancedConfigManager:
    """增强配置管理器类 - 支持多种配置源"""
    
    def __init__(self, 
                 config_yaml: Optional[str] = None, 
                 env_file: Optional[str] = None,
                 config_ini: Optional[str] = None):
        """
        初始化配置管理器
        
        参数:
            config_yaml: YAML配置文件路径
            env_file: .env文件路径
            config_ini: INI配置文件路径(兼容旧版)
        """
        # 配置数据存储
        self.config = {
            "trading": {
                "symbols": ["BTC/USDT", "ETH/USDT"],
                "risk_percent": 0.5,
                "check_interval": 60,
                "test_mode": True,
                "indicators": {
                    "fast_ma": 7,
                    "slow_ma": 25,
                    "atr_period": 14
                }
            },
            "data_sources": {
                "use_binance_testnet": True,
                "auto_fallback": True,
                "min_switch_interval": 300
            },
            "monitoring": {
                "enabled": True,
                "port": 9090,
                "alerts_enabled": True,
                "heartbeat_timeout": 180
            },
            "logging": {
                "level": "INFO",
                "log_dir": "logs/stability_test",
                "console": True,
                "max_file_size_mb": 10,
                "backup_count": 5
            }
        }
        
        self.env_vars = {}
        self.config_file_path = None
        
        # 优先尝试加载.env文件
        if DOTENV_AVAILABLE:
            self._load_dotenv(env_file)
        
        # 尝试加载YAML配置
        if YAML_AVAILABLE:
            yaml_loaded = self._load_yaml_config(config_yaml)
            if yaml_loaded:
                self.config_file_path = config_yaml
                
        # 如果YAML未加载成功且提供了INI文件，尝试加载INI配置(兼容旧版)
        if not self.config_file_path and config_ini:
            try:
                # 导入旧配置管理器
                from scripts.config_manager import ConfigManager
                
                # 加载INI配置
                old_config = ConfigManager(config_ini)
                
                # 转换配置格式
                self._convert_from_ini(old_config)
                
                self.config_file_path = config_ini
                logger.info(f"已加载INI配置文件: {config_ini}")
            except Exception as e:
                logger.error(f"加载INI配置文件时出错: {e}")
        
        # 应用环境变量覆盖配置
        self._apply_env_vars()
        
        logger.info("配置管理器初始化完成")
    
    def _load_dotenv(self, env_file: Optional[str] = None) -> bool:
        """加载.env文件"""
        if not DOTENV_AVAILABLE:
            return False
            
        # 如果未指定.env文件，尝试查找默认位置
        if env_file is None:
            possible_locations = [
                ".env",
                "scripts/.env",
                "../.env",
            ]
            
            for location in possible_locations:
                if os.path.exists(location):
                    env_file = location
                    break
        
        # 如果找到.env文件，加载它
        if env_file and os.path.exists(env_file):
            try:
                load_dotenv(env_file)
                logger.info(f"已加载.env文件: {env_file}")
                
                # 存储所有环境变量
                for key, value in os.environ.items():
                    if key.startswith("BINANCE_") or key in ["LOG_LEVEL", "PRODUCTION"]:
                        self.env_vars[key] = value
                        
                return True
            except Exception as e:
                logger.error(f"加载.env文件时出错: {e}")
                return False
        
        return False
    
    def _load_yaml_config(self, config_yaml: Optional[str] = None) -> bool:
        """加载YAML配置文件"""
        if not YAML_AVAILABLE:
            return False
            
        # 如果未指定YAML文件，尝试查找默认位置
        if config_yaml is None:
            possible_locations = [
                "config.yaml",
                "scripts/config.yaml",
                "../config.yaml",
            ]
            
            for location in possible_locations:
                if os.path.exists(location):
                    config_yaml = location
                    break
        
        # 如果找到YAML文件，加载它
        if config_yaml and os.path.exists(config_yaml):
            try:
                with open(config_yaml, 'r', encoding='utf-8') as f:
                    yaml_config = yaml.safe_load(f)
                
                # 更新配置
                if yaml_config:
                    # 递归合并字典
                    self._deep_update(self.config, yaml_config)
                
                logger.info(f"已加载YAML配置文件: {config_yaml}")
                return True
            except Exception as e:
                logger.error(f"加载YAML配置文件时出错: {e}")
                return False
        
        return False
    
    def _convert_from_ini(self, old_config):
        """从旧版INI配置转换"""
        # 交易配置
        self.config["trading"]["symbols"] = old_config.get_symbols()
        self.config["trading"]["risk_percent"] = old_config.get_risk_percent() 
        self.config["trading"]["check_interval"] = old_config.get_check_interval()
        self.config["trading"]["test_mode"] = old_config.is_test_mode()
        
        # 数据源配置
        self.config["data_sources"]["use_binance_testnet"] = old_config.use_binance_testnet()
        self.config["data_sources"]["min_switch_interval"] = old_config.get_min_switch_interval()
        
        # 日志配置
        self.config["logging"]["level"] = old_config.get_log_level()
        self.config["logging"]["log_dir"] = old_config.get_log_dir()
    
    def _apply_env_vars(self):
        """应用环境变量覆盖配置"""
        # API密钥
        api_key = os.environ.get("BINANCE_TESTNET_API_KEY")
        api_secret = os.environ.get("BINANCE_TESTNET_API_SECRET")
        
        if api_key:
            self.env_vars["BINANCE_TESTNET_API_KEY"] = api_key
        
        if api_secret:
            self.env_vars["BINANCE_TESTNET_API_SECRET"] = api_secret
        
        # 日志级别
        log_level = os.environ.get("LOG_LEVEL")
        if log_level:
            self.config["logging"]["level"] = log_level
        
        # 生产环境标志
        production = os.environ.get("PRODUCTION")
        if production and production.lower() in ["true", "1", "yes"]:
            self.config["trading"]["test_mode"] = False
    
    def _deep_update(self, d: Dict, u: Dict) -> Dict:
        """递归更新字典"""
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._deep_update(d[k], v)
            else:
                d[k] = v
        return d
    
    def get_symbols(self) -> List[str]:
        """获取交易对列表"""
        return self.config["trading"]["symbols"]
    
    def get_risk_percent(self) -> float:
        """获取风险百分比"""
        return float(self.config["trading"]["risk_percent"])
    
    def get_check_interval(self) -> int:
        """获取检查间隔(秒)"""
        return int(self.config["trading"]["check_interval"])
    
    def is_test_mode(self) -> bool:
        """是否为测试模式"""
        return bool(self.config["trading"]["test_mode"])
    
    def get_indicator_params(self) -> Dict[str, int]:
        """获取技术指标参数"""
        return self.config["trading"]["indicators"]
    
    def use_binance_testnet(self) -> bool:
        """是否使用币安测试网"""
        return bool(self.config["data_sources"]["use_binance_testnet"])
    
    def auto_fallback(self) -> bool:
        """数据源不可用时是否自动切换"""
        return bool(self.config["data_sources"]["auto_fallback"])
    
    def get_min_switch_interval(self) -> int:
        """获取数据源切换的最小间隔(秒)"""
        return int(self.config["data_sources"]["min_switch_interval"])
    
    def get_binance_testnet_api_key(self) -> Optional[str]:
        """获取币安测试网API密钥"""
        return self.env_vars.get("BINANCE_TESTNET_API_KEY")
    
    def get_binance_testnet_api_secret(self) -> Optional[str]:
        """获取币安测试网API密钥密钥"""
        return self.env_vars.get("BINANCE_TESTNET_API_SECRET")
    
    def get_log_level(self) -> str:
        """获取日志级别"""
        return self.config["logging"]["level"]
    
    def get_log_dir(self) -> str:
        """获取日志目录"""
        return self.config["logging"]["log_dir"]
    
    def is_console_logging_enabled(self) -> bool:
        """是否启用控制台日志"""
        return bool(self.config["logging"]["console"])
    
    def get_log_file_size(self) -> int:
        """获取日志文件最大大小(MB)"""
        return int(self.config["logging"]["max_file_size_mb"])
    
    def get_log_backup_count(self) -> int:
        """获取保留日志文件数"""
        return int(self.config["logging"]["backup_count"])
    
    def get_as_dict(self) -> Dict[str, Any]:
        """获取完整配置字典"""
        # 创建一个配置副本
        config_copy = copy.deepcopy(self.config)
        
        # 添加环境变量(不包含敏感信息)
        config_copy["env"] = {
            k: v for k, v in self.env_vars.items() 
            if not (k.endswith("_KEY") or k.endswith("_SECRET"))
        }
        
        # 添加API密钥存在标志
        config_copy["env"]["has_api_key"] = "BINANCE_TESTNET_API_KEY" in self.env_vars
        config_copy["env"]["has_api_secret"] = "BINANCE_TESTNET_API_SECRET" in self.env_vars
        
        return config_copy
    
    def save_yaml_config(self, config_yaml: Optional[str] = None) -> bool:
        """保存配置到YAML文件"""
        if not YAML_AVAILABLE:
            logger.error("未安装PyYAML，无法保存YAML配置")
            return False
            
        if config_yaml is None:
            config_yaml = self.config_file_path
        
        if config_yaml is None:
            config_yaml = "config.yaml"
            
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(config_yaml)), exist_ok=True)
            
            # 获取配置副本(不含环境变量信息)
            config_to_save = copy.deepcopy(self.config)
            
            # 写入文件
            with open(config_yaml, 'w', encoding='utf-8') as f:
                yaml.dump(config_to_save, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
                
            logger.info(f"配置已保存到: {config_yaml}")
            return True
        except Exception as e:
            logger.error(f"保存YAML配置文件时出错: {e}")
            return False
    
    def is_monitoring_enabled(self) -> bool:
        """是否启用监控"""
        return bool(self.config["monitoring"]["enabled"])
    
    def get_monitoring_port(self) -> int:
        """获取监控端口"""
        return int(self.config["monitoring"]["port"])
    
    def is_alerts_enabled(self) -> bool:
        """是否启用告警"""
        return bool(self.config["monitoring"]["alerts_enabled"])
    
    def get_heartbeat_timeout(self) -> int:
        """获取心跳超时时间(秒)"""
        return int(self.config["monitoring"]["heartbeat_timeout"])


# 创建全局配置管理器实例
_config_manager = None

def get_config(config_yaml=None, env_file=None, config_ini=None) -> EnhancedConfigManager:
    """获取全局配置管理器实例，如果不存在则创建"""
    global _config_manager
    if _config_manager is None:
        _config_manager = EnhancedConfigManager(
            config_yaml=config_yaml, 
            env_file=env_file,
            config_ini=config_ini
        )
    return _config_manager

def setup_logging():
    """设置日志系统"""
    config = get_config()
    
    # 日志格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_level = getattr(logging, config.get_log_level(), logging.INFO)
    
    # 创建日志目录
    log_dir = config.get_log_dir()
    os.makedirs(log_dir, exist_ok=True)
    
    # 日志文件路径
    log_file = os.path.join(log_dir, "app.log")
    
    # 配置根日志
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 添加控制台处理器
    if config.is_console_logging_enabled():
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(console_handler)
    
    # 添加文件处理器
    try:
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=config.get_log_file_size() * 1024 * 1024,
            backupCount=config.get_log_backup_count()
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(file_handler)
    except Exception as e:
        # 如果不支持RotatingFileHandler，则使用常规FileHandler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(file_handler)
        
        # 记录警告
        root_logger.warning(f"无法初始化RotatingFileHandler: {e}，使用基本FileHandler代替")
    
    # 屏蔽一些库的过多日志
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    return root_logger 