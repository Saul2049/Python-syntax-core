#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移动平均指标模块 (Moving Averages Module)

提供各种移动平均计算功能，包括简单、指数和加权移动平均
"""

import numpy as np
import pandas as pd


def simple_moving_average(series: pd.Series, window: int) -> pd.Series:
    """
    计算简单移动平均 (SMA)

    参数:
        series: 输入时间序列
        window: 窗口大小

    返回:
        简单移动平均序列
    """
    return series.rolling(window=window).mean()


def exponential_moving_average(series: pd.Series, window: int, adjust: bool = False) -> pd.Series:
    """
    计算指数移动平均 (EMA)

    参数:
        series: 输入时间序列
        window: 窗口大小
        adjust: 是否使用调整方法

    返回:
        指数移动平均序列
    """
    return series.ewm(span=window, adjust=adjust).mean()


def weighted_moving_average(series: pd.Series, window: int) -> pd.Series:
    """
    计算加权移动平均 (WMA)

    参数:
        series: 输入时间序列
        window: 窗口大小

    返回:
        加权移动平均序列
    """
    weights = np.arange(1, window + 1)
    return series.rolling(window=window).apply(
        lambda x: np.sum(weights * x) / np.sum(weights), raw=True
    )


def moving_average(
    series: pd.Series, window: int, kind: str = "simple", type: str = None
) -> pd.Series:
    """
    通用移动平均计算函数

    参数:
        series: 输入时间序列
        window: 窗口大小
        kind: 移动平均类型，'sma', 'ema', 'wma'
        type: 旧参数名，为了向后兼容，优先使用kind参数

    返回:
        移动平均序列
    """
    # 向后兼容，优先使用kind参数
    ma_type = kind if type is None else type

    if ma_type.lower() in ["simple", "sma"]:
        return simple_moving_average(series, window)
    elif ma_type.lower() in ["exponential", "ema"]:
        return exponential_moving_average(series, window)
    elif ma_type.lower() == "wma":
        return weighted_moving_average(series, window)
    else:
        raise ValueError(f"不支持的移动平均类型: {ma_type}. 支持的类型: 'sma', 'ema', 'wma'")
