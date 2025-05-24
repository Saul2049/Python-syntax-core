#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动量指标模块 (Momentum Indicators Module)

提供各种动量相关的技术指标计算
"""

import pandas as pd


def momentum(series: pd.Series, period: int = 14) -> pd.Series:
    """
    计算动量指标

    参数:
        series: 输入时间序列
        period: 计算周期

    返回:
        动量序列
    """
    return series.diff(period)


def rate_of_change(series: pd.Series, period: int = 14) -> pd.Series:
    """
    计算变化率 (ROC)

    参数:
        series: 输入时间序列
        period: 计算周期

    返回:
        变化率序列 (百分比)
    """
    return series.pct_change(period) * 100


def zscore(series: pd.Series, window: int = 20) -> pd.Series:
    """
    计算z-score标准化

    参数:
        series: 输入时间序列
        window: 计算窗口

    返回:
        z-score序列
    """
    rolling_mean = series.rolling(window=window).mean()
    rolling_std = series.rolling(window=window).std()
    return (series - rolling_mean) / rolling_std


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """
    计算相对强弱指标 (RSI)

    参数:
        series: 输入时间序列
        window: 计算窗口

    返回:
        RSI序列 (0-100)
    """
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def stochastic_oscillator(
    high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3
) -> tuple[pd.Series, pd.Series]:
    """
    计算随机振荡器 (Stochastic Oscillator)

    参数:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        k_period: %K周期
        d_period: %D周期

    返回:
        (%K, %D) 元组
    """
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()

    k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    d_percent = k_percent.rolling(window=d_period).mean()

    return k_percent, d_percent
