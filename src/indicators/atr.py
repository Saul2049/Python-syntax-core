#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ATR (Average True Range) Calculation Module
"""

import pandas as pd


def calculate_true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """
    计算真实波幅 (True Range)

    参数:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列

    返回:
        pd.Series: 真实波幅序列
    """
    # 计算三种情况的真实波幅
    tr1 = high - low  # 当日高低价差
    tr2 = abs(high - close.shift(1))  # 当日最高价与前日收盘价差的绝对值
    tr3 = abs(low - close.shift(1))  # 当日最低价与前日收盘价差的绝对值

    # 取三者最大值作为真实波幅
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    return tr


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    """
    计算平均真实波幅 (Average True Range)

    参数:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        window: 计算窗口，默认14天

    返回:
        pd.Series: ATR序列
    """
    if window <= 0:
        raise ValueError("ATR计算窗口必须大于0")

    # 计算真实波幅
    tr = calculate_true_range(high, low, close)

    # 计算移动平均
    atr = tr.rolling(window=window, min_periods=1).mean()

    return atr


def calculate_atr_from_ohlc(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """
    从OHLC数据框直接计算ATR

    参数:
        df: 包含'high', 'low', 'close'列的DataFrame
        window: 计算窗口

    返回:
        pd.Series: ATR序列
    """
    required_columns = ["high", "low", "close"]
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"数据框缺少必要列: {missing_columns}")

    return calculate_atr(df["high"], df["low"], df["close"], window)


def calculate_atr_single_value(
    high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14
) -> float:
    """
    计算最新的ATR单一值

    参数:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        window: 计算窗口

    返回:
        float: 最新ATR值，如果无法计算则返回0.0
    """
    atr_series = calculate_atr(high, low, close, window)

    if atr_series.empty or pd.isna(atr_series.iloc[-1]):
        return 0.0

    return float(atr_series.iloc[-1])


# 兼容旧版本的函数名
def compute_atr(series: pd.Series, window: int = 14) -> float:
    """
    兼容性函数：从单一价格序列计算ATR
    注意：这是简化版本，建议使用complete OHLC数据

    参数:
        series: 价格序列 (通常是收盘价)
        window: 计算窗口

    返回:
        float: ATR值
    """
    # 简化计算，仅使用价格变化的绝对值
    price_diff = series.diff().abs()
    atr = price_diff.rolling(window=window, min_periods=1).mean()

    return atr.iloc[-1] if not atr.empty and not pd.isna(atr.iloc[-1]) else 0.0
