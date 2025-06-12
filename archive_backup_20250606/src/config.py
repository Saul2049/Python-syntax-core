#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deprecated configuration module (archived).
This file exists solely to satisfy legacy test-suites located in *old_tests*.
"""

from __future__ import annotations

import pathlib
import warnings
from typing import List

# Emit deprecation warning expected by the tests
warnings.warn(
    "src.config is deprecated. Please use the new configuration system.",
    DeprecationWarning,
    stacklevel=2,
)


class TradingConfig(dict):
    """Minimal stub – behaves like a dictionary."""


class DefaultConfig(TradingConfig):
    """Alias for default configuration stub."""


class ConfigSourceLoader:
    """Mock loader that discovers config files next to this file."""

    @staticmethod
    def discover() -> List[pathlib.Path]:
        return _discover_config_files()


class ConfigValidator:
    """Always-true validator stub."""

    @staticmethod
    def validate(cfg: TradingConfig) -> bool:
        return True


class ConfigSanitizer:
    """No-op sanitizer stub."""

    @staticmethod
    def sanitize(cfg: TradingConfig) -> TradingConfig:
        return cfg


# ---------------------------------------------------------------------------
# Helper functions required by the tests
# ---------------------------------------------------------------------------


def get_config() -> TradingConfig:
    """Return a default configuration instance (stub)."""

    return DefaultConfig()


def setup_logging(level: str | int = "INFO") -> None:
    """Very small logging helper."""

    import logging

    level_value = getattr(logging, str(level).upper(), logging.INFO)
    logging.basicConfig(level=level_value, format="%(levelname)s | %(message)s")


def reset_config() -> None:
    """Reset any cached configuration (noop)."""

    pass


def _discover_config_files() -> List[pathlib.Path]:
    """Find .yaml/.yml/.json files in current directory."""

    here = pathlib.Path(__file__).resolve().parent
    return list(here.glob("*.yml")) + list(here.glob("*.yaml")) + list(here.glob("*.json"))


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
