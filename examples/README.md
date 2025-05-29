# 📚 使用示例集合

本目录包含了专业交易系统的各种使用示例，帮助用户快速上手和理解系统功能。

## 📁 示例目录结构

```
examples/
├── basic/                  # 基础示例
│   ├── simple_strategy.py     # 简单策略示例
│   ├── data_loading.py        # 数据加载示例
│   └── backtesting_basic.py   # 基础回测示例
├── advanced/               # 高级示例
│   ├── multi_strategy.py      # 多策略组合
│   ├── real_time_trading.py   # 实时交易
│   └── portfolio_management.py # 投资组合管理
├── monitoring/             # 监控示例
│   ├── metrics_setup.py       # 指标配置
│   ├── alerting_config.py     # 告警配置
│   └── dashboard_setup.py     # 仪表板设置
└── integration/            # 集成示例
    ├── jupyter_notebook.ipynb # Jupyter集成
    ├── api_client.py          # API客户端示例
    └── data_pipeline.py       # 数据管道示例
```

## 🚀 快速开始示例

### 1. 最简单的策略示例

```python
# examples/basic/simple_strategy.py
from src.core.base_strategy import BaseStrategy
import pandas as pd

class SimpleMAStrategy(BaseStrategy):
    """简单移动平均策略"""
    
    def __init__(self, period=20):
        super().__init__(name="SimpleMA")
        self.period = period
    
    def generate_signals(self, data: pd.DataFrame):
        # 计算移动平均
        data['ma'] = data['close'].rolling(window=self.period).mean()
        
        # 生成信号
        if data['close'].iloc[-1] > data['ma'].iloc[-1]:
            return {
                "signal": "BUY",
                "confidence": 0.7,
                "price": data['close'].iloc[-1],
                "timestamp": data.index[-1]
            }
        else:
            return {
                "signal": "SELL", 
                "confidence": 0.7,
                "price": data['close'].iloc[-1],
                "timestamp": data.index[-1]
            }

# 使用示例
if __name__ == "__main__":
    import yfinance as yf
    
    # 下载数据
    data = yf.download("BTC-USD", period="1mo", interval="1h")
    
    # 创建策略
    strategy = SimpleMAStrategy(period=20)
    
    # 生成信号
    signal = strategy.generate_signals(data)
    print(f"信号: {signal}")
```

### 2. 数据加载和预处理

```python
# examples/basic/data_loading.py
import pandas as pd
import yfinance as yf
from src.data.processors.data_processor import DataProcessor

def load_crypto_data(symbol, period="1mo"):
    """加载加密货币数据"""
    data = yf.download(symbol, period=period, interval="1h")
    data.columns = data.columns.droplevel(1)  # 移除多级列名
    return data.dropna()

def preprocess_data(data):
    """数据预处理"""
    processor = DataProcessor()
    
    # 添加技术指标
    data['rsi'] = processor.calculate_rsi(data, period=14)
    data['macd'], data['macd_signal'] = processor.calculate_macd(data)
    data['bb_upper'], data['bb_lower'] = processor.calculate_bollinger_bands(data)
    
    return data

# 使用示例
if __name__ == "__main__":
    # 加载多个币种数据
    symbols = ["BTC-USD", "ETH-USD", "ADA-USD"]
    
    for symbol in symbols:
        print(f"加载 {symbol} 数据...")
        data = load_crypto_data(symbol)
        data = preprocess_data(data)
        
        print(f"数据形状: {data.shape}")
        print(f"最新RSI: {data['rsi'].iloc[-1]:.2f}")
        print("-" * 40)
```

### 3. 基础回测示例

```python
# examples/basic/backtesting_basic.py
from src.core.backtesting import BacktestEngine
from examples.basic.simple_strategy import SimpleMAStrategy
import pandas as pd
import yfinance as yf

def run_simple_backtest():
    """运行简单回测"""
    
    # 1. 准备数据
    print("📈 加载历史数据...")
    data = yf.download("BTC-USD", start="2024-01-01", end="2024-12-01", interval="1h")
    data.columns = data.columns.droplevel(1)
    
    # 2. 创建回测引擎
    backtest = BacktestEngine(
        initial_capital=10000,    # 初始资金
        commission=0.001,         # 手续费0.1%
        slippage=0.0005          # 滑点0.05%
    )
    
    # 3. 创建策略
    strategy = SimpleMAStrategy(period=20)
    
    # 4. 运行回测
    print("🔍 运行回测...")
    results = backtest.run(strategy, data)
    
    # 5. 分析结果
    print("\n📊 回测结果:")
    print(f"总收益率: {results['total_return']:.2%}")
    print(f"年化收益率: {results['annual_return']:.2%}")
    print(f"夏普比率: {results['sharpe_ratio']:.2f}")
    print(f"最大回撤: {results['max_drawdown']:.2%}")
    print(f"胜率: {results['win_rate']:.2%}")
    print(f"总交易次数: {results['total_trades']}")
    
    # 6. 绘制权益曲线
    if 'equity_curve' in results:
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(12, 6))
        plt.plot(results['equity_curve'])
        plt.title("权益曲线")
        plt.xlabel("时间")
        plt.ylabel("账户价值")
        plt.grid(True)
        plt.show()

if __name__ == "__main__":
    run_simple_backtest()
```

