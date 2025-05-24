#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
波动率指标模块 (Volatility Indicators Module)

提供各种波动率相关的技术指标计算
"""

from typing import Tuple

import pandas as pd


def bollinger_bands(
    series: pd.Series, window: int = 20, num_std: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    计算布林带指标

    参数:
        series: 输入时间序列
        window: 计算窗口
        num_std: 标准差倍数

    返回:
        (上轨, 中轨, 下轨)
    """
    middle_band = series.rolling(window=window).mean()
    std_dev = series.rolling(window=window).std()
    upper_band = middle_band + (std_dev * num_std)
    lower_band = middle_band - (std_dev * num_std)
    return upper_band, middle_band, lower_band


def standard_deviation(series: pd.Series, window: int = 20) -> pd.Series:
    """
    计算滚动标准差

    参数:
        series: 输入时间序列
        window: 计算窗口

    返回:
        标准差序列
    """
    return series.rolling(window=window).std()


def average_true_range(
    high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14
) -> pd.Series:
    """
    计算平均真实范围 (ATR)

    参数:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        window: 计算窗口

    返回:
        ATR序列
    """
    # 计算真实范围的三个组成部分
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))

    # 取最大值作为真实范围
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # 计算平均真实范围
    atr = true_range.rolling(window=window).mean()
    return atr


def calculate_true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """
    计算真实范围 (True Range)

    参数:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列

    返回:
        真实范围序列
    """
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))

    return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    """
    计算ATR的别名函数，保持向后兼容性

    参数:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        window: 计算窗口

    返回:
        ATR序列
    """
    return average_true_range(high, low, close, window)


def keltner_channels(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    ma_period: int = 20,
    atr_period: int = 10,
    multiplier: float = 2.0,
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    计算Keltner通道

    参数:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        ma_period: 移动平均周期
        atr_period: ATR周期
        multiplier: ATR倍数

    返回:
        (上轨, 中轨, 下轨)
    """
    middle_line = close.rolling(window=ma_period).mean()
    atr = average_true_range(high, low, close, atr_period)

    upper_line = middle_line + (atr * multiplier)
    lower_line = middle_line - (atr * multiplier)

    return upper_line, middle_line, lower_line
