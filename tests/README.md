# 🧪 Tests Directory (测试目录)

这里包含了专业交易系统的测试套件，确保代码质量和功能正确性。

## 📊 测试状态

- ✅ **测试通过率**: 100% (1462/1462)
- ✅ **代码覆盖率**: 86% (行业优秀水平)
- ✅ **测试数量**: 1462个测试用例

## 📂 测试文件组织

### 🧠 核心模块测试
- `test_core_signal_processor.py` - 信号处理器测试
- `test_core_position_management.py` - 仓位管理测试
- `test_core_trading_engine.py` - 交易引擎测试
- `test_core_network.py` - 网络模块测试

### 📈 策略测试
- `test_improved_strategy.py` - 改进策略测试
- `test_snapshots.py` - 策略快照测试

### 💰 经纪商测试
- `test_brokers_binance_client.py` - 币安客户端测试
- `test_broker.py` - 经纪商接口测试
- `test_broker_single.py` - 单一经纪商测试

### 📁 数据处理测试
- `test_data_processors.py` - 数据处理器测试
- `test_utils.py` - 工具函数测试

### 📈 监控系统测试
- `test_monitoring.py` - 监控系统测试
- `test_telegram_module.py` - Telegram模块测试
- `test_telegram.py` - Telegram通知测试

### ⚙️ 配置和稳定性测试
- `test_config.py` - 配置管理测试
- `test_config_refactoring.py` - 配置重构测试
- `test_stability.py` - 稳定性测试

### 🔧 其他测试
- `test_indicators.py` - 技术指标测试
- `test_signals.py` - 信号测试
- `test_metrics.py` - 指标测试
- `test_notify.py` - 通知测试
- `test_portfolio.py` - 投资组合测试

## 🚀 运行测试

### 运行所有测试
```bash
python -m pytest
```

### 运行特定测试文件
```bash
python -m pytest tests/test_core_signal_processor.py -v
```

### 生成覆盖率报告
```bash
python -m pytest --cov=src --cov-report=html
```

### 运行快速测试（跳过慢速测试）
```bash
python -m pytest -m "not slow"
```

## 📋 测试规范

### 测试文件命名
- 测试文件以 `test_` 开头
- 测试文件名对应被测试的模块名
- 测试类以 `Test` 开头
- 测试方法以 `test_` 开头

### 测试结构
```python
import unittest
from src.module import TargetClass

class TestTargetClass(unittest.TestCase):
    def setUp(self):
        """测试前准备"""
        pass
    
    def test_basic_functionality(self):
        """测试基础功能"""
        pass
    
    def test_edge_cases(self):
        """测试边界情况"""
        pass
    
    def test_error_handling(self):
        """测试错误处理"""
        pass
```

### 测试类型
1. **单元测试**: 测试单个函数或方法
2. **集成测试**: 测试模块间的交互
3. **功能测试**: 测试完整的业务流程
4. **边界测试**: 测试边界条件和异常情况

## 📈 覆盖率目标

- **核心模块**: 90%+ 覆盖率
- **策略模块**: 85%+ 覆盖率
- **工具模块**: 80%+ 覆盖率
- **整体项目**: 86%+ 覆盖率 ✅

## 🔗 相关文档

- [`../src/README.md`](../src/README.md) - 源代码结构说明
- [`../archive/old_tests/`](../archive/old_tests/) - 历史测试文件
- [`../archive/coverage_reports/`](../archive/coverage_reports/) - 历史覆盖率报告 