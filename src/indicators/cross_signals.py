#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交叉信号检测模块 (Cross Signal Detection Module)

提供各种交叉信号检测功能，用于识别技术分析中的交叉点
"""

from typing import Literal, Union

import numpy as np
import pandas as pd


def crossover(series1: pd.Series, series2: pd.Series) -> pd.Series:
    """
    检测 series1 上穿 series2

    参数:
        series1: 第一个时间序列
        series2: 第二个时间序列

    返回:
        布尔序列，True表示发生上穿
    """
    series1, series2 = pd.Series(series1), pd.Series(series2)
    # 当前值大于，且前一个值小于等于
    return (series1 > series2) & (series1.shift(1) <= series2.shift(1))


def crossunder(series1: pd.Series, series2: pd.Series) -> pd.Series:
    """
    检测 series1 下穿 series2

    参数:
        series1: 第一个时间序列
        series2: 第二个时间序列

    返回:
        布尔序列，True表示发生下穿
    """
    series1, series2 = pd.Series(series1), pd.Series(series2)
    # 当前值小于，且前一个值大于等于
    return (series1 < series2) & (series1.shift(1) >= series2.shift(1))


def vectorized_cross(
    fast: pd.Series,
    slow: pd.Series,
    direction: Literal["above", "below"] = "above",
    threshold: float = 0.0,
    return_series: bool = True,
) -> Union[pd.Series, np.ndarray]:
    """
    向量化交叉检测函数

    参数:
        fast: 快速线
        slow: 慢速线
        direction: 交叉方向 ('above': 上穿, 'below': 下穿)
        threshold: 交叉阈值，用于控制交叉的灵敏度
        return_series: 是否返回Series (True: 布尔Series, False: 索引数组)

    返回:
        交叉信号 (布尔Series或索引数组)
    """
    if direction == "above":
        cross = (fast.shift(1) <= slow.shift(1) + threshold) & (fast > slow + threshold)
    else:
        cross = (fast.shift(1) >= slow.shift(1) - threshold) & (fast < slow - threshold)

    return cross if return_series else np.where(cross)[0]


def bullish_cross_indices(fast: pd.Series, slow: pd.Series) -> np.ndarray:
    """返回fast上穿slow的索引位置"""
    return vectorized_cross(fast, slow, direction="above", return_series=False)


def bearish_cross_indices(fast: pd.Series, slow: pd.Series) -> np.ndarray:
    """返回fast下穿slow的索引位置"""
    return vectorized_cross(fast, slow, direction="below", return_series=False)


def bullish_cross_series(fast: pd.Series, slow: pd.Series) -> pd.Series:
    """
    返回一个布尔Series，标记fast线上穿slow线的位置

    优势:
    - 保留了原始数据的索引
    - 可以用.diff()方法快速找出变化点
    - 易于与其他Series进行逻辑组合
    """
    return vectorized_cross(fast, slow, direction="above")


def bearish_cross_series(fast: pd.Series, slow: pd.Series) -> pd.Series:
    """
    返回一个布尔Series，标记fast线下穿slow线的位置

    与bullish_cross_series类似，返回Series便于:
    - 保留原始索引
    - 进行.diff()操作
    - 与其他条件组合
    """
    return vectorized_cross(fast, slow, direction="below")
