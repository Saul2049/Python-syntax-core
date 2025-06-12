# 测试覆盖率提升计划 (Test Coverage Improvement Plan)

## 📈 当前状态
- **整体覆盖率**: 68% (4576/6717 行代码已覆盖)
- **目标覆盖率**: 85%+ 
- **需要改进的代码行数**: ~1400 行

## 🎯 优先级改进列表

### Priority 1: 零覆盖率模块 (0% Coverage)
1. **src/data.py** (38 行) - 数据处理核心模块
2. **src/core/signal_cache.py** (11 行) - 信号缓存模块
3. **src/indicators/moving_average.py** (26 行) - 移动平均指标

### Priority 2: 极低覆盖率模块 (< 30%)
1. **src/ws/binance_ws_client.py** (16%) - WebSocket 客户端
2. **src/core/price_fetcher.py** (16%) - 价格获取器
3. **src/data/transformers/data_transformers.py** (22%) - 数据转换器
4. **src/indicators/momentum_indicators.py** (27%) - 动量指标
5. **src/indicators/volatility_indicators.py** (27%) - 波动率指标

### Priority 3: 中等覆盖率模块 (30-70%)
1. **src/monitoring/prometheus_exporter.py** (41%) - Prometheus 导出器
2. **src/config/utils.py** (42%) - 配置工具
3. **src/data/transformers/missing_values.py** (36%) - 缺失值处理
4. **src/strategies/breakout.py** (51%) - 突破策略
5. **src/monitoring/health_checker.py** (61%) - 健康检查器

## 🛠 具体改进措施

### 1. 创建专门的测试文件
- `test_data_core.py` - 测试 src/data.py
- `test_signal_cache.py` - 测试信号缓存功能
- `test_indicators_comprehensive.py` - 全面测试技术指标
- `test_websocket_client.py` - 测试 WebSocket 连接

### 2. 增强现有测试
- 添加边界条件测试 (Edge Cases)
- 添加异常处理测试 (Exception Handling)
- 添加集成测试 (Integration Tests)
- 添加性能测试 (Performance Tests)

### 3. Mock 和 Fixture 改进
- 改进 Telegram 环境变量 Mock
- 创建通用的测试数据 Fixtures
- 改进网络请求 Mock

### 4. 配置改进
- 修复 pytest 配置中的 asyncio 警告
- 优化 coverage 配置
- 添加测试环境变量配置

## 📋 实施步骤

### Phase 1: 快速胜利 (Quick Wins)
1. 修复现有失败的测试 (20个失败测试)
2. 为零覆盖率模块添加基础测试
3. 改进环境变量处理

### Phase 2: 系统性改进
1. 为低覆盖率模块添加全面测试
2. 重构重复的测试代码
3. 添加集成测试

### Phase 3: 高级优化
1. 添加性能测试
2. 添加压力测试
3. 完善文档和示例

## 🎯 覆盖率目标

| 模块类型 | 当前覆盖率 | 目标覆盖率 |
|---------|-----------|-----------|
| 核心模块 (core/) | 73% | 90%+ |
| 策略模块 (strategies/) | 64% | 85%+ |
| 数据模块 (data/) | 32% | 80%+ |
| 指标模块 (indicators/) | 49% | 85%+ |
| 监控模块 (monitoring/) | 54% | 75%+ |
| 经纪人模块 (brokers/) | 79% | 90%+ |

## 📊 预期结果
通过以上改进，预期整体覆盖率从 **68%** 提升到 **85%+** 