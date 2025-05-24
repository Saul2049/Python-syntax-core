#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Improved Strategy Module - Backward Compatibility Layer (改进策略模块 - 向后兼容层)

This module maintains backward compatibility while delegating to the new modular strategy package.
For new code, prefer importing from src.strategies package directly.
"""

import warnings

import pandas as pd

from src.strategies.breakout import BollingerBreakoutStrategy

# Import new strategy classes
from src.strategies.moving_average import ImprovedMAStrategy, SimpleMAStrategy
from src.strategies.oscillator import MACDStrategy, RSIStrategy
from src.strategies.trend_following import MultiTimeframeStrategy, TrendFollowingStrategy

# Issue deprecation warning
warnings.warn(
    "Importing from src.improved_strategy is deprecated. "
    "Please use 'from src.strategies import <StrategyName>' instead.",
    DeprecationWarning,
    stacklevel=2,
)


def simple_ma_cross(
    data: pd.DataFrame,
    short_window: int = 10,
    long_window: int = 50,
    column: str = "close",
) -> pd.DataFrame:
    """
    简单移动平均线交叉策略 (Legacy function - use SimpleMAStrategy instead)

    参数:
        data: 包含价格数据的DataFrame
        short_window: 短期移动平均窗口
        long_window: 长期移动平均窗口
        column: 用于计算移动平均的列名

    返回:
        包含信号的DataFrame
    """
    warnings.warn(
        "simple_ma_cross function is deprecated. Use SimpleMAStrategy class instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    strategy = SimpleMAStrategy(short_window=short_window, long_window=long_window, column=column)
    return strategy.generate_signals(data)


def bollinger_breakout(
    data: pd.DataFrame,
    window: int = 20,
    num_std: float = 2.0,
    column: str = "close",
) -> pd.DataFrame:
    """
    布林带突破策略 (Legacy function - use BollingerBreakoutStrategy instead)

    参数:
        data: 包含价格数据的DataFrame
        window: 移动平均窗口
        num_std: 标准差倍数
        column: 用于计算布林带的列名

    返回:
        包含信号的DataFrame
    """
    warnings.warn(
        "bollinger_breakout function is deprecated. Use BollingerBreakoutStrategy class instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    strategy = BollingerBreakoutStrategy(window=window, num_std=num_std)
    return strategy.generate_signals(data)


def rsi_strategy(
    data: pd.DataFrame,
    window: int = 14,
    overbought: int = 70,
    oversold: int = 30,
    column: str = "close",
) -> pd.DataFrame:
    """
    RSI策略 (Legacy function - use RSIStrategy instead)

    参数:
        data: 包含价格数据的DataFrame
        window: RSI计算窗口
        overbought: 超买阈值
        oversold: 超卖阈值
        column: 用于计算RSI的列名

    返回:
        包含信号的DataFrame
    """
    warnings.warn(
        "rsi_strategy function is deprecated. Use RSIStrategy class instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    strategy = RSIStrategy(window=window, overbought=overbought, oversold=oversold, column=column)
    return strategy.generate_signals(data)


def macd_strategy(
    data: pd.DataFrame,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
    column: str = "close",
) -> pd.DataFrame:
    """
    MACD策略 (Legacy function - use MACDStrategy instead)

    参数:
        data: 包含价格数据的DataFrame
        fast_period: 快速EMA周期
        slow_period: 慢速EMA周期
        signal_period: 信号线周期
        column: 用于计算MACD的列名

    返回:
        包含信号的DataFrame
    """
    warnings.warn(
        "macd_strategy function is deprecated. Use MACDStrategy class instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    strategy = MACDStrategy(
        fast_period=fast_period, slow_period=slow_period, signal_period=signal_period
    )
    return strategy.generate_signals(data)


def improved_ma_cross(
    data: pd.DataFrame,
    short_window: int = 10,
    long_window: int = 50,
    rsi_window: int = 14,
    rsi_threshold: int = 50,
    volume_factor: float = 1.5,
    column: str = "close",
) -> pd.DataFrame:
    """
    改进版移动平均线交叉策略，结合RSI和成交量确认 (Legacy function - use ImprovedMAStrategy instead)

    参数:
        data: 包含价格数据的DataFrame
        short_window: 短期移动平均窗口
        long_window: 长期移动平均窗口
        rsi_window: RSI计算窗口
        rsi_threshold: RSI阈值
        volume_factor: 成交量确认因子
        column: 用于计算的列名

    返回:
        包含信号的DataFrame
    """
    warnings.warn(
        "improved_ma_cross function is deprecated. Use ImprovedMAStrategy class instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    strategy = ImprovedMAStrategy(
        short_window=short_window,
        long_window=long_window,
        rsi_window=rsi_window,
        rsi_threshold=rsi_threshold,
        volume_factor=volume_factor,
        column=column,
    )
    return strategy.generate_signals(data)


def trend_following_strategy(
    data: pd.DataFrame,
    ma_window: int = 20,
    atr_window: int = 14,
    atr_multiplier: float = 2.0,
    column: str = "close",
) -> pd.DataFrame:
    """
    趋势跟踪策略 (Legacy function - use TrendFollowingStrategy instead)

    参数:
        data: 包含价格数据的DataFrame
        ma_window: 移动平均窗口
        atr_window: ATR计算窗口
        atr_multiplier: ATR倍数
        column: 用于计算的列名

    返回:
        包含信号的DataFrame
    """
    warnings.warn(
        "trend_following_strategy function is deprecated. Use TrendFollowingStrategy class instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    strategy = TrendFollowingStrategy(
        ma_window=ma_window, atr_window=atr_window, multiplier=atr_multiplier
    )
    return strategy.generate_signals(data)


def multi_timeframe_strategy(
    data: pd.DataFrame,
    short_window: int = 10,
    long_window: int = 50,
    rsi_window: int = 14,
    column: str = "close",
    resample_rule: str = "4H",
) -> pd.DataFrame:
    """
    多时间框架策略 (Legacy function - use MultiTimeframeStrategy instead)

    参数:
        data: 包含价格数据的DataFrame
        short_window: 短期移动平均窗口
        long_window: 长期移动平均窗口
        rsi_window: RSI计算窗口
        column: 用于计算的列名
        resample_rule: 重采样规则

    返回:
        包含信号的DataFrame
    """
    warnings.warn(
        "multi_timeframe_strategy function is deprecated. Use MultiTimeframeStrategy class instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    strategy = MultiTimeframeStrategy(
        short_window=short_window,
        medium_window=long_window,
        long_window=50,
    )
    return strategy.generate_signals(data)


# Export all legacy functions for backward compatibility
__all__ = [
    "simple_ma_cross",
    "bollinger_breakout",
    "rsi_strategy",
    "macd_strategy",
    "improved_ma_cross",
    "trend_following_strategy",
    "multi_timeframe_strategy",
]
