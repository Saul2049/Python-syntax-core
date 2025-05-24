"""
网络装饰器模块 (Network Decorators Module)

提供高级网络装饰器，包括：
- 带状态管理的重试装饰器
- 自动状态恢复装饰器
- 组合装饰器
"""

import logging
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar

from .retry_manager import (
    DEFAULT_RETRY_CONFIG,
    calculate_retry_delay,
)
from .state_manager import (
    get_global_state_manager,
    load_state,
    save_state,
)

# 设置日志记录器
logger = logging.getLogger(__name__)

# 定义类型变量
T = TypeVar("T")


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
        retry_on_exceptions: 需要重试的异常类型列表
        state_file: 状态文件名，用于保存进度，默认为None

    返回 (Returns):
        Callable: 装饰器函数
    """
    # 使用默认配置
    if retry_config is None:
        retry_config = DEFAULT_RETRY_CONFIG.copy()

    # 使用默认异常列表
    if retry_on_exceptions is None:
        retry_on_exceptions = [
            ConnectionError,  # 连接错误
            TimeoutError,  # 超时错误
            OSError,  # 操作系统错误
        ]

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            retry_executor = RetryExecutor(
                func=func,
                retry_config=retry_config,
                retry_on_exceptions=retry_on_exceptions,
                state_file=state_file,
            )
            return retry_executor.execute_with_retry(*args, **kwargs)

        return wrapper

    return decorator


class RetryExecutor:
    """处理重试逻辑的执行器类"""

    def __init__(
        self,
        func: Callable[..., T],
        retry_config: Dict[str, float],
        retry_on_exceptions: List[type],
        state_file: Optional[str],
    ):
        self.func = func
        self.retry_config = retry_config
        self.retry_on_exceptions = retry_on_exceptions
        self.state_file = state_file
        self.state_path = None
        self.max_retries = retry_config.get("max_retries", DEFAULT_RETRY_CONFIG["max_retries"])

    def execute_with_retry(self, *args: Any, **kwargs: Any) -> T:
        """执行带重试的函数调用"""
        self._setup_state_management()
        self._load_initial_state(args, kwargs)

        attempt = 0
        last_exception = None

        while attempt <= self.max_retries:
            try:
                return self._execute_attempt(attempt, args, kwargs)
            except Exception as e:
                attempt += 1
                last_exception = e

                if not self._should_continue_retry(e, attempt):
                    self._handle_final_failure(e, attempt)
                    raise

                self._log_retry_attempt(e, attempt)

        # 不应该到达这里，但为了完整性
        if last_exception:
            raise last_exception
        return None  # type: ignore

    def _setup_state_management(self):
        """设置状态管理"""
        if self.state_file:
            state_manager = get_global_state_manager()
            self.state_path = state_manager.get_state_path(self.state_file)

    def _load_initial_state(self, args: tuple, kwargs: dict):
        """加载初始状态并可选择性恢复参数"""
        if not self.state_path:
            return

        state_data = load_state(self.state_path)

        if "saved_args" in state_data and "saved_kwargs" in state_data:
            logger.info(f"Resuming from saved state in {self.state_path}")
            self._restore_params_if_requested(state_data, kwargs)

    def _restore_params_if_requested(self, state_data: dict, kwargs: dict):
        """根据请求恢复保存的参数"""
        if kwargs.get("resume_params", False):
            saved_kwargs = state_data["saved_kwargs"]
            for key, value in saved_kwargs.items():
                if key not in kwargs:
                    kwargs[key] = value

    def _execute_attempt(self, attempt: int, args: tuple, kwargs: dict) -> T:
        """执行单次尝试"""
        if attempt > 0:
            self._apply_retry_delay(attempt)

        self._save_attempt_state(attempt, args, kwargs)
        result = self.func(*args, **kwargs)
        self._handle_success()

        return result

    def _apply_retry_delay(self, attempt: int):
        """应用重试延迟"""
        delay = calculate_retry_delay(attempt, self.retry_config)
        logger.info(f"Retry {attempt}/{self.max_retries} after {delay:.2f}s delay")
        import time

        time.sleep(delay)

    def _save_attempt_state(self, attempt: int, args: tuple, kwargs: dict):
        """保存当前尝试的状态"""
        if not self.state_path:
            return

        current_state = {
            "function": self.func.__name__,
            "attempt": attempt,
            "saved_args": [str(arg) for arg in args],
            "saved_kwargs": {k: str(v) for k, v in kwargs.items() if k != "password"},
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        save_state(self.state_path, current_state)

    def _handle_success(self):
        """处理成功执行后的状态清理"""
        if self.state_path and self.state_path.exists():
            completed_state = {
                "function": self.func.__name__,
                "status": "completed",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            save_state(self.state_path, completed_state)

    def _should_continue_retry(self, exception: Exception, attempt: int) -> bool:
        """判断是否应该继续重试"""
        should_retry = any(isinstance(exception, exc_type) for exc_type in self.retry_on_exceptions)
        return should_retry and attempt <= self.max_retries

    def _log_retry_attempt(self, exception: Exception, attempt: int):
        """记录重试尝试"""
        logger.warning(f"Attempt {attempt}/{self.max_retries} failed: {exception}")

    def _handle_final_failure(self, exception: Exception, attempt: int):
        """处理最终失败的情况"""
        if self.state_path:
            failure_state = {
                "function": self.func.__name__,
                "status": "failed",
                "error": str(exception),
                "attempt": attempt,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            save_state(self.state_path, failure_state)

        logger.error(f"All {attempt} attempts failed, last error: {exception}")


def with_state_management(
    operation_name: Optional[str] = None,
    auto_save: bool = True,
    auto_clear_on_success: bool = True,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    状态管理装饰器，自动保存和恢复函数状态

    参数:
        operation_name: 操作名称，如果不提供则使用函数名
        auto_save: 是否自动保存状态
        auto_clear_on_success: 成功后是否自动清除状态

    返回:
        装饰器函数
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            op_name = operation_name or func.__name__
            state_manager = get_global_state_manager()

            if auto_save:
                _save_start_state(state_manager, op_name, func, args, kwargs)

            try:
                result = func(*args, **kwargs)
                if auto_save:
                    _handle_success_state(
                        state_manager, op_name, func, result, auto_clear_on_success
                    )
                return result

            except Exception as e:
                if auto_save:
                    _save_error_state(state_manager, op_name, func, e)
                raise

        return wrapper

    return decorator


def _save_start_state(state_manager, op_name: str, func: Callable, args: tuple, kwargs: dict):
    """保存函数开始执行时的状态"""
    start_state = {
        "function": func.__name__,
        "status": "started",
        "args": [str(arg) for arg in args],
        "kwargs": {k: str(v) for k, v in kwargs.items() if k != "password"},
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    state_manager.save_operation_state(op_name, start_state)


def _handle_success_state(
    state_manager, op_name: str, func: Callable, result: Any, auto_clear: bool
):
    """处理函数成功执行后的状态保存和清理"""
    success_state = {
        "function": func.__name__,
        "status": "completed",
        "result_summary": str(result)[:200],  # 保存结果摘要
        "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    state_manager.save_operation_state(op_name, success_state)

    if auto_clear:
        _schedule_state_cleanup(state_manager, op_name)


def _schedule_state_cleanup(state_manager, op_name: str):
    """安排延迟清理状态"""
    import threading
    import time

    def delayed_clear():
        time.sleep(5)  # 5秒后清除
        state_manager.clear_operation_state(op_name)

    threading.Thread(target=delayed_clear, daemon=True).start()


def _save_error_state(state_manager, op_name: str, func: Callable, error: Exception):
    """保存函数执行失败时的状态"""
    error_state = {
        "function": func.__name__,
        "status": "failed",
        "error": str(error),
        "error_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    state_manager.save_operation_state(op_name, error_state)


def with_comprehensive_retry(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: float = 0.1,
    retry_on: Optional[List[type]] = None,
    state_file: Optional[str] = None,
    operation_name: Optional[str] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    综合重试装饰器，结合重试和状态管理功能

    参数:
        max_retries: 最大重试次数
        base_delay: 基础延迟
        max_delay: 最大延迟
        backoff_factor: 退避因子
        jitter: 抖动系数
        retry_on: 重试异常列表
        state_file: 状态文件名
        operation_name: 操作名称

    返回:
        装饰器函数
    """
    retry_config = {
        "max_retries": max_retries,
        "base_delay": base_delay,
        "max_delay": max_delay,
        "backoff_factor": backoff_factor,
        "jitter": jitter,
    }

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # 先应用状态管理装饰器
        func_with_state = with_state_management(
            operation_name=operation_name or func.__name__,
            auto_save=True,
            auto_clear_on_success=True,
        )(func)

        # 再应用重试装饰器
        func_with_retry = with_retry(
            retry_config=retry_config,
            retry_on_exceptions=retry_on,
            state_file=state_file or func.__name__,
        )(func_with_state)

        return func_with_retry

    return decorator


# 便捷的预定义装饰器
def network_request(
    max_retries: int = 3,
    base_delay: float = 1.0,
    state_file: Optional[str] = None,
):
    """网络请求装饰器（便捷版本）"""
    return with_comprehensive_retry(
        max_retries=max_retries,
        base_delay=base_delay,
        retry_on=[ConnectionError, TimeoutError, OSError],
        state_file=state_file,
    )


def api_call(
    max_retries: int = 5,
    base_delay: float = 2.0,
    state_file: Optional[str] = None,
):
    """API调用装饰器（便捷版本）"""
    return with_comprehensive_retry(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=120.0,
        retry_on=[ConnectionError, TimeoutError, OSError],
        state_file=state_file,
    )


def critical_operation(
    max_retries: int = 10,
    base_delay: float = 1.0,
    state_file: Optional[str] = None,
):
    """关键操作装饰器（便捷版本）"""
    return with_comprehensive_retry(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=300.0,  # 5分钟最大延迟
        backoff_factor=1.5,  # 更温和的退避
        retry_on=[ConnectionError, TimeoutError, OSError],
        state_file=state_file,
    )
