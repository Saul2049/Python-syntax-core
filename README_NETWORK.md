# 网络重试和状态持久化 (Network Retry and State Persistence)

本文档介绍如何使用网络重试和状态持久化功能来处理网络中断和应用重启。
This document explains how to use network retry and state persistence to handle network interruptions and application restarts.

## 功能概述 (Features Overview)

1. **自动重试机制 (Automatic Retry Mechanism)**
   - 指数退避算法 (Exponential backoff algorithm)
   - 可配置的重试参数 (Configurable retry parameters)
   - 抖动机制避免雪崩效应 (Jitter to avoid retry storms)

2. **状态持久化 (State Persistence)**
   - 自动保存函数调用状态 (Automatic saving of function call state)
   - 在应用重启后恢复状态 (Resume state after application restart)
   - 支持增量数据同步 (Support for incremental data synchronization)

3. **异常处理 (Exception Handling)**
   - 针对不同类型的网络错误定制重试策略 (Customized retry strategies for different network errors)
   - 清晰的错误日志 (Clear error logging)
   - 错误状态持久化 (Error state persistence)

## 使用方法 (Usage)

### 1. 重试装饰器 (Retry Decorator)

```python
from src.network import with_retry

@with_retry(
    retry_config={"max_retries": 5, "base_delay": 1.0},
    retry_on_exceptions=[ConnectionError, TimeoutError],
    state_file="my_operation"
)
def my_network_function(param1, param2):
    # 函数实现 (Function implementation)
    pass
```

### 2. 配置参数 (Configuration Parameters)

```python
# 默认重试配置 (Default retry configuration)
DEFAULT_RETRY_CONFIG = {
    "max_retries": 5,          # 最大重试次数 (Maximum retry attempts)
    "base_delay": 1.0,         # 基础延迟秒数 (Base delay in seconds)
    "max_delay": 60.0,         # 最大延迟秒数 (Maximum delay in seconds)
    "backoff_factor": 2.0,     # 退避因子 (Backoff factor)
    "jitter": 0.1,             # 抖动系数 (Jitter coefficient)
}
```

### 3. 使用 NetworkClient 类 (Using NetworkClient Class)

```python
from src.network import NetworkClient

class MyClient(NetworkClient):
    def __init__(self, api_key, api_secret):
        super().__init__()
        self.api_key = api_key
        self.api_secret = api_secret
        
    @with_retry(state_file="get_data")
    def get_data(self, param1, param2):
        # 实现 (Implementation)
        pass
        
    # 手动管理状态 (Manual state management)
    def long_running_task(self):
        operation = "long_task"
        state = self.load_operation_state(operation)
        
        # 检查已完成的步骤 (Check completed steps)
        completed_steps = state.get("completed_steps", [])
        
        # 执行未完成的步骤 (Execute incomplete steps)
        for step in range(10):
            if step not in completed_steps:
                # 执行步骤 (Execute step)
                
                # 更新状态 (Update state)
                completed_steps.append(step)
                self.save_operation_state(operation, {
                    "completed_steps": completed_steps
                })
```

## 运行示例 (Running the Example)

提供了一个示例脚本展示如何使用网络重试和状态持久化功能：
An example script is provided to demonstrate how to use network retry and state persistence functionality:

```bash
# 运行示例 (Run example)
python examples/retry_example.py
```

这个示例演示了：
This example demonstrates:

1. 自动重试网络请求 (Automatic retry of network requests)
2. 在失败时保存状态 (State saving on failure)
3. 在重启后恢复状态 (State recovery after restart)
4. 增量数据同步 (Incremental data synchronization)

## 最佳实践 (Best Practices)

1. **状态文件命名 (State File Naming)**
   - 使用有意义的名称，包含操作和参数信息
   - 例如：`order_btcusdt_buy_20230101`

2. **状态文件清理 (State File Cleanup)**
   - 定期清理已完成的状态文件
   - 可以实现一个定期清理任务

3. **敏感信息处理 (Handling Sensitive Information)**
   - 避免在状态文件中保存敏感信息（密码、API密钥等）
   - 使用过滤器排除敏感参数

4. **错误处理 (Error Handling)**
   - 区分临时错误（应重试）和永久错误（不应重试）
   - 对于重试后仍然失败的操作，实现手动恢复机制

5. **日志记录 (Logging)**
   - 详细记录每次重试的信息
   - 记录状态保存和恢复操作

## 常见问题 (Common Issues)

1. **状态文件冲突 (State File Conflicts)**
   - 问题：多个请求使用相同的状态文件
   - 解决：为每个请求使用唯一的状态文件名，包含参数信息

2. **状态文件过大 (Large State Files)**
   - 问题：保存大量数据导致状态文件过大
   - 解决：只保存必要的元数据，使用分页或流式处理大数据

3. **无法序列化的数据 (Non-serializable Data)**
   - 问题：某些对象无法JSON序列化
   - 解决：实现自定义序列化方法或只保存可序列化的数据 