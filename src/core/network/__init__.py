"""
网络核心模块 (Network Core Module)

提供网络相关的核心功能：
- 重试管理
- 状态管理
- 网络客户端基类
- 高级装饰器
"""

from .client import (
    NetworkClient,
    StatefulNetworkClient,
    create_simple_client,
    create_stateful_client,
)
from .decorators import (
    api_call,
    critical_operation,
    network_request,
    with_comprehensive_retry,
    with_retry,
    with_state_management,
)
from .retry_manager import (
    DEFAULT_RETRY_CONFIG,
    RetryManager,
    calculate_retry_delay,
    create_retry_decorator,
    retry,
)
from .state_manager import (
    StateManager,
    clear_state,
    get_global_state_manager,
    load_state,
    save_state,
    set_global_state_dir,
)

__all__ = [
    # 重试管理
    "calculate_retry_delay",
    "create_retry_decorator",
    "retry",
    "RetryManager",
    "DEFAULT_RETRY_CONFIG",
    # 状态管理
    "save_state",
    "load_state",
    "clear_state",
    "StateManager",
    "get_global_state_manager",
    "set_global_state_dir",
    # 网络客户端
    "NetworkClient",
    "StatefulNetworkClient",
    "create_simple_client",
    "create_stateful_client",
    # 高级装饰器
    "with_retry",
    "with_state_management",
    "with_comprehensive_retry",
    "network_request",
    "api_call",
    "critical_operation",
]
