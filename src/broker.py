import pandas as pd
import numpy as np
from math import isfinite, ceil

def compute_position_size(equity: float, atr: float, risk_frac: float = 0.02) -> int:
    """Risk a fraction of equity per trade, return share size (rounded down)."""
    # 如果ATR为零，则无法建仓
    if atr == 0:
        return 0
    # 使用天花板函数确保至少建仓1手
    return ceil((equity * risk_frac) / atr)


def compute_stop_price(entry: float, atr: float, multiplier: float = 1.0) -> float:
    """Calculate stop-loss price as entry minus ATR multiplied by multiplier."""
    return entry - multiplier * atr 

from src import signals   # 避免循环引用

def backtest_single(price: pd.Series,
                    fast_win: int = 7,
                    slow_win: int = 20,
                    atr_win : int = 20,
                    risk_frac: float = 0.02,
                    init_equity: float = 100_000.0) -> pd.Series:
    """对单一 price 序列执行 MA+ATR 回测，返回 equity 曲线。"""
    fast = signals.moving_average(price, fast_win)
    slow = signals.moving_average(price, slow_win)

    # ATR
    tr = pd.concat(
        {
            "hl": price.rolling(2).max() - price.rolling(2).min(),
            "hc": (price - price.shift(1)).abs(),
            "lc": (price - price.shift(1)).abs(),
        }, axis=1
    ).max(axis=1)
    atr = tr.rolling(atr_win).mean()

    equity = init_equity
    equity_curve, position, entry, stop = [], 0, None, None

    buy_i  = set(signals.bullish_cross_indices(fast, slow))
    sell_i = set(signals.bearish_cross_indices(fast, slow))

    for i, p in enumerate(price):
        # 止损
        if position and p < stop:
            equity += (p - entry) * position
            position = 0

        # 卖出信号
        if i in sell_i and position:
            equity += (p - entry) * position
            position = 0

        # 买入信号
        if i in buy_i and position == 0 and isfinite(atr.iloc[i]):
            size = compute_position_size(equity, atr.iloc[i], risk_frac)
            if size:
                position = size
                entry = p
                stop = compute_stop_price(entry, atr.iloc[i])

        equity_curve.append(equity + (p - entry) * position if position else equity)

    return pd.Series(equity_curve, index=price.index[:len(equity_curve)]) 