#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backward Compatibility Configuration Module (向后兼容配置模块)

This module maintains backward compatibility while delegating to the new modular config package.
For new code, prefer importing from src.config package directly.
"""

import warnings

from src.config import (
    ConfigSanitizer,
    ConfigSourceLoader,
    ConfigValidator,
    DefaultConfig,
    TradingConfig,
    get_config,
    reset_config,
    setup_logging,
)

# Issue deprecation warning
warnings.warn(
    "Importing from src.config is deprecated. "
    "Please use 'from src.config import get_config' instead.",
    DeprecationWarning,
    stacklevel=2,
)


# Legacy function names for backward compatibility
def _discover_config_files():
    """Legacy function - use src.config._discover_config_files instead"""
    from src.config import _discover_config_files as new_discover

    return new_discover()


# Export everything for backward compatibility
__all__ = [
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
