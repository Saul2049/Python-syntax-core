import matplotlib.pyplot as plt

from src import data, metrics
from src.broker import backtest_portfolio, backtest_single

# 加载数据
df = data.load_csv()
prices_dict = {"btc": df["btc"], "eth": df["eth"]}

# 单资产回测
eq_btc = backtest_single(df["btc"])
eq_eth = backtest_single(df["eth"])

# 不同配置的投资组合回测
# 等权重组合 (50/50固定权重)
eq_df_equal = backtest_portfolio(prices_dict, use_dynamic_weights=False)
eq_total_equal = eq_df_equal["Portfolio"]

# 动态权重组合 - 标准配置
eq_df_dynamic = backtest_portfolio(
    prices_dict,
    use_dynamic_weights=True,
    max_weight_factor=3.0,  # 增加最大权重倍数
    min_weight_factor=0.2,
    lookback=20,  # 增加回看期，避免过度依赖短期波动
    prefer_better_asset=True,
    weight_power=2.5,  # 增加权重差异
)
eq_total_dynamic = eq_df_dynamic["Portfolio"]

# 动态权重组合 - 熊市防御配置
eq_df_dynamic_bear = backtest_portfolio(
    prices_dict,
    use_dynamic_weights=True,
    max_weight_factor=5.0,  # 在熊市中更极端地偏向表现好的资产
    min_weight_factor=0.1,
    lookback=30,  # 更长的回看期，减少噪音
    prefer_better_asset=True,
    weight_power=4.0,  # 更激进地放大表现差异
)
eq_total_dynamic_bear = eq_df_dynamic_bear["Portfolio"]

# 偏向BTC的固定偏向配置 (80% BTC / 20% ETH)
eq_df_btc_biased = backtest_portfolio(
    prices_dict, use_dynamic_weights=False, base_risk_frac=0.02, init_equity=100_000.0
)
# 手动调整初始权重 (80/20)
eq_df_btc_biased["btc"] = eq_df_btc_biased["btc"] * 1.6  # 增加80%
eq_df_btc_biased["eth"] = eq_df_btc_biased["eth"] * 0.4  # 减少到20%
eq_df_btc_biased["Portfolio"] = eq_df_btc_biased["btc"] + eq_df_btc_biased["eth"]
eq_total_btc_biased = eq_df_btc_biased["Portfolio"]

# 100% BTC
eq_btc_only = backtest_portfolio({"btc": df["btc"]}, init_equity=100_000)["Portfolio"]

# 100% ETH
eq_eth_only = backtest_portfolio({"eth": df["eth"]}, init_equity=100_000)["Portfolio"]

# 打印各个投资组合的绩效指标
print("\nPerformance Comparison:")
print("-" * 80)
print(
    f"BTC Strategy:       CAGR: {metrics.cagr(eq_btc):.2%}, MaxDD: {metrics.max_drawdown(eq_btc):.2%}, Sharpe: {metrics.sharpe_ratio(eq_btc):.2f}"
)
print(
    f"ETH Strategy:       CAGR: {metrics.cagr(eq_eth):.2%}, MaxDD: {metrics.max_drawdown(eq_eth):.2%}, Sharpe: {metrics.sharpe_ratio(eq_eth):.2f}"
)
print(
    f"Equal Weight:       CAGR: {metrics.cagr(eq_total_equal):.2%}, MaxDD: {metrics.max_drawdown(eq_total_equal):.2%}, Sharpe: {metrics.sharpe_ratio(eq_total_equal):.2f}"
)
print(
    f"Fixed 80/20:        CAGR: {metrics.cagr(eq_total_btc_biased):.2%}, MaxDD: {metrics.max_drawdown(eq_total_btc_biased):.2%}, Sharpe: {metrics.sharpe_ratio(eq_total_btc_biased):.2f}"
)
print(
    f"Dynamic Weight:     CAGR: {metrics.cagr(eq_total_dynamic):.2%}, MaxDD: {metrics.max_drawdown(eq_total_dynamic):.2%}, Sharpe: {metrics.sharpe_ratio(eq_total_dynamic):.2f}"
)
print(
    f"Bear Defense:       CAGR: {metrics.cagr(eq_total_dynamic_bear):.2%}, MaxDD: {metrics.max_drawdown(eq_total_dynamic_bear):.2%}, Sharpe: {metrics.sharpe_ratio(eq_total_dynamic_bear):.2f}"
)
print(
    f"100% BTC:           CAGR: {metrics.cagr(eq_btc_only):.2%}, MaxDD: {metrics.max_drawdown(eq_btc_only):.2%}, Sharpe: {metrics.sharpe_ratio(eq_btc_only):.2f}"
)
print(
    f"100% ETH:           CAGR: {metrics.cagr(eq_eth_only):.2%}, MaxDD: {metrics.max_drawdown(eq_eth_only):.2%}, Sharpe: {metrics.sharpe_ratio(eq_eth_only):.2f}"
)
print("-" * 80)

