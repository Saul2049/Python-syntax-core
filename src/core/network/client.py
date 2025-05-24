"""
网络客户端模块 (Network Client Module)

提供网络客户端基类，包括：
- 重试机制集成
- 状态管理集成
- 示例请求方法
"""

import logging
import random
import time
from typing import Any, Dict, Optional

from .retry_manager import DEFAULT_RETRY_CONFIG, RetryManager
from .state_manager import StateManager

# 设置日志记录器
logger = logging.getLogger(__name__)


class NetworkClient:
    """网络客户端基类，提供重试和状态恢复功能。
    Base network client class providing retry and state recovery functionality.
    """

    def __init__(
        self,
        state_dir: Optional[str] = None,
        retry_config: Optional[Dict[str, float]] = None,
        retry_exceptions: Optional[list[type]] = None,
    ):
        """
        初始化网络客户端。
        Initialize network client.

        参数 (Parameters):
            state_dir: 状态文件目录，默认为None (使用默认交易目录)
            retry_config: 重试配置
            retry_exceptions: 重试异常列表
        """
        # 初始化状态管理器
        self.state_manager = StateManager(state_dir)

        # 初始化重试管理器
        self.retry_manager = RetryManager(
            default_config=retry_config or DEFAULT_RETRY_CONFIG.copy(),
            default_exceptions=retry_exceptions
            or [
                ConnectionError,
                TimeoutError,
                OSError,
            ],
        )

    def get_state_path(self, operation: str):
        """
        获取特定操作的状态文件路径。
        Get state file path for specific operation.

        参数 (Parameters):
            operation: 操作名称 (Operation name)

        返回 (Returns):
            Path: 状态文件路径 (State file path)
        """
        return self.state_manager.get_state_path(operation)

    def save_operation_state(self, operation: str, state_data: Dict[str, Any]) -> bool:
        """
        保存操作状态。
        Save operation state.

        参数 (Parameters):
            operation: 操作名称 (Operation name)
            state_data: 状态数据 (State data)

        返回 (Returns):
            bool: 保存是否成功 (Whether save was successful)
        """
        return self.state_manager.save_operation_state(operation, state_data)

    def load_operation_state(self, operation: str) -> Dict[str, Any]:
        """
        加载操作状态。
        Load operation state.

        参数 (Parameters):
            operation: 操作名称 (Operation name)

        返回 (Returns):
            Dict[str, Any]: 状态数据 (State data)
        """
        return self.state_manager.load_operation_state(operation)

    def clear_operation_state(self, operation: str) -> bool:
        """
        清除操作状态。
        Clear operation state.

        参数 (Parameters):
            operation: 操作名称 (Operation name)

        返回 (Returns):
            bool: 清除是否成功 (Whether clear was successful)
        """
        return self.state_manager.clear_operation_state(operation)

    def execute_with_retry(
        self,
        func,
        *args,
        retry_config: Optional[Dict[str, float]] = None,
        retry_on_exceptions: Optional[list[type]] = None,
        **kwargs,
    ):
        """
        执行函数并应用重试逻辑

        参数:
            func: 要执行的函数
            *args: 函数参数
            retry_config: 重试配置
            retry_on_exceptions: 重试异常列表
            **kwargs: 函数关键字参数

        返回:
            函数执行结果
        """
        return self.retry_manager.execute_with_retry(
            func,
            *args,
            retry_config=retry_config,
            retry_on_exceptions=retry_on_exceptions,
            **kwargs,
        )

    def create_retry_decorator(
        self,
        retry_config: Optional[Dict[str, float]] = None,
        retry_on_exceptions: Optional[list[type]] = None,
    ):
        """
        创建重试装饰器

        参数:
            retry_config: 重试配置
            retry_on_exceptions: 重试异常列表

        返回:
            装饰器函数
        """
        return self.retry_manager.create_decorator(
            retry_config=retry_config,
            retry_on_exceptions=retry_on_exceptions,
        )

    def example_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        示例请求方法，展示如何使用重试装饰器。
        Example request method demonstrating how to use the retry decorator.

        参数 (Parameters):
            url: 请求URL (Request URL)
            params: 请求参数 (Request parameters)

        返回 (Returns):
            Dict[str, Any]: 响应数据 (Response data)
        """

        def _make_request():
            # 这里应该是实际的网络请求代码
            logger.info(f"Making request to {url} with params: {params}")

            # 模拟网络延迟
            time.sleep(0.5)

            # 模拟随机失败
            if random.random() < 0.3:  # 30% 失败率
                raise ConnectionError("Simulated network error")

            # 模拟成功响应
            return {"status": "success", "data": {"result": "some data"}}

        # 使用重试机制执行请求
        return self.execute_with_retry(_make_request)

    def get_status(self) -> Dict[str, Any]:
        """
        获取客户端状态信息

        返回:
            Dict[str, Any]: 状态信息
        """
        return {
            "state_manager": self.state_manager.get_state_summary(),
            "retry_config": self.retry_manager.default_config,
            "retry_exceptions": [exc.__name__ for exc in self.retry_manager.default_exceptions],
        }


class StatefulNetworkClient(NetworkClient):
    """
    有状态的网络客户端，自动管理请求状态
    Stateful network client that automatically manages request state
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._operation_counter = 0

    def _get_next_operation_id(self) -> str:
        """获取下一个操作ID"""
        self._operation_counter += 1
        return f"operation_{self._operation_counter}"

    def stateful_request(
        self,
        request_func,
        *args,
        operation_id: Optional[str] = None,
        save_state: bool = True,
        **kwargs,
    ):
        """
        执行有状态的请求

        参数:
            request_func: 请求函数
            *args: 函数参数
            operation_id: 操作ID，如果不提供则自动生成
            save_state: 是否保存状态
            **kwargs: 函数关键字参数

        返回:
            请求结果
        """
        if operation_id is None:
            operation_id = self._get_next_operation_id()

        if save_state:
            # 保存请求开始状态
            start_state = {
                "operation_id": operation_id,
                "status": "started",
                "args": str(args),  # 简化序列化
                "kwargs": {k: str(v) for k, v in kwargs.items() if k != "password"},
            }
            self.save_operation_state(operation_id, start_state)

        try:
            # 执行请求
            result = self.execute_with_retry(request_func, *args, **kwargs)

            if save_state:
                # 保存成功状态
                success_state = {
                    "operation_id": operation_id,
                    "status": "completed",
                    "result_summary": str(result)[:100],  # 只保存结果摘要
                }
                self.save_operation_state(operation_id, success_state)

            return result

        except Exception as e:
            if save_state:
                # 保存失败状态
                error_state = {
                    "operation_id": operation_id,
                    "status": "failed",
                    "error": str(e),
                }
                self.save_operation_state(operation_id, error_state)
            raise


# 便捷函数
def create_simple_client(state_dir: Optional[str] = None) -> NetworkClient:
    """
    创建简单的网络客户端

    参数:
        state_dir: 状态目录

    返回:
        NetworkClient: 网络客户端实例
    """
    return NetworkClient(state_dir=state_dir)


def create_stateful_client(state_dir: Optional[str] = None) -> StatefulNetworkClient:
    """
    创建有状态的网络客户端

    参数:
        state_dir: 状态目录

    返回:
        StatefulNetworkClient: 有状态网络客户端实例
    """
    return StatefulNetworkClient(state_dir=state_dir)
