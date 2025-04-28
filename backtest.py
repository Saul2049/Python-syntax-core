#!/usr/bin/env python3
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from broker import compute_position_size, compute_stop_price
from data import load_csv
from signals import (bearish_cross_indices, bullish_cross_indices,
                     moving_average)


def run_backtest(
    price: pd.Series,
    fast_win: int,
    slow_win: int,
    risk_per_trade: float,
    stop_mult: float,
) -> (float, pd.Series):
    # Calculate ATR(14)
    tr = pd.DataFrame(
        {
            "hl": price.rolling(2).max() - price.rolling(2).min(),
            "hc": (price - price.shift(1)).abs(),
            "lc": (price - price.shift(1)).abs(),
        }
    ).max(axis=1)
    atr14 = tr.rolling(14).mean()

    # Generate signals
    fast = moving_average(price, fast_win)
    slow = moving_average(price, slow_win)
    buy_i = bullish_cross_indices(fast, slow)
    sell_i = bearish_cross_indices(fast, slow)

    equity = 100_000.0
    position = 0
    entry = 0.0
    stop_price = None
    equity_curve = []

    for i, p in enumerate(price):
        # entry logic
        if i in buy_i and position == 0 and not np.isnan(atr14.iloc[i]):
            size = compute_position_size(equity, atr14.iloc[i], risk_per_trade)
            entry = p
            position = size
            stop_price = compute_stop_price(entry, atr14.iloc[i], stop_mult)
        # exit logic
        if position > 0:
            # stop-loss
            if p <= stop_price:
                equity += (stop_price - entry) * position
                position = 0
                stop_price = None
                equity_curve.append(equity)
                continue
            # crossover exit
            if i in sell_i:
                equity += (p - entry) * position
                position = 0
                stop_price = None
        # record equity
        equity_curve.append(equity)

    # mark-to-market
    if position > 0:
        equity += (price.iloc[-1] - entry) * position

    equity_series = pd.Series(equity_curve, index=price.index)
    return equity, equity_series


def compute_metrics(equity_series: pd.Series, price: pd.Series):
    days = (price.index[-1] - price.index[0]).days
    years = days / 365.25
    initial = equity_series.iloc[0]
    final = equity_series.iloc[-1]
    cagr = (final / initial) ** (1 / years) - 1
    drawdown = (equity_series / equity_series.cummax() - 1).min()
    returns = equity_series.pct_change().dropna()
    sharpe = returns.mean() / returns.std() * np.sqrt(252)
    return cagr, drawdown, sharpe


if __name__ == "__main__":
    # Load data from CSV or fetch via Binance
    df = load_csv()
    # df = pd.concat([fetch_klines("BTCUSDT"),
    #               fetch_klines("ETHUSDT")], axis=1)
    price = df["btc"]

    # Run backtest strategy
    equity, equity_series = run_backtest(
        price,
        fast_win=3,
        slow_win=7,
        risk_per_trade=0.02,
        stop_mult=1
    )

    print(f"Final equity: {equity:,.2f} USD")

    # Compute performance metrics
    cagr, dd, sharpe = compute_metrics(equity_series, price)
    print(f"CAGR: {cagr:.2%}, Max DD: {dd:.2%}, Sharpe: {sharpe:.2f}")

    # Plot equity curve
    equity_series.plot(title="Equity Curve")
    plt.xlabel("Date")
    plt.ylabel("Equity (USD)")
    plt.show()
