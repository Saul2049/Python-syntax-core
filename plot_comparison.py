import matplotlib.pyplot as plt
from src import data, backtest, metrics

# Load price data
price = data.load_csv()["btc"]

# Run backtest to get equity curve
eq = backtest.run_backtest()

# Calculate buy & hold benchmark
buy_hold = price / price.iloc[0] * eq.iloc[0]

# Plot comparison
plt.figure(figsize=(10, 6))
plt.plot(eq, label="Strategy")
plt.plot(buy_hold, label="Buy & Hold")
plt.legend()
plt.title("Trading Strategy vs Buy & Hold")
plt.xlabel("Date")
plt.ylabel("Equity ($)")
plt.grid(alpha=0.3)
plt.show()

# Calculate and display metrics
print(f"Strategy final equity: ${eq.iloc[-1]:,.2f}")
print(f"Buy & Hold final equity: ${buy_hold.iloc[-1]:,.2f}")
print()
print(f"Strategy CAGR: {metrics.cagr(eq):.2%}")
print(f"Buy & Hold CAGR: {metrics.cagr(buy_hold):.2%}")
print() 
print(f"Strategy Max DD: {metrics.max_drawdown(eq):.2%}")
print(f"Buy & Hold Max DD: {metrics.max_drawdown(buy_hold):.2%}")
print()
print(f"Strategy Sharpe: {metrics.sharpe_ratio(eq):.2f}")
print(f"Buy & Hold Sharpe: {metrics.sharpe_ratio(buy_hold):.2f}") 