import pandas as pd
import numpy as np
from math import isfinite, ceil

def compute_position_size(equity: float, atr: float, risk_frac: float = 0.02) -> int:
    """
    计算基于风险的仓位大小。
    
    根据账户权益、波动率(ATR)和风险系数计算适当的仓位大小，至少返回1手。
    
    参数:
        equity: 当前账户权益
        atr: 平均真实波幅，用于衡量价格波动
        risk_frac: 风险系数，每笔交易愿意损失的资金比例(默认: 2%)
        
    返回:
        int: 仓位大小，至少为1手
    """
    # 如果ATR为零或无效，返回最小单位1
    if atr <= 0:
        return 1
    
    # 计算理论上的仓位大小
    position = (equity * risk_frac) / atr
    
    # 确保至少为1手
    return max(1, int(position))


def compute_stop_price(entry: float, atr: float, multiplier: float = 1.0) -> float:
    """
    计算止损价格。
    
    基于入场价格、ATR和乘数计算止损价格，通常用于为交易设置风险控制点。
    
    参数:
        entry: 入场价格
        atr: 平均真实波幅，用于度量价格波动
        multiplier: ATR乘数，控制止损距离(默认: 1.0)
        
    返回:
        float: 计算得到的止损价格
    """
    # 确保ATR为非负值
    atr_value = max(0, atr)
    
    # 计算止损价格 (做多的情况下)
    return entry - multiplier * atr_value

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
            position = size
            entry = p
            stop = compute_stop_price(entry, atr.iloc[i])

        equity_curve.append(equity + (p - entry) * position if position else equity)

    return pd.Series(equity_curve, index=price.index[:len(equity_curve)]) 