## 🔧 高级示例

### 多策略组合示例

```python
# examples/advanced/multi_strategy.py
from src.core.trading_engine import TradingEngine
from src.strategies.trend_following import TrendFollowingStrategy
from src.strategies.mean_reversion import MeanReversionStrategy

def create_multi_strategy_portfolio():
    """创建多策略投资组合"""
    
    # 配置
    config = {
        "capital_allocation": {
            "trend_following": 0.6,  # 60%分配给趋势策略
            "mean_reversion": 0.4    # 40%分配给均值回归
        },
        "risk_management": {
            "max_position_size": 0.05,
            "max_drawdown": 0.15
        }
    }
    
    # 创建交易引擎
    engine = TradingEngine(config)
    
    # 添加策略
    trend_strategy = TrendFollowingStrategy(
        fast_period=12,
        slow_period=26,
        name="TrendFollowing"
    )
    
    mean_strategy = MeanReversionStrategy(
        lookback_period=20,
        threshold=2.0,
        name="MeanReversion"
    )
    
    engine.add_strategy(trend_strategy, weight=0.6)
    engine.add_strategy(mean_strategy, weight=0.4)
    
    return engine

# 使用示例
if __name__ == "__main__":
    portfolio = create_multi_strategy_portfolio()
    
    # 模拟运行
    portfolio.start()
    print("多策略投资组合已启动")
```

### 实时交易示例

```python
# examples/advanced/real_time_trading.py
import asyncio
from src.brokers.live_broker_async import LiveBrokerAsync
from src.ws.binance_ws_client import BinanceWSClient
from src.strategies.trend_following import TrendFollowingStrategy
from src.monitoring.metrics_collector import get_metrics_collector

async def real_time_trading_example():
    """实时交易示例"""
    
    # 1. 配置
    API_KEY = "your_api_key"
    API_SECRET = "your_api_secret"
    SYMBOL = "BTCUSDT"
    
    # 2. 初始化组件
    strategy = TrendFollowingStrategy()
    metrics = get_metrics_collector()
    
    # 3. 启动监控服务
    metrics.start_server()
    
    # 4. 建立实时数据连接
    async with LiveBrokerAsync(API_KEY, API_SECRET, testnet=True) as broker:
        ws_client = BinanceWSClient()
        
        # 订阅实时数据
        await ws_client.subscribe_kline(SYMBOL, "1m")
        
        print(f"🚀 开始实时交易 {SYMBOL}")
        
        async for kline_data in ws_client.listen():
            # 更新价格
            current_price = float(kline_data['c'])
            metrics.record_price_update(SYMBOL, current_price)
            
            # 检查信号
            if should_check_signal(kline_data):  # 每分钟检查一次
                data = prepare_data_for_strategy(kline_data)
                signal = strategy.generate_signals(data)
                
                if signal['signal'] != 'HOLD':
                    # 执行交易
                    await execute_trade(broker, signal, SYMBOL)
                    
            await asyncio.sleep(1)  # 避免过度频繁检查

async def execute_trade(broker, signal, symbol):
    """执行交易"""
    try:
        if signal['signal'] == 'BUY':
            order = await broker.place_order_async(
                symbol=symbol,
                side='BUY',
                order_type='MARKET',
                quantity=0.001  # 固定数量
            )
            print(f"✅ 买入订单已提交: {order}")
            
        elif signal['signal'] == 'SELL':
            order = await broker.place_order_async(
                symbol=symbol,
                side='SELL', 
                order_type='MARKET',
                quantity=0.001
            )
            print(f"✅ 卖出订单已提交: {order}")
            
    except Exception as e:
        print(f"❌ 交易执行失败: {e}")

# 运行实时交易
if __name__ == "__main__":
    asyncio.run(real_time_trading_example())
```

## 📊 监控示例

### 完整监控设置

