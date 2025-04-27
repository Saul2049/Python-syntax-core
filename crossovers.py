import numpy as np
import pandas as pd

def bullish_cross_indices(fast: pd.Series, slow: pd.Series) -> np.ndarray:
    """
    Return the integer indices where `fast` strictly crosses upward over `slow`.

    Both Series must share the same index and have no missing values.
    """
    # detect upward crossings: prior fast ≤ slow and current fast > slow
    crossover = (fast.shift(1) <= slow.shift(1)) & (fast > slow)
    return np.where(crossover)[0]

def bearish_cross_indices(fast: pd.Series, slow: pd.Series) -> np.ndarray:
    """Indices where fast crosses *down* below slow."""
    crossover = (fast.shift(1) >= slow.shift(1)) & (fast < slow)
    return np.where(crossover)[0]

if __name__ == "__main__":
    # quick demo: compute bullish cross indices for BTC using 5- and 20-day SMAs
    df = pd.read_csv("btc_eth.csv", parse_dates=["date"], index_col="date")
    fast = df["btc"].rolling(5).mean()
    slow = df["btc"].rolling(20).mean()
    idx = bullish_cross_indices(fast, slow)
    print("Bullish crosses at positions:", idx)
    print("Dates:", fast.index[idx])


