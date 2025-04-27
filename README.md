# Python Algorithmic Trading Framework

```mermaid
graph TD
    A[数据层/Data Layer] -->|提供价格数据| B[信号层/Signals Layer]
    A -->|提供价格数据| D[回测引擎/Backtest Engine]
    B -->|生成交易信号| C[执行层/Broker Layer]
    C -->|执行交易策略| D
    D -->|生成权益曲线| E[指标层/Metrics Layer]
    D -->|组合配置| F[投资组合/Portfolio Layer]
    F -->|生成组合权益| E
    
    subgraph 核心模块/Core Modules
    A["data.py<br/>(数据加载/Data Loading)"]
    B["signals.py<br/>(技术指标/Technical Indicators)"]
    C["broker.py<br/>(仓位管理/Position Sizing)"]
    D["backtest.py<br/>(策略回测/Strategy Backtest)"]
    E["metrics.py<br/>(性能评估/Performance Metrics)"]
    F["portfolio_backtest.py<br/>(组合回测/Portfolio Backtest)"]
    end
```

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