import json
import logging
import os
import random
import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from src import utils

# 设置日志记录器 (Setup logger)
logger = logging.getLogger(__name__)

# 定义类型变量 (Define type variables)
T = TypeVar("T")  # 函数返回类型 (Function return type)

# 默认重试参数 (Default retry parameters)
DEFAULT_RETRY_CONFIG = {
    "max_retries": 5,  # 最大重试次数 (Maximum retry attempts)
    "base_delay": 1.0,  # 基础延迟秒数 (Base delay in seconds)
    "max_delay": 60.0,  # 最大延迟秒数 (Maximum delay in seconds)
    "backoff_factor": 2.0,  # 退避因子 (Backoff factor)
    "jitter": 0.1,  # 抖动系数 (Jitter coefficient)
}


def calculate_retry_delay(attempt: int, config: Dict[str, float]) -> float:
    """
    计算重试延迟时间（带抖动的指数退避）。
    Calculate retry delay time (exponential backoff with jitter).

    参数 (Parameters):
        attempt: 当前尝试次数，从1开始 (Current attempt number, starting from 1)
        config: 重试配置参数 (Retry configuration parameters)

    返回 (Returns):
        float: 延迟秒数 (Delay in seconds)
    """
    base_delay = config.get("base_delay", DEFAULT_RETRY_CONFIG["base_delay"])
    max_delay = config.get("max_delay", DEFAULT_RETRY_CONFIG["max_delay"])
    backoff_factor = config.get(
        "backoff_factor", DEFAULT_RETRY_CONFIG["backoff_factor"]
    )
    jitter = config.get("jitter", DEFAULT_RETRY_CONFIG["jitter"])

    # 计算指数退避 (Calculate exponential backoff)
    delay = min(max_delay, base_delay * (backoff_factor ** (attempt - 1)))

    # 添加随机抖动 (Add random jitter)
    jitter_amount = delay * jitter
    delay = random.uniform(delay - jitter_amount, delay + jitter_amount)

    return max(0, delay)  # 确保延迟非负 (Ensure delay is non-negative)


def save_state(state_path: Path, state_data: Dict[str, Any]) -> bool:
    """
    保存状态到JSON文件。
    Save state to JSON file.

    参数 (Parameters):
        state_path: 状态文件路径 (State file path)
        state_data: 要保存的状态数据 (State data to save)

    返回 (Returns):
        bool: 保存是否成功 (Whether save was successful)
    """
    try:
        # 确保目录存在 (Ensure directory exists)
        state_path.parent.mkdir(parents=True, exist_ok=True)

        # 添加时间戳 (Add timestamp)
        state_data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 写入JSON文件 (Write to JSON file)
        with open(state_path, "w") as f:
            json.dump(state_data, f, indent=2)

        logger.debug(f"State saved to {state_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to save state: {e}")
        return False


def load_state(state_path: Path) -> Dict[str, Any]:
    """
    从JSON文件加载状态。
    Load state from JSON file.

    参数 (Parameters):
        state_path: 状态文件路径 (State file path)

    返回 (Returns):
        Dict[str, Any]: 加载的状态数据，如果失败则返回空字典
        (Loaded state data, returns empty dict if failed)
    """
    try:
        if not state_path.exists():
            logger.debug(f"State file not found: {state_path}")
            return {}

        with open(state_path, "r") as f:
            state_data = json.load(f)

        logger.debug(f"State loaded from {state_path}")
        return state_data

    except Exception as e:
        logger.error(f"Failed to load state: {e}")
        return {}


