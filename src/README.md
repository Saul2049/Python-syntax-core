# 📦 Source Code Directory (源代码目录)

这里包含了专业交易系统的核心业务代码。

## 📂 目录结构

### 🧠 `/core/` - 核心模块
- `signal_processor.py` - 信号处理器
- `position_management.py` - 仓位管理
- `price_fetcher.py` - 价格获取
- `trading_engine.py` - 交易引擎

### 📈 `/strategies/` - 交易策略
- `moving_average.py` - 移动平均策略
- `oscillator.py` - 振荡器策略
- `breakout.py` - 突破策略
- `trend_following.py` - 趋势跟踪策略
- `improved_strategy.py` - 改进策略

### 📊 `/indicators/` - 技术指标
- `moving_averages.py` - 移动平均指标
- `momentum_indicators.py` - 动量指标
- `volatility_indicators.py` - 波动率指标

### 💰 `/brokers/` - 经纪商接口
- `binance/` - 币安接口
- `simulator/` - 市场模拟器

### 📁 `/data/` - 数据处理
- `processors/` - 数据处理器
- `transformers/` - 数据转换器

### 📈 `/monitoring/` - 监控系统
- `prometheus_exporter.py` - Prometheus导出器
- `metrics_collector.py` - 指标收集器
- `health_checker.py` - 健康检查
- `alert_manager.py` - 告警管理

### 🔧 `/config/` - 配置管理
- `config_utils.py` - 配置工具

### 🛠️ `/tools/` - 工具模块
- 数据分析和处理工具

## 📝 根目录主要文件

- `trading_loop.py` - 主要交易循环
- `backtest.py` - 回测引擎
- `telegram.py` - Telegram通知
- `utils.py` - 通用工具函数
- `metrics.py` - 指标计算
- `config.py` - 配置管理

## 🚀 快速开始

```python
# 导入核心模块
from src.strategies import SimpleMAStrategy
from src.core import TradingEngine

# 创建策略
strategy = SimpleMAStrategy(short_window=5, long_window=20)

# 创建交易引擎
engine = TradingEngine(strategy)
```

## 📋 开发规范

1. **模块化设计**: 每个模块职责单一，接口清晰
2. **类型注解**: 所有公共接口都使用类型注解
3. **文档字符串**: 所有类和函数都有完整的文档
4. **测试覆盖**: 核心模块保持高测试覆盖率
5. **错误处理**: 完善的异常处理和日志记录 