# 避免测试卡死的最佳实践 (Avoiding Test Hangs)

## 🚨 问题分析

测试卡死的常见原因：

### 1. 网络请求超时 (Network Request Timeout)
- **问题**: 测试尝试进行真实的API调用
- **现象**: 测试在网络请求处停止响应
- **解决**: 始终Mock网络请求

### 2. 异步睡眠调用 (Async Sleep Calls)  
- **问题**: 使用了真实的 `asyncio.sleep()` 或 `time.sleep()`
- **现象**: 测试长时间等待睡眠结束
- **解决**: Mock所有睡眠函数

### 3. 无限循环 (Infinite Loops)
- **问题**: 某些条件永远不满足，导致死循环
- **现象**: CPU使用率高，测试永不结束
- **解决**: 添加超时保护和循环计数器

### 4. 资源锁定 (Resource Locking)
- **问题**: 文件、数据库或其他资源被锁定
- **现象**: 测试等待资源释放
- **解决**: 使用临时资源和适当的清理

## 🛡️ 解决方案

### 1. 使用超时保护
```python
import pytest

@pytest.mark.timeout(30)  # 30秒超时
def test_example():
    # 测试代码
    pass
```

### 2. Mock所有外部依赖
```python
from unittest.mock import patch

@patch('requests.get')
@patch('time.sleep')
@patch('asyncio.sleep')
def test_with_mocks(mock_sleep, mock_time_sleep, mock_get):
    # 配置Mock响应
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {'data': 'test'}
    
    # 测试代码
    pass
```

### 3. 使用安全的测试运行器
```python
from tests.test_safe_runner import run_safe_test

def my_test():
    # 测试逻辑
    pass

# 安全运行，5秒超时
success, error = run_safe_test(my_test, timeout_seconds=5)
assert success, f"Test failed: {error}"
```

## 🔧 具体修复策略

### 对于网络相关测试
```python
# ❌ 错误做法 - 真实网络请求
def test_api_call():
    response = requests.get("https://api.binance.com/api/v3/ticker/price")
    assert response.status_code == 200

# ✅ 正确做法 - Mock网络请求
@patch('requests.get')
def test_api_call(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {'symbol': 'BTCUSDT', 'price': '50000'}
    
    response = requests.get("https://api.binance.com/api/v3/ticker/price")
    assert response.status_code == 200
```

### 对于异步测试
```python
# ❌ 错误做法 - 真实睡眠
@pytest.mark.asyncio
async def test_async_function():
    await asyncio.sleep(5)  # 会真的等待5秒
    assert True

# ✅ 正确做法 - Mock睡眠
@pytest.mark.asyncio
@patch('asyncio.sleep')
async def test_async_function(mock_sleep):
    mock_sleep.return_value = None
    await asyncio.sleep(5)  # 立即返回
    assert True
```

### 对于循环逻辑
```python
# ❌ 错误做法 - 可能的无限循环
def test_retry_logic():
    attempts = 0
    while not some_condition():  # 如果条件永不满足...
        attempts += 1
        # 可能的无限循环

# ✅ 正确做法 - 有限制的循环
def test_retry_logic():
    attempts = 0
    max_attempts = 10
    while attempts < max_attempts and not some_condition():
        attempts += 1
    
    assert attempts <= max_attempts
```

## 🚀 推荐的测试配置

### pytest.ini 配置
```ini
[tool:pytest]
timeout = 30
timeout_method = thread
addopts = --timeout=30 --maxfail=3 -ra
```

### conftest.py 全局Mock配置
```python
import pytest
from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_slow_operations():
    """自动Mock慢操作"""
    with patch('time.sleep'), \
         patch('asyncio.sleep'), \
         patch('requests.get'), \
         patch('requests.post'):
        yield
```

## 📊 测试分类建议

### 按执行时间分类
- **Fast Tests** (<1s): 单元测试，纯逻辑测试
- **Medium Tests** (1-10s): 集成测试，有Mock的网络测试  
- **Slow Tests** (>10s): 端到端测试，真实环境测试

### 分离运行策略
```bash
# 只运行快速测试
pytest -m "not slow" --timeout=10

# 运行所有测试，但有超时保护
pytest --timeout=30 --maxfail=5

# 单独运行慢测试（更长超时）
pytest -m slow --timeout=120
```

## 🔍 问题调试

### 找出卡死的测试
```bash
# 使用详细输出模式
pytest -v -s --tb=short

# 限制失败数量，快速定位问题
pytest --maxfail=1 --tb=short

# 运行特定测试文件
pytest tests/test_specific.py -v
```

### 监控测试执行
```bash
# 显示最慢的测试
pytest --durations=10

# 实时显示测试名称
pytest -v --tb=line
```

## ⚡ 性能优化

### 并行测试 (需要 pytest-xdist)
```bash
pip install pytest-xdist
pytest -n auto  # 自动使用所有CPU核心
pytest -n 4     # 使用4个并行进程
```

### 选择性运行
```bash
# 只运行失败的测试
pytest --lf

# 只运行特定标记的测试
pytest -m "unit and not slow"

# 跳过慢测试
pytest -m "not slow"
```

## 📝 总结

遵循这些最佳实践可以有效避免测试卡死：

1. **始终Mock外部依赖** - 网络、文件系统、时间
2. **设置超时保护** - 防止测试无限等待
3. **分类测试** - 按速度和类型分离
4. **使用安全运行器** - 自动化保护机制
5. **监控和调试** - 快速定位问题测试

记住：**好的测试应该是快速、可靠、可重复的**! 🎯 