def with_retry(
    retry_config: Optional[Dict[str, float]] = None,
    retry_on_exceptions: Optional[List[type]] = None,
    state_file: Optional[str] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    网络请求重试装饰器，支持状态保存和恢复。
    Network request retry decorator with state persistence.

    参数 (Parameters):
        retry_config: 重试配置，包含重试次数和延迟参数
                    (Retry configuration with retry count and delay parameters)
        retry_on_exceptions: 需要重试的异常类型列表
                          (List of exception types to retry on)
        state_file: 状态文件名，用于保存进度，默认为None
                  (State filename for saving progress, default None)

    返回 (Returns):
        Callable: 装饰器函数 (Decorator function)
    """
    # 使用默认配置 (Use default configuration)
    if retry_config is None:
        retry_config = DEFAULT_RETRY_CONFIG.copy()

    # 使用默认异常列表 (Use default exception list)
    if retry_on_exceptions is None:
        retry_on_exceptions = [
            ConnectionError,  # 连接错误 (Connection error)
            TimeoutError,  # 超时错误 (Timeout error)
            OSError,  # 操作系统错误 (OS error)
        ]

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            max_retries = retry_config.get(
                "max_retries", DEFAULT_RETRY_CONFIG["max_retries"]
            )
            state_data = {}
            state_path = None

            # 确定状态文件路径 (Determine state file path)
            if state_file:
                state_dir = Path(utils.get_trades_dir()) / "states"
                state_path = state_dir / f"{state_file}.json"

                # 加载已有状态 (Load existing state)
                state_data = load_state(state_path)

                # 从状态恢复参数 (Restore parameters from state)
                if "saved_args" in state_data and "saved_kwargs" in state_data:
                    logger.info(f"Resuming from saved state in {state_path}")

                    # 可以选择性地恢复参数 (Optionally restore parameters)
                    # 此处是一个简化示例，实际应用可能需要更复杂的处理
                    # This is a simplified example, actual applications may need more complex handling
                    if "resume_params" in kwargs and kwargs.get("resume_params", False):
                        # 仅在显式要求时恢复参数 (Only restore parameters when explicitly requested)
                        saved_kwargs = state_data["saved_kwargs"]
                        for key, value in saved_kwargs.items():
                            if key not in kwargs:
                                kwargs[key] = value

            attempt = 0
            last_exception = None

            while attempt <= max_retries:
                try:
                    if attempt > 0:
                        delay = calculate_retry_delay(attempt, retry_config)
                        logger.info(
                            f"Retry {attempt}/{max_retries} after {delay:.2f}s delay"
                        )
                        time.sleep(delay)

                    # 保存当前调用状态 (Save current call state)
                    if state_path:
                        # 注意：这里简单地保存了参数，但应考虑安全性和大小限制
                        # Note: This simply saves the parameters, but security and size limits should be considered
                        current_state = {
                            "function": func.__name__,
                            "attempt": attempt,
                            "saved_args": [
                                str(arg) for arg in args
                            ],  # 简化，实际应用可能需要更复杂的序列化
                            "saved_kwargs": {
                                k: str(v) for k, v in kwargs.items() if k != "password"
                            },
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                        save_state(state_path, current_state)

                    # 执行原始函数 (Execute original function)
                    result = func(*args, **kwargs)

                    # 成功执行后清除状态文件 (Clear state file after successful execution)
                    if state_path and state_path.exists():
                        # 标记为已完成 (Mark as completed)
                        completed_state = {
                            "function": func.__name__,
                            "status": "completed",
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                        save_state(state_path, completed_state)

                    return result

                except Exception as e:
                    attempt += 1
                    last_exception = e

                    # 检查是否是需要重试的异常 (Check if exception is in retry list)
                    should_retry = any(
                        isinstance(e, exc_type) for exc_type in retry_on_exceptions
                    )

                    if should_retry and attempt <= max_retries:
                        logger.warning(f"Attempt {attempt}/{max_retries} failed: {e}")
                    else:
                        # 达到最大重试次数或不需要重试的异常 (Max retries reached or exception not in retry list)
                        if state_path:
                            # 保存失败状态 (Save failure state)
                            failure_state = {
                                "function": func.__name__,
                                "status": "failed",
                                "error": str(e),
                                "attempt": attempt,
                                "timestamp": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                            }
                            save_state(state_path, failure_state)

                        # 重新抛出最后一个异常 (Re-raise the last exception)
                        logger.error(f"All {attempt} attempts failed, last error: {e}")
                        raise

            # 不应该到达这里，但为了完整性 (Should not reach here, but for completeness)
            if last_exception:
                raise last_exception

            # 类型检查器需要这一行 (Type checker needs this line)
            return None  # type: ignore

        return wrapper

    return decorator


class NetworkClient:
    """网络客户端基类，提供重试和状态恢复功能。
    Base network client class providing retry and state recovery functionality.
    """

    def __init__(self, state_dir: Optional[str] = None):
        """
        初始化网络客户端。
        Initialize network client.

        参数 (Parameters):
            state_dir: 状态文件目录，默认为None (使用默认交易目录)
                      (State file directory, default None (uses default trades directory))
        """
        self.state_dir = state_dir or str(utils.get_trades_dir() / "states")

        # 确保状态目录存在 (Ensure state directory exists)
        Path(self.state_dir).mkdir(parents=True, exist_ok=True)

    def get_state_path(self, operation: str) -> Path:
        """
        获取特定操作的状态文件路径。
        Get state file path for specific operation.

        参数 (Parameters):
            operation: 操作名称 (Operation name)

        返回 (Returns):
            Path: 状态文件路径 (State file path)
        """
        return Path(self.state_dir) / f"{operation}_state.json"

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
        state_path = self.get_state_path(operation)
        return save_state(state_path, state_data)

    def load_operation_state(self, operation: str) -> Dict[str, Any]:
        """
        加载操作状态。
        Load operation state.

        参数 (Parameters):
            operation: 操作名称 (Operation name)

        返回 (Returns):
            Dict[str, Any]: 状态数据 (State data)
        """
        state_path = self.get_state_path(operation)
        return load_state(state_path)

    def clear_operation_state(self, operation: str) -> bool:
        """
        清除操作状态。
        Clear operation state.

        参数 (Parameters):
            operation: 操作名称 (Operation name)

        返回 (Returns):
            bool: 清除是否成功 (Whether clear was successful)
        """
        try:
            state_path = self.get_state_path(operation)
            if state_path.exists():
                state_path.unlink()
                logger.debug(f"State cleared: {state_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to clear state: {e}")
            return False

    @with_retry(state_file="example_request")
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
        # 这里应该是实际的网络请求代码
        # Actual network request code would go here

        # 模拟请求 (Simulate request)
        logger.info(f"Making request to {url} with params: {params}")

        # 模拟网络延迟 (Simulate network delay)
        time.sleep(0.5)

        # 模拟随机失败 (Simulate random failure)
        if random.random() < 0.3:  # 30% 失败率 (30% failure rate)
            raise ConnectionError("Simulated network error")

        # 模拟成功响应 (Simulate successful response)
        return {"status": "success", "data": {"result": "some data"}}