```python
# examples/monitoring/metrics_setup.py
from src.monitoring.metrics_collector import get_metrics_collector
from src.monitoring.health_checker import HealthChecker
from src.monitoring.alerting import AlertManager

def setup_comprehensive_monitoring():
    """设置全面的监控系统"""
    
    # 1. 指标收集器
    metrics = get_metrics_collector()
    metrics.start_server()
    
    # 2. 健康检查器
    health_checker = HealthChecker(
        check_interval=30,
        alert_thresholds={
            "memory_usage": 80,
            "cpu_usage": 90,
            "error_rate": 5,
            "latency_p95": 1.0
        }
    )
    health_checker.start()
    
    # 3. 告警管理器
    alert_manager = AlertManager(
        webhook_url="https://hooks.slack.com/your-webhook",
        email_config={
            "smtp_server": "smtp.gmail.com",
            "username": "your-email@gmail.com",
            "password": "your-password"
        }
    )
    
    # 4. 设置监控规则
    setup_monitoring_rules(alert_manager)
    
    print("🔍 监控系统已启动")
    print(f"📊 Prometheus指标: http://localhost:8000/metrics")
    
    return metrics, health_checker, alert_manager

def setup_monitoring_rules(alert_manager):
    """设置监控规则"""
    
    # 延迟告警
    alert_manager.add_rule(
        name="high_latency",
        condition="signal_latency_p95 > 1.0",
        message="交易信号计算延迟过高",
        severity="warning"
    )
    
    # 错误率告警
    alert_manager.add_rule(
        name="high_error_rate", 
        condition="error_rate > 0.05",
        message="系统错误率超过5%",
        severity="critical"
    )
    
    # 内存使用告警
    alert_manager.add_rule(
        name="memory_usage",
        condition="memory_usage_percent > 80",
        message="内存使用率超过80%",
        severity="warning"
    )

if __name__ == "__main__":
    setup_comprehensive_monitoring()
    
    # 保持运行
    import time
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("监控系统已停止")
```

## 🔗 集成示例

### Jupyter Notebook 集成

```python
# examples/integration/jupyter_setup.py
def setup_jupyter_environment():
    """设置Jupyter笔记本环境"""
    
    # 安装必要的扩展
    import subprocess
    import sys
    
    extensions = [
        "matplotlib",
        "plotly", 
        "ipywidgets",
        "jupyter_contrib_nbextensions"
    ]
    
    for ext in extensions:
        subprocess.check_call([sys.executable, "-m", "pip", "install", ext])
    
    # 启用扩展
    subprocess.run(["jupyter", "contrib", "nbextension", "install", "--user"])
    subprocess.run(["jupyter", "nbextension", "enable", "variable_inspector/main"])
    
    print("✅ Jupyter环境配置完成")

# 在Jupyter中使用的辅助函数
def load_trading_environment():
    """加载交易环境到Jupyter"""
    
    # 导入必要模块
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    # 设置显示选项
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', 100)
    plt.style.use('seaborn-v0_8')
    
    # 导入交易模块
    from src.strategies.trend_following import TrendFollowingStrategy
    from src.core.backtesting import BacktestEngine
    from src.data.processors.data_processor import DataProcessor
    
    print("🚀 交易环境已加载到Jupyter")
    
    return {
        'pd': pd, 'np': np, 'plt': plt, 'go': go,
        'TrendFollowingStrategy': TrendFollowingStrategy,
        'BacktestEngine': BacktestEngine,
        'DataProcessor': DataProcessor
    }
```

## 📖 学习路径建议

### 初学者 (第1-2周)
1. 运行 `basic/simple_strategy.py` 理解策略基础
2. 学习 `basic/data_loading.py` 掌握数据处理
3. 尝试 `basic/backtesting_basic.py` 进行回测

### 中级用户 (第3-4周)  
1. 研究 `advanced/multi_strategy.py` 学习组合管理
2. 配置 `monitoring/metrics_setup.py` 建立监控
3. 使用 `integration/jupyter_notebook.ipynb` 进行分析

### 高级用户 (第5-8周)
1. 实现 `advanced/real_time_trading.py` 实盘交易
2. 优化 `advanced/portfolio_management.py` 投资组合
3. 自定义监控和告警系统

## 🆘 常见问题

### Q: 如何快速验证系统是否正常工作？
A: 运行 `basic/simple_strategy.py`，应该能看到正确的信号输出。

### Q: 监控系统无法启动怎么办？
A: 检查端口8000是否被占用，可以修改 `PROMETHEUS_PORT` 环境变量。

### Q: 实时交易连接失败？
A: 确认API密钥正确，网络连接正常，并且使用了正确的测试网地址。

---

📞 **需要帮助？** 请查看 [API文档](../docs/API_DOCUMENTATION.md) 或提交Issue。

*最后更新: 2024-12-20* 