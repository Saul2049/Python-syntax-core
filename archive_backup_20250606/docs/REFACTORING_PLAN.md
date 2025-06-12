# 代码质量改进计划 (Code Quality Improvement Plan)

## 1. 文件重构 (File Refactoring)

### 拆分 broker.py (974行 → 多个小文件)
```
src/
├── trading/
│   ├── __init__.py
│   ├── position_manager.py     # 仓位管理
│   ├── risk_calculator.py      # 风险计算 (ATR, 止损等)
│   ├── backtest_engine.py      # 回测引擎
│   └── order_executor.py       # 订单执行
├── indicators/
│   ├── __init__.py
│   ├── atr.py                  # ATR计算统一实现
│   └── moving_average.py       # 移动平均线
└── models/
    ├── __init__.py
    ├── position.py             # 仓位数据模型
    └── trade.py                # 交易数据模型
```

### 统一ATR计算
```python
# src/indicators/atr.py
def calculate_atr(
    high: pd.Series,
    low: pd.Series, 
    close: pd.Series,
    window: int = 14
) -> pd.Series:
    """统一的ATR计算函数"""
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=window).mean()
```

## 2. 解决依赖冲突 (Resolve Dependency Conflicts)

### 统一requirements.txt和pyproject.toml
```toml
# pyproject.toml中只保留核心依赖，版本范围要宽松
dependencies = [
    "pandas>=2.0.0,<3.0.0",
    "numpy>=1.24.0,<2.0.0", 
    "matplotlib>=3.7.0,<4.0.0",
    "tqdm>=4.66.0",
]
```

## 3. 降低函数复杂度 (Reduce Function Complexity)

### 重构 backtest_portfolio 函数
- 拆分为多个小函数：
  - `initialize_portfolio()`
  - `calculate_signals()`
  - `execute_trades()`
  - `update_positions()`
  - `calculate_returns()`

## 4. 解决循环导入 (Fix Circular Imports)

### 依赖注入模式
```python
# 使用依赖注入避免循环导入
class TradingEngine:
    def __init__(self, signal_generator, risk_manager, broker):
        self.signal_generator = signal_generator
        self.risk_manager = risk_manager
        self.broker = broker
```

## 5. 统一配置管理 (Unified Configuration)

### 简化config.py
```python
# 使用pydantic进行配置验证
from pydantic import BaseSettings

class TradingConfig(BaseSettings):
    symbols: List[str] = ["BTCUSDT", "ETHUSDT"]
    risk_percent: float = 0.01
    fast_ma: int = 7
    slow_ma: int = 25
    
    class Config:
        env_file = ".env"
```

## 6. 增加测试覆盖率 (Improve Test Coverage)

### 核心测试文件
```
tests/
├── unit/
│   ├── test_atr_calculation.py
│   ├── test_position_sizing.py
│   └── test_stop_loss.py
├── integration/
│   ├── test_trading_workflow.py
│   └── test_backtest_engine.py
└── fixtures/
    └── sample_data.py
```

## 7. 代码风格修复 (Code Style Fixes)

### 运行代码格式化工具
```bash
# 自动修复格式问题
black src/ tests/ --line-length 100
isort src/ tests/ --profile black
flake8 src/ tests/ --max-complexity 10
```

## 8. 性能优化 (Performance Optimization)

### 数据处理优化
- 使用numba加速ATR计算
- 避免在循环中重复计算
- 使用pandas向量化操作

## 实施优先级 (Implementation Priority)
1. **高优先级**: 修复代码风格问题，统一ATR计算
2. **中优先级**: 拆分大文件，解决循环导入
3. **低优先级**: 架构重构，性能优化

## 预期收益 (Expected Benefits)
- 代码可维护性提升 60%
- 测试覆盖率达到 85%+
- 开发效率提升 40%
- 代码重复率降低 70% 