# 绘制各策略净值曲线比较图 - 基础策略对比
plt.figure(figsize=(12, 6))
plt.plot(eq_btc, label="BTC Strategy", linewidth=2)
plt.plot(eq_eth, label="ETH Strategy", linewidth=2)
plt.plot(eq_total_equal, label="Equal Weight (50/50)", linewidth=2, linestyle="--")
plt.title("Strategy and Portfolio Comparison")
plt.xlabel("Date")
plt.ylabel("Equity")
plt.grid(alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig("strategy_comparison.png")
plt.show()

# 绘制不同权重方法的比较图
plt.figure(figsize=(12, 6))
plt.plot(eq_btc_only, label="100% BTC", linewidth=2)
plt.plot(eq_total_equal, label="Equal Weight (50/50)", linewidth=2, linestyle="--")
plt.plot(eq_total_btc_biased, label="Fixed 80/20", linewidth=2, color="orange")
plt.plot(eq_total_dynamic, label="Dynamic Weight", linewidth=2, color="green")
plt.plot(eq_total_dynamic_bear, label="Bear Defense", linewidth=2, color="red")
plt.title("Portfolio Allocation Methods Comparison")
plt.xlabel("Date")
plt.ylabel("Equity")
plt.grid(alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig("allocation_comparison.png")
plt.show()

# 绘制动态权重组合的资产权重随时间变化
plt.figure(figsize=(12, 4))

# 标准动态权重的BTC比例
btc_weights = eq_df_dynamic["btc"] / eq_df_dynamic["Portfolio"]
plt.plot(btc_weights, label="BTC Weight (Standard)", linewidth=2, color="green")

# 熊市防御配置的BTC比例
btc_weights_bear = eq_df_dynamic_bear["btc"] / eq_df_dynamic_bear["Portfolio"]
plt.plot(btc_weights_bear, label="BTC Weight (Bear Defense)", linewidth=2, color="red")

plt.axhline(y=0.5, color="blue", linestyle="--", alpha=0.5, label="Equal Weight (0.5)")
plt.axhline(y=0.8, color="orange", linestyle="--", alpha=0.5, label="Fixed 80/20 (0.8)")
plt.title("BTC Weight in Dynamic Portfolios")
plt.xlabel("Date")
plt.ylabel("Weight")
plt.ylim(0, 1)
plt.grid(alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig("dynamic_weights.png")
plt.show()

# 绘制相对比较图 - 各策略相对于100% BTC的表现
plt.figure(figsize=(12, 6))
btc_returns = eq_btc_only / eq_btc_only.iloc[0]
eq_rel = eq_total_equal / eq_total_equal.iloc[0] / btc_returns
dyn_rel = eq_total_dynamic / eq_total_dynamic.iloc[0] / btc_returns
bear_rel = eq_total_dynamic_bear / eq_total_dynamic_bear.iloc[0] / btc_returns
fixed_rel = eq_total_btc_biased / eq_total_btc_biased.iloc[0] / btc_returns

plt.plot([1] * len(btc_returns), label="100% BTC (baseline)", linewidth=2, color="blue")
plt.plot(eq_rel, label="Equal Weight (50/50)", linewidth=2, linestyle="--")
plt.plot(fixed_rel, label="Fixed 80/20", linewidth=2, color="orange")
plt.plot(dyn_rel, label="Dynamic Weight", linewidth=2, color="green")
plt.plot(bear_rel, label="Bear Defense", linewidth=2, color="red")
plt.axhline(y=1.0, color="k", linestyle="-", alpha=0.2)
plt.title("Portfolio Performance Relative to 100% BTC")
plt.xlabel("Date")
plt.ylabel("Relative Performance")
plt.grid(alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig("relative_performance.png")
plt.show()
