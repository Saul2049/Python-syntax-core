from typing import Literal, Optional, Union

import numpy as np
import pandas as pd


def moving_average(
    series: pd.Series, window: int, kind: Literal["sma", "ema", "wma"] = "sma"
) -> pd.Series:
    """
    计算移动平均线。
    Calculate moving average.

    参数 (Parameters):
        series: 输入的时间序列数据 (Input time series data)
        window: 窗口大小 (Window size)
        kind: 均线类型 (Moving average type)
              'sma': 简单移动平均 (Simple Moving Average)
              'ema': 指数移动平均 (Exponential Moving Average)
              'wma': 加权移动平均 (Weighted Moving Average)

    返回 (Returns):
        pd.Series: 计算后的均线序列 (Resulting moving average series)

    说明 (Notes):
        - EMA计算使用span参数，确保与传统技术分析软件的计算方法一致
        - span = 2/(alpha) - 1，其中alpha是平滑因子
        - 当window=20时，相当于传统EMA的20日周期
    """
    kind = kind.lower()

    if kind == "sma":
        # 简单移动平均线 (Simple Moving Average)
        return series.rolling(window).mean()
    elif kind == "ema":
        # 指数移动平均线 (Exponential Moving Average)
        # 使用span参数: span = 2/(alpha) - 1, 确保与传统EMA计算一致
        # span参数确保与技术分析软件的EMA计算方法一致
        return series.ewm(span=window, adjust=False, min_periods=1).mean()
    elif kind == "wma":
        # 加权移动平均线 (Weighted Moving Average)
        weights = np.arange(1, window + 1)
        return series.rolling(window).apply(
            lambda x: np.sum(weights * x) / weights.sum(), raw=True
        )
    else:
        raise ValueError(
            f"不支持的移动平均类型 (Unsupported moving average type): {kind}"
        )


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
