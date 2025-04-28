#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# plot_equity.py
import matplotlib.pyplot as plt

from src import backtest, data, metrics

df = data.load_csv()
price = df["btc"]

# 1) 策略曲线
equity = backtest.run_backtest()

# 2) 买入并持有基准
buy_hold = price / price.iloc[0] * equity.iloc[0]

# 3) 指标
print("CAGR      :", f"{metrics.cagr(equity):.2%}")
print("Max DD    :", f"{metrics.max_drawdown(equity):.2%}")
print("Sharpe(0) :", f"{metrics.sharpe_ratio(equity):.2f}")

# 4) 画图
plt.figure(figsize=(10, 5))
plt.plot(equity, label="Strategy")
plt.plot(buy_hold, label="Buy & Hold")
plt.title("Equity Curve vs Benchmark")
plt.legend()
plt.tight_layout()
plt.show()
