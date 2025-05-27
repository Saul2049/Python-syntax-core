# 🔧 专业交易系统 API 文档

## 📋 目录
- [核心模块 API](#核心模块-api)
- [交易策略 API](#交易策略-api)
- [监控系统 API](#监控系统-api)
- [数据处理 API](#数据处理-api)
- [使用示例](#使用示例)

---

## 🏗️ 核心模块 API

### TradingEngine (交易引擎)

核心交易引擎，负责策略执行和订单管理。

#### 类定义
```python
class TradingEngine:
    def __init__(self, config: Dict[str, Any])
```

#### 主要方法

##### start()
启动交易引擎
```python
def start() -> None
```
**功能**: 初始化并启动交易引擎的所有组件
**参数**: 无
**返回**: 无
**异常**: `TradingEngineError` 如果启动失败

**示例**:
```python
engine = TradingEngine(config)
engine.start()
```

##### add_strategy()
添加交易策略
```python
def add_strategy(strategy: BaseStrategy) -> None
```
**参数**:
- `strategy`: 继承自BaseStrategy的策略实例

**示例**:
```python
from src.strategies.trend_following import TrendFollowingStrategy
strategy = TrendFollowingStrategy(period=20)
engine.add_strategy(strategy)
```

##### get_performance()
获取性能统计
```python
def get_performance() -> Dict[str, Any]
```
**返回**: 包含性能指标的字典
- `total_return`: 总收益率
- `sharpe_ratio`: 夏普比率
- `max_drawdown`: 最大回撤
- `win_rate`: 胜率

---

## 🧠 交易策略 API

### BaseStrategy (基础策略)

所有交易策略的基类，定义了标准接口。

#### 抽象方法

##### generate_signals()
生成交易信号（必须实现）
```python
@abstractmethod
def generate_signals(data: pd.DataFrame) -> Dict[str, Any]
```
**参数**:
- `data`: 市场数据DataFrame，必须包含close、volume列

**返回**: 信号字典
```python
{
    "signal": "BUY" | "SELL" | "HOLD",
    "confidence": float,  # 0-1之间
    "timestamp": datetime,
    "price": float,
    "metadata": Dict[str, Any]  # 可选的额外信息
}
```

#### 实用方法

##### validate_data()
验证数据有效性
```python
def validate_data(data: pd.DataFrame) -> bool
```

##### calculate_returns()
计算收益率
```python
def calculate_returns(data: pd.DataFrame, price_column: str = "close") -> pd.Series
```

##### set_parameter() / get_parameter()
参数管理
```python
def set_parameter(key: str, value: Any) -> None
def get_parameter(key: str, default: Any = None) -> Any
```

### TrendFollowingStrategy

趋势跟踪策略的具体实现。

#### 初始化参数
```python
TrendFollowingStrategy(
    fast_period: int = 12,     # 快速移动平均周期
    slow_period: int = 26,     # 慢速移动平均周期  
    signal_period: int = 9,    # 信号线周期
    rsi_period: int = 14,      # RSI周期
    rsi_overbought: float = 70, # RSI超买阈值
    rsi_oversold: float = 30   # RSI超卖阈值
)
```

#### 使用示例
```python
from src.strategies.trend_following import TrendFollowingStrategy

# 创建策略实例
strategy = TrendFollowingStrategy(
    fast_period=10,
    slow_period=20,
    rsi_period=14
)

# 设置参数
strategy.set_parameter("rsi_overbought", 75)

# 生成信号
signals = strategy.generate_signals(market_data)
print(f"信号: {signals['signal']}, 置信度: {signals['confidence']}")
```

---

## 📊 监控系统 API

### TradingMetricsCollector

交易系统的核心监控组件，基于Prometheus指标。

#### 初始化
```python
from src.monitoring.metrics_collector import get_metrics_collector

metrics = get_metrics_collector()
metrics.start_server()  # 启动Prometheus服务器
```

#### 主要方法

##### 延迟测量
```python
# 测量信号计算延迟
with metrics.measure_signal_latency():
    signals = strategy.generate_signals(data)

# 测量订单执行延迟  
with metrics.measure_order_latency():
    order_result = broker.place_order(...)
```

##### 性能指标记录
```python
# 记录账户余额
metrics.update_account_balance(10000.0)

# 记录滑点
metrics.record_slippage(expected_price=100.0, actual_price=100.5)

# 记录异常
try:
    risky_operation()
except Exception as e:
    metrics.record_exception("trading_module", e)
```

##### WebSocket监控
```python
# 记录WebSocket延迟
metrics.observe_ws_latency(0.05)  # 50ms

# 记录价格更新
metrics.record_price_update("BTCUSDT", 45000.0, source="ws")

# 记录重连事件
metrics.record_ws_reconnect("BTCUSDT", reason="connection_lost")
```

#### 指标访问
所有指标可通过 `http://localhost:8000/metrics` 访问，支持Grafana可视化。

---

## 📈 数据处理 API

### DataProcessor

高性能数据处理组件，支持向量化操作。

#### 创建实例
```python
from src.data.processors.data_processor import DataProcessor

processor = DataProcessor(
    cache_size=1000,        # 缓存大小
    enable_vectorization=True,  # 启用向量化
    parallel_workers=4      # 并行工作线程数
)
```

#### 主要方法

##### 技术指标计算
```python
# 计算移动平均
ma_data = processor.calculate_moving_average(
    data=price_data, 
    period=20,
    column="close"
)

# 计算RSI
rsi_data = processor.calculate_rsi(
    data=price_data,
    period=14
)

# 计算MACD
macd_data = processor.calculate_macd(
    data=price_data,
    fast_period=12,
    slow_period=26,
    signal_period=9
)
```

##### 数据验证
```python
# 验证数据质量
is_valid = processor.validate_ohlc_data(market_data)

# 检查缺失值
missing_stats = processor.check_missing_values(market_data)
```

##### 批量处理
```python
# 并行处理多个数据集
results = processor.process_multiple_datasets([
    {"data": btc_data, "indicators": ["rsi", "macd"]},
    {"data": eth_data, "indicators": ["sma", "ema"]}
])
```

---

## 💡 使用示例

### 完整交易系统示例

```python
import pandas as pd
from src.core.trading_engine import TradingEngine
from src.strategies.trend_following import TrendFollowingStrategy
from src.monitoring.metrics_collector import get_metrics_collector
from src.brokers.live_broker_async import LiveBrokerAsync

# 1. 配置系统
config = {
    "risk_management": {
        "max_position_size": 0.02,
        "max_drawdown": 0.1
    },
    "data_source": {
        "provider": "binance",
        "symbols": ["BTCUSDT", "ETHUSDT"]
    }
}

# 2. 初始化组件
engine = TradingEngine(config)
metrics = get_metrics_collector()

# 3. 创建策略
strategy = TrendFollowingStrategy(
    fast_period=12,
    slow_period=26,
    rsi_period=14
)

# 4. 配置异步代理
async def setup_trading():
    async with LiveBrokerAsync(api_key, api_secret, testnet=True) as broker:
        engine.set_broker(broker)
        engine.add_strategy(strategy)
        
        # 启动监控
        metrics.start_server()
        
        # 开始交易
        await engine.run_async()

# 5. 运行系统
import asyncio
asyncio.run(setup_trading())
```

### 策略回测示例

```python
from src.core.backtesting import BacktestEngine
from src.strategies.improved_strategy import ImprovedStrategy

# 加载历史数据
data = pd.read_csv("btc_historical_data.csv")
data['timestamp'] = pd.to_datetime(data['timestamp'])
data.set_index('timestamp', inplace=True)

# 创建回测引擎
backtest = BacktestEngine(
    initial_capital=10000,
    commission=0.001,
    slippage=0.0005
)

# 创建策略
strategy = ImprovedStrategy(
    lookback_period=20,
    volatility_threshold=0.02
)

# 运行回测
results = backtest.run(
    strategy=strategy,
    data=data,
    start_date="2024-01-01",
    end_date="2024-12-01"
)

# 分析结果
print(f"总收益率: {results['total_return']:.2%}")
print(f"夏普比率: {results['sharpe_ratio']:.2f}")
print(f"最大回撤: {results['max_drawdown']:.2%}")
print(f"胜率: {results['win_rate']:.2%}")
```

### 实时监控示例

```python
import time
from src.monitoring.health_checker import HealthChecker

# 创建健康检查器
health_checker = HealthChecker(
    check_interval=30,  # 30秒检查一次
    alert_thresholds={
        "memory_usage": 80,     # 内存使用超过80%报警
        "cpu_usage": 90,        # CPU使用超过90%报警
        "error_rate": 5         # 错误率超过5%报警
    }
)

# 启动健康监控
health_checker.start()

# 获取系统健康状态
while True:
    status = health_checker.get_health_status()
    
    if status["status"] == "unhealthy":
        print(f"⚠️ 系统异常: {status['issues']}")
        # 执行恢复措施
    
    time.sleep(60)  # 每分钟检查一次
```

---

## 🔗 相关链接

- [开发指南](DEVELOPMENT_GUIDE.md)
- [部署文档](DEPLOYMENT.md)
- [性能优化指南](PERFORMANCE_OPTIMIZATION.md)
- [故障排除](TROUBLESHOOTING.md)

---

*最后更新: 2024-12-20* 