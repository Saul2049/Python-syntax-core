import matplotlib.pyplot as plt
from src import data, metrics
from src.portfolio_backtest import run_portfolio
from src.broker import backtest_single

df = data.load_csv()
eq_btc = backtest_single(df["btc"])
eq_eth = backtest_single(df["eth"])
eq_total = run_portfolio()  # 默认 50/50 配置
eq_btc_only = run_portfolio({"btc": 1.0, "eth": 0.0})  # 100% BTC
eq_eth_only = run_portfolio({"btc": 0.0, "eth": 1.0})  # 100% ETH

# 打印各个投资组合的绩效指标
print("\nPerformance Comparison:")
print("-" * 60)
print(f"BTC Strategy:   CAGR: {metrics.cagr(eq_btc):.2%}, MaxDD: {metrics.max_drawdown(eq_btc):.2%}, Sharpe: {metrics.sharpe_ratio(eq_btc):.2f}")
print(f"ETH Strategy:   CAGR: {metrics.cagr(eq_eth):.2%}, MaxDD: {metrics.max_drawdown(eq_eth):.2%}, Sharpe: {metrics.sharpe_ratio(eq_eth):.2f}")
print(f"50/50 Portfolio: CAGR: {metrics.cagr(eq_total):.2%}, MaxDD: {metrics.max_drawdown(eq_total):.2%}, Sharpe: {metrics.sharpe_ratio(eq_total):.2f}")
print(f"100% BTC:       CAGR: {metrics.cagr(eq_btc_only):.2%}, MaxDD: {metrics.max_drawdown(eq_btc_only):.2%}, Sharpe: {metrics.sharpe_ratio(eq_btc_only):.2f}")
print(f"100% ETH:       CAGR: {metrics.cagr(eq_eth_only):.2%}, MaxDD: {metrics.max_drawdown(eq_eth_only):.2%}, Sharpe: {metrics.sharpe_ratio(eq_eth_only):.2f}")
print("-" * 60)

# 绘制各策略净值曲线比较图
plt.figure(figsize=(12, 6))
plt.plot(eq_btc, label="BTC Strategy", linewidth=2)
plt.plot(eq_eth, label="ETH Strategy", linewidth=2)
plt.plot(eq_total, label="50/50 Portfolio", linewidth=2, linestyle='--')
plt.title("Strategy and Portfolio Comparison")
plt.xlabel("Date")
plt.ylabel("Equity")
plt.grid(alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig("strategy_comparison.png")
plt.show()

# 绘制不同权重配置的比较图
plt.figure(figsize=(12, 6))
plt.plot(eq_btc_only, label="100% BTC", linewidth=2)
plt.plot(eq_eth_only, label="100% ETH", linewidth=2)
plt.plot(eq_total, label="50/50 Portfolio", linewidth=2, linestyle='--')
plt.title("Different Asset Allocations Comparison")
plt.xlabel("Date")
plt.ylabel("Equity")
plt.grid(alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig("allocation_comparison.png")
plt.show() 