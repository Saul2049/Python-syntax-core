#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移动平均线指标计算模块
Moving Average Indicators Module
"""

import numpy as np
import pandas as pd


def simple_moving_average(data: pd.Series, window: int) -> pd.Series:
    """
    计算简单移动平均线 (Simple Moving Average, SMA)

    参数:
        data: 价格数据序列
        window: 移动平均窗口

    返回:
        pd.Series: 简单移动平均线序列
    """
    if window <= 0:
        raise ValueError("移动平均窗口必须大于0")

    return data.rolling(window=window, min_periods=1).mean()


def exponential_moving_average(data: pd.Series, window: int, alpha: float = None) -> pd.Series:
    """
    计算指数移动平均线 (Exponential Moving Average, EMA)

    参数:
        data: 价格数据序列
        window: 移动平均窗口
        alpha: 平滑因子，如果不提供则使用 2/(window+1)

    返回:
        pd.Series: 指数移动平均线序列
    """
    if window <= 0:
        raise ValueError("移动平均窗口必须大于0")

    if alpha is None:
        alpha = 2.0 / (window + 1)

    if not 0 < alpha <= 1:
        raise ValueError("平滑因子alpha必须在(0,1]范围内")

    return data.ewm(alpha=alpha, adjust=False).mean()


def weighted_moving_average(data: pd.Series, window: int) -> pd.Series:
    """
    计算加权移动平均线 (Weighted Moving Average, WMA)

    参数:
        data: 价格数据序列
        window: 移动平均窗口

    返回:
        pd.Series: 加权移动平均线序列
    """
    if window <= 0:
        raise ValueError("移动平均窗口必须大于0")

    # 创建权重序列：最近的数据权重更大
    weights = np.arange(1, window + 1)

    def wma_calc(x):
        if len(x) < window:
            # 如果数据不足，使用可用数据计算
            available_weights = weights[: len(x)]
            return np.average(x, weights=available_weights)
        else:
            return np.average(x, weights=weights)

    return data.rolling(window=window, min_periods=1).apply(wma_calc, raw=True)


# 兼容性别名
def moving_average(data: pd.Series, window: int) -> pd.Series:
    """
    兼容性函数：计算简单移动平均线

    参数:
        data: 价格数据序列
        window: 移动平均窗口

    返回:
        pd.Series: 移动平均线序列
    """
    return simple_moving_average(data, window)
