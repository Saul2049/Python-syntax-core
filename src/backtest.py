#!/usr/bin/env python3
from math import isfinite

import matplotlib.pyplot as plt
import pandas as pd

from src.broker import compute_position_size, compute_stop_price
from src.data import load_csv
from src.signals import (
    bearish_cross_indices,
    bullish_cross_indices,
    moving_average,
)


def run_backtest(
    fast_win: int = 7,
    slow_win: int = 20,
    risk_frac: float = 0.02,
    atr_win: int = 20,
    stop_mult: float = 1.0,
) -> pd.Series:
    df = load_csv()
    price = df["btc"]
    fast = moving_average(price, fast_win)
    slow = moving_average(price, slow_win)

    tr = pd.concat(
        {
            "hl": price.rolling(2).max() - price.rolling(2).min(),
            "hc": (price - price.shift(1)).abs(),
            "lc": (price - price.shift(1)).abs(),
        },
        axis=1,
    ).max(axis=1)
    atr = tr.rolling(atr_win).mean()

    equity = 100_000.0
    equity_curve = []

    position = 0
    entry = None
    stop = None

    buy_i = set(bullish_cross_indices(fast, slow))
    sell_i = set(bearish_cross_indices(fast, slow))

    for i, p in enumerate(price):
        # stop-loss check
        if position and p < stop:
            equity += (p - entry) * position
            position = 0

        # exit on crossover
        if i in sell_i and position:
            equity += (p - entry) * position
            position = 0

        # entry on crossover
        if i in buy_i and not position and isfinite(atr.iloc[i]):
            size = compute_position_size(equity, atr.iloc[i], risk_frac)
            if size:
                position = size
                entry = p
                stop = compute_stop_price(entry, atr.iloc[i], stop_mult)

        equity_curve.append(
            equity + (p - entry) * position if position else equity
        )

    return pd.Series(equity_curve, index=price.index)


if __name__ == "__main__":
    equity_series = run_backtest(
        fast_win=7,
        slow_win=20,
        risk_frac=0.02,
        atr_win=20,
    )
    print(equity_series)
    equity_series.plot(title="Equity Curve")
    plt.xlabel("Date")
    plt.ylabel("Equity (USD)")
    plt.show()
