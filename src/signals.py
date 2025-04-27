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