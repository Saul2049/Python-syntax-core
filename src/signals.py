import pandas as pd
import numpy as np


def moving_average(series: pd.Series, window: int, kind: str = "sma") -> pd.Series:
    """
    计算移动平均线。
    
    参数:
        series: 输入的时间序列数据
        window: 窗口大小
        kind: 均线类型，支持 'sma'(简单移动平均), 'ema'(指数移动平均), 
              'wma'(加权移动平均)
              
    返回:
        pd.Series: 计算后的均线序列
    """
    kind = kind.lower()
    
    if kind == "sma":
        # 简单移动平均线 (Simple Moving Average)
        return series.rolling(window).mean()
    elif kind == "ema":
        # 指数移动平均线 (Exponential Moving Average)
        return series.ewm(span=window, adjust=False).mean()
    elif kind == "wma":
        # 加权移动平均线 (Weighted Moving Average)
        weights = np.arange(1, window + 1)
        return series.rolling(window).apply(
            lambda x: np.sum(weights * x) / weights.sum(), raw=True
        )
    else:
        raise ValueError(f"Unsupported moving average type: {kind}")


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