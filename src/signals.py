import pandas as pd
import numpy as np


def moving_average(series: pd.Series, window: int) -> pd.Series:
    """Compute the simple moving average over a specified window."""
    return series.rolling(window).mean()


def bullish_cross_indices(fast: pd.Series, slow: pd.Series) -> np.ndarray:
    """Return indices where `fast` strictly crosses above `slow`."""
    # prior fast ≤ slow and current fast > slow
    cross = (fast.shift(1) <= slow.shift(1)) & (fast > slow)
    return np.where(cross)[0]


def bearish_cross_indices(fast: pd.Series, slow: pd.Series) -> np.ndarray:
    """Return indices where `fast` crosses below `slow`."""
    cross = (fast.shift(1) >= slow.shift(1)) & (fast < slow)
    return np.where(cross)[0]


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
    return (fast.shift(1) <= slow.shift(1)) & (fast > slow)


def bearish_cross_series(fast: pd.Series, slow: pd.Series) -> pd.Series:
    """
    返回一个布尔Series，标记fast线下穿slow线的位置
    
    与bullish_cross_series类似，返回Series便于:
    - 保留原始索引
    - 进行.diff()操作
    - 与其他条件组合
    """
    return (fast.shift(1) >= slow.shift(1)) & (fast < slow) 