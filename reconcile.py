#!/usr/bin/env python3
"""
对账脚本 - 比较实盘交易与回测结果
"""
from datetime import datetime

import numpy as np
import pandas as pd

from src import broker, signals
from src.data import load_csv

# 读取实盘交易记录
print("读取交易记录...")
trades_df = pd.read_csv("trades.csv", parse_dates=["timestamp"])

# 过滤有效的买卖记录(排除止损更新等记录)
trades_df = trades_df[trades_df["action"].isin(["BUY", "SELL"])]

if trades_df.empty:
    print("没有找到交易记录，请先执行实盘交易")
    exit(0)

# 计算每笔交易的盈亏
trades_df["pnl"] = np.where(
    trades_df["action"] == "SELL",
    trades_df["quantity"] * trades_df["price"],
    -trades_df["quantity"] * trades_df["price"],
)

# 累计实盘权益曲线
initial_equity = 10000  # 假设初始资金为10000
real_equity = initial_equity + trades_df["pnl"].cumsum()
trades_df["cumulative_equity"] = real_equity

# 设置日期范围
start_date = trades_df["timestamp"].min().date()
end_date = datetime.now().date()
print(f"交易时间范围: {start_date} 至 {end_date}")

# 读取价格数据
print("加载价格数据...")
price_data = load_csv()["btc"]

# 确保数据范围正确
valid_price_data = price_data[price_data.index >= pd.Timestamp(start_date)]
if valid_price_data.empty:
    print("价格数据不包含交易日期范围，无法进行对比")
    print(
        f"价格数据范围: {price_data.index.min().date()} 至 {price_data.index.max().date()}"
    )
    exit(0)

# 运行回测
print("执行回测分析...")
bt_equity = broker.backtest_single(
    price_data,
    fast_win=7,
    slow_win=20,
    atr_win=14,
    risk_frac=0.02,
    init_equity=initial_equity,
)

# 获取相同日期范围的回测结果
bt_filtered = bt_equity[bt_equity.index >= pd.Timestamp(start_date)]

# 输出比较结果
print("\n===== 实盘 vs 回测对比 =====")
print(f"初始资金: {initial_equity:.2f} USDT")
print(f"实盘交易笔数: {len(trades_df)}")
print(f"实盘最终资金: {real_equity.iloc[-1]:.2f} USDT")

if not bt_filtered.empty:
    bt_final = bt_filtered.iloc[-1]
    print(f"回测同期资金: {bt_final:.2f} USDT")

    # 计算差异
    diff_amount = real_equity.iloc[-1] - bt_final
    diff_pct = (diff_amount / bt_final) * 100
    print(f"差异金额: {diff_amount:.2f} USDT ({diff_pct:.2f}%)")

    # 分析可能的原因
    if abs(diff_pct) > 5:
        print("\n差异分析:")
        print("- 交易成本: 实盘中的手续费和滑点会导致额外成本")
        print("- 交易时机: 实盘交易可能没有在理想价格成交")
        print("- 信号处理: 回测可能捕获了实盘错过的信号")
        print("- 风险控制: 回测与实盘可能有不同的止损触发")
else:
    print("无法获取同期回测数据进行比较")

# 保存分析结果
output_file = "reconciliation_report.csv"
trades_df.to_csv(output_file, index=False)
print(f"\n详细分析已保存至 {output_file}")
