#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backward Compatibility Configuration Module
向后兼容配置模块

Configuration Package (配置包)

Unified configuration management with modular architecture

Note: This module provides backward compatibility with legacy configuration
interfaces. Some legacy functions may be deprecated in future versions.
"""

import logging
import warnings
from pathlib import Path
from typing import Optional

from .defaults import DefaultConfig
from .manager import TradingConfig
from .sources import ConfigSourceLoader
from .validators import ConfigSanitizer, ConfigValidator

# Issue deprecation warning
warnings.warn(
    "src.config is deprecated. Please use the new configuration system.",
    DeprecationWarning,
    stacklevel=2,
)

# Module-level logger
logger = logging.getLogger(__name__)

# Global configuration instance
_global_config: Optional[TradingConfig] = None


def get_config(
    config_file: Optional[str] = None,
    config_yaml: Optional[str] = None,
    env_file: Optional[str] = None,
    use_cache: bool = True,
) -> TradingConfig:
    """
    Get configuration instance with automatic file discovery

    Args:
        config_file: INI configuration file path
        config_yaml: YAML configuration file path
        env_file: Environment variables file path
        use_cache: Whether to use cached configuration instance

    Returns:
        TradingConfig instance
    """
    global _global_config

    # Return cached instance if available and requested
    if use_cache and _global_config is not None:
        return _global_config

    # Auto-discover config files if not specified
    if not any([config_file, config_yaml, env_file]):
        config_file, config_yaml, env_file = _discover_config_files()

    # Create new configuration instance
    _global_config = TradingConfig(
        config_file=config_file,
        config_yaml=config_yaml,
        env_file=env_file,
    )

    return _global_config


def _discover_config_files() -> tuple:
    """
    Discover configuration files in common locations

    Note: This function is deprecated and will be removed in future versions.
    Use the new configuration discovery mechanism instead.

    Returns:
        Tuple of (config_file, config_yaml, env_file) paths
    """
    config_file = None
    config_yaml = None
    env_file = None

    # Search for config files in order of preference
    search_paths = [".", "config", "../config"]

    for search_path in search_paths:
        path = Path(search_path)
        if not path.exists():
            continue

        if config_file is None:
            config_file = _find_ini_file(path)

        if config_yaml is None:
            config_yaml = _find_yaml_file(path)

        if env_file is None:
            env_file = _find_env_file(path)

    return config_file, config_yaml, env_file


def _find_ini_file(path: Path) -> Optional[str]:
    """在指定路径查找INI配置文件"""
    for ini_name in ["config.ini", "trading.ini", "app.ini"]:
        ini_path = path / ini_name
        if ini_path.exists():
            return str(ini_path)
    return None


def _find_yaml_file(path: Path) -> Optional[str]:
    """在指定路径查找YAML配置文件"""
    for yaml_name in ["config.yaml", "config.yml", "trading.yaml"]:
        yaml_path = path / yaml_name
        if yaml_path.exists():
            return str(yaml_path)
    return None


def _find_env_file(path: Path) -> Optional[str]:
    """在指定路径查找环境变量文件"""
    for env_name in [".env", "trading.env", "app.env"]:
        env_path = path / env_name
        if env_path.exists():
            return str(env_path)
    return None


def setup_logging(config: Optional[TradingConfig] = None):
    """
    Setup logging based on configuration

    Args:
        config: Configuration instance (uses global if None)
    """
    if config is None:
        config = get_config()

    log_level = config.get_log_level()
    log_dir = config.get_log_dir()

    # Create log directory
    Path(log_dir).mkdir(exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(Path(log_dir) / "trading.log"), logging.StreamHandler()],
    )

    logger.info(f"Logging configured: level={log_level}, dir={log_dir}")


def reset_config():
    """Reset global configuration instance"""
    global _global_config
    _global_config = None


# Export main classes and functions
__all__ = [
    "TradingConfig",
    "DefaultConfig",
    "ConfigSourceLoader",
    "ConfigValidator",
    "ConfigSanitizer",
    "get_config",
    "setup_logging",
    "reset_config",
]
