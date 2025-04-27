#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
绘制移动平均策略与买入持有基准收益对比图表
"""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from src import data, backtest, metrics

# 读取价格数据
df = data.load_csv()
price = df["btc"]

# 运行回测获取权益曲线
equity = backtest.run_backtest(
    fast_win=3,
    slow_win=7,
    risk_frac=0.02,
    atr_win=14,
    stop_mult=1.0
)

# 计算买入持有基准 (Buy & Hold)
benchmark = price / price.iloc[0] * equity.iloc[0]

# 绘制主图表
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1]})
fig.suptitle("移动平均交叉策略回测 (MA Crossover Backtest)", fontsize=16)

# 权益曲线图 (上图)
ax1.plot(equity.index, equity, 'b-', linewidth=2, label='策略 (Strategy)')
ax1.plot(benchmark.index, benchmark, 'r--', linewidth=1.5, label='买入持有 (Buy & Hold)')
ax1.set_ylabel("权益 (Equity $)")
ax1.legend(loc='upper left')
ax1.grid(alpha=0.3)

# 设置日期格式
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=1))

# 相对表现图 (下图)
relative = equity / benchmark
ax2.plot(relative.index, relative, 'g-', linewidth=1.5)
ax2.axhline(y=1.0, color='black', linestyle='--', alpha=0.5)
ax2.set_ylabel("相对表现 (Relative)")
ax2.grid(alpha=0.3)
ax2.set_xlabel("日期 (Date)")

# 调整布局
plt.tight_layout()
plt.subplots_adjust(top=0.94)

# 计算性能指标
cagr_strategy = metrics.cagr(equity)
cagr_benchmark = metrics.cagr(benchmark)
dd_strategy = metrics.max_drawdown(equity)
dd_benchmark = metrics.max_drawdown(benchmark)

# 在图表上添加指标说明
metrics_text = (
    f"策略CAGR (Strategy CAGR): {cagr_strategy:.2%}\n"
    f"基准CAGR (Benchmark CAGR): {cagr_benchmark:.2%}\n\n"
    f"策略最大回撤 (Strategy Max DD): {dd_strategy:.2%}\n"
    f"基准最大回撤 (Benchmark Max DD): {dd_benchmark:.2%}"
)
ax1.text(0.02, 0.05, metrics_text, transform=ax1.transAxes, 
         bbox=dict(facecolor='white', alpha=0.7), fontsize=10)

# 保存和显示
plt.savefig("equity_plot.png", dpi=150)
plt.show()

# 打印详细指标
print("\n=== 策略表现指标 (Performance Metrics) ===")
print(f"策略最终权益 (Final Equity): ${equity.iloc[-1]:,.2f}")
print(f"买入持有最终权益 (Buy & Hold Final): ${benchmark.iloc[-1]:,.2f}")
print(f"超额收益 (Alpha): ${equity.iloc[-1] - benchmark.iloc[-1]:,.2f}")
print()
print(f"策略CAGR (Strategy CAGR): {cagr_strategy:.2%}")
print(f"基准CAGR (Benchmark CAGR): {cagr_benchmark:.2%}")
print() 
print(f"策略最大回撤 (Strategy Max DD): {dd_strategy:.2%}")
print(f"基准最大回撤 (Benchmark Max DD): {dd_benchmark:.2%}")
print()
print(f"策略夏普比率 (Strategy Sharpe): {metrics.sharpe_ratio(equity):.2f}")
print(f"基准夏普比率 (Benchmark Sharpe): {metrics.sharpe_ratio(benchmark):.2f}")
print(f"收益风险比 (Return/Risk): {abs(cagr_strategy / dd_strategy):.2f}")
