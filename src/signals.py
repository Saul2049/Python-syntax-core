#!/usr/bin/env python3
# signals.py - 信号处理模块

from typing import Literal, Tuple, Union

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


def moving_average(
    series: pd.Series, window: int, kind: str = "simple", type: str = None
) -> pd.Series:
    """
    计算移动平均

    参数:
        series: 输入时间序列
        window: 窗口大小
        kind: 移动平均类型，'sma', 'ema', 'wma'('sma'=简单,'ema'=指数,'wma'=加权)
        type: 旧参数名，为了向后兼容，优先使用kind参数

    返回:
        移动平均序列
    """
    # 向后兼容，优先使用kind参数
    ma_type = kind if type is None else type

    if ma_type.lower() in ["simple", "sma"]:
        return series.rolling(window=window).mean()
    elif ma_type.lower() in ["exponential", "ema"]:
        return series.ewm(span=window, adjust=False).mean()
    elif ma_type.lower() == "wma":
        # 实现加权移动平均
        weights = np.arange(1, window + 1)
        return series.rolling(window=window).apply(
            lambda x: np.sum(weights * x) / np.sum(weights), raw=True
        )
    else:
        raise ValueError(f"不支持的移动平均类型: {ma_type}. 支持的类型: 'sma', 'ema', 'wma'")


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
    计算变化率

    参数:
        series: 输入时间序列
        period: 计算周期

    返回:
        变化率序列
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


def vectorized_cross(
    fast: pd.Series,
    slow: pd.Series,
    direction: Literal["above", "below"] = "above",
    threshold: float = 0.0,
    return_series: bool = True,
) -> Union[pd.Series, np.ndarray]:
    """
    向量化交叉检测函数。
    Vectorized cross detection function.

    参数 (Parameters):
        fast: 快速线 (Fast line)
        slow: 慢速线 (Slow line)
        direction: 交叉方向 (Cross direction)
                  'above': 上穿 (Cross above)
                  'below': 下穿 (Cross below)
        threshold: 交叉阈值 (Cross threshold)
                  用于控制交叉的灵敏度，默认0.0表示严格交叉
        return_series: 是否返回Series (Whether to return Series)
                      True: 返回布尔Series，保留原始索引
                      False: 返回交叉点的索引数组

    返回 (Returns):
        Union[pd.Series, np.ndarray]: 交叉信号 (Cross signals)

    说明 (Notes):
        - 当direction='above'时，检测fast上穿slow
        - 当direction='below'时，检测fast下穿slow
        - threshold参数可以用于控制交叉的灵敏度
          * threshold > 0: 需要更大的价格差才触发交叉
          * threshold < 0: 允许更小的价格差触发交叉
    """
    if direction == "above":
        cross = (fast.shift(1) <= slow.shift(1) + threshold) & (fast > slow + threshold)
    else:
        cross = (fast.shift(1) >= slow.shift(1) - threshold) & (fast < slow - threshold)

    return cross if return_series else np.where(cross)[0]


def bullish_cross_indices(fast: pd.Series, slow: pd.Series) -> np.ndarray:
    """Return indices where `fast` strictly crosses above `slow`."""
    return vectorized_cross(fast, slow, direction="above", return_series=False)


def bearish_cross_indices(fast: pd.Series, slow: pd.Series) -> np.ndarray:
    """Return indices where `fast` crosses below `slow`."""
    return vectorized_cross(fast, slow, direction="below", return_series=False)


def bullish_cross_series(fast: pd.Series, slow: pd.Series) -> pd.Series:
    """
    返回一个布尔Series，标记fast线上穿slow线的位置

    相比索引数组，返回Series的优势:
    - 保留了原始数据的索引
    - 可以用.diff()方法快速找出变化点
    - 易于与其他Series进行逻辑组合

    Example:
        cross_series = bullish_cross_series(fast_ma, slow_ma)
        # 找出所有上穿点
        cross_points = cross_series[cross_series]
        # 或者和其他条件组合
        buy_signal = cross_series & (rsi < 30)
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
