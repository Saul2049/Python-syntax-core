# Python Algorithmic Trading Framework

This repository contains a modular Python framework for backtesting algorithmic trading strategies, with a focus on moving average crossovers and risk-based position sizing. The architecture follows clean separation of concerns:

## Structure

- `src/data.py` - Data loading and API access (CSV, Binance)
- `src/signals.py` - Technical indicators and signal generation (MA, crossovers)
- `src/broker.py` - Position sizing and stop-loss logic
- `src/backtest.py` - Strategy orchestration and backtest runner
- `tests/` - Unit tests with pytest

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Run the backtest
python -c "from src.backtest import run_backtest; print(run_backtest().iloc[-1])"

# Run the tests
pytest
```

## Examples

### Simple Moving Average Demo
```python
from src import data, signals

df = data.load_csv()
sma_5 = signals.moving_average(df["btc"], 5)
print(sma_5.tail())
```

### Strategy vs Buy & Hold
```python
import matplotlib.pyplot as plt
from src import data, backtest

# Load data and run strategy
price = data.load_csv()["btc"]
eq = backtest.run_backtest()
buy_hold = price / price.iloc[0] * eq.iloc[0]

# Plot comparison
plt.plot(eq, label="Strategy")
plt.plot(buy_hold, label="Buy & Hold")
plt.legend()
plt.title("Trading Strategy vs Buy & Hold")
plt.xlabel("Date")
plt.ylabel("Equity ($)")
plt.show()
``` 