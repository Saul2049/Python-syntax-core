#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移动平均策略参数网格搜索优化
"""
import itertools

import pandas as pd
from tqdm import tqdm  # pip install tqdm

from src import backtest, metrics

# 搜索空间
FAST = range(3, 11)  # 3…10
SLOW = range(10, 41, 5)  # 10,15,20,25,30,35,40
ATR = [10, 14, 20]

results = []
for f, s, a in tqdm(itertools.product(FAST, SLOW, ATR), total=len(FAST) * len(SLOW) * len(ATR)):
    if f >= s:  # 保证快线 < 慢线
        continue
    equity = backtest.run_backtest(fast_win=f, slow_win=s, atr_win=a)
    row = dict(
        fast=f,
        slow=s,
        atr=a,
        cagr=metrics.cagr(equity),
        sharpe=metrics.sharpe_ratio(equity),
        mdd=metrics.max_drawdown(equity),
        final=equity.iloc[-1],
    )
    results.append(row)

df = pd.DataFrame(results).sort_values("sharpe", ascending=False)
df.to_csv("grid_results.csv", index=False)

print(df.head(10)[["fast", "slow", "atr", "cagr", "sharpe", "mdd"]])
print("\n最佳组合:", df.iloc[0][["fast", "slow", "atr"]].to_dict())
