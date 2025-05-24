"""
重试管理模块 (Retry Manager Module)

提供网络请求重试机制，包括：
- 指数退避算法
- 抖动计算
- 重试装饰器
- 异常处理
"""

import logging
import random
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar

# 设置日志记录器
logger = logging.getLogger(__name__)

# 定义类型变量
T = TypeVar("T")

# 默认重试参数
DEFAULT_RETRY_CONFIG = {
    "max_retries": 5,  # 最大重试次数
    "base_delay": 1.0,  # 基础延迟秒数
    "max_delay": 60.0,  # 最大延迟秒数
    "backoff_factor": 2.0,  # 退避因子
    "jitter": 0.1,  # 抖动系数
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
    backoff_factor = config.get("backoff_factor", DEFAULT_RETRY_CONFIG["backoff_factor"])
    jitter = config.get("jitter", DEFAULT_RETRY_CONFIG["jitter"])

    # 计算指数退避
    delay = min(max_delay, base_delay * (backoff_factor ** (attempt - 1)))

    # 添加随机抖动
    jitter_amount = delay * jitter
    delay = random.uniform(delay - jitter_amount, delay + jitter_amount)

    return max(0, delay)  # 确保延迟非负


def create_retry_decorator(
    retry_config: Optional[Dict[str, float]] = None,
    retry_on_exceptions: Optional[List[type]] = None,
    logger_name: Optional[str] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    创建重试装饰器（简化版本，不包含状态管理）。
    Create retry decorator (simplified version without state management).

    参数 (Parameters):
        retry_config: 重试配置参数
        retry_on_exceptions: 需要重试的异常类型列表
        logger_name: 日志记录器名称

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

    # 获取日志记录器
    retry_logger = logging.getLogger(logger_name or __name__)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            simple_executor = SimpleRetryExecutor(
                func=func,
                retry_config=retry_config,
                retry_on_exceptions=retry_on_exceptions,
                logger=retry_logger,
            )
            return simple_executor.execute(*args, **kwargs)

        return wrapper

    return decorator


class SimpleRetryExecutor:
    """简化的重试执行器，不包含状态管理"""

    def __init__(
        self,
        func: Callable[..., T],
        retry_config: Dict[str, float],
        retry_on_exceptions: List[type],
        logger: logging.Logger,
    ):
        self.func = func
        self.retry_config = retry_config
        self.retry_on_exceptions = retry_on_exceptions
        self.logger = logger
        self.max_retries = retry_config.get("max_retries", DEFAULT_RETRY_CONFIG["max_retries"])

    def execute(self, *args: Any, **kwargs: Any) -> T:
        """执行函数并应用重试逻辑"""
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

    def _execute_attempt(self, attempt: int, args: tuple, kwargs: dict) -> T:
        """执行单次尝试"""
        if attempt > 0:
            self._apply_retry_delay(attempt)

        return self.func(*args, **kwargs)

    def _apply_retry_delay(self, attempt: int):
        """应用重试延迟"""
        delay = calculate_retry_delay(attempt, self.retry_config)
        self.logger.info(f"Retry {attempt}/{self.max_retries} after {delay:.2f}s delay")
        time.sleep(delay)

    def _should_continue_retry(self, exception: Exception, attempt: int) -> bool:
        """判断是否应该继续重试"""
        should_retry = any(isinstance(exception, exc_type) for exc_type in self.retry_on_exceptions)
        return should_retry and attempt <= self.max_retries

    def _log_retry_attempt(self, exception: Exception, attempt: int):
        """记录重试尝试"""
        self.logger.warning(f"Attempt {attempt}/{self.max_retries} failed: {exception}")

    def _handle_final_failure(self, exception: Exception, attempt: int):
        """处理最终失败的情况"""
        self.logger.error(f"All {attempt} attempts failed, last error: {exception}")


# 便捷的重试装饰器
def retry(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: float = 0.1,
    retry_on: Optional[List[type]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    便捷的重试装饰器。
    Convenient retry decorator.

    参数 (Parameters):
        max_retries: 最大重试次数
        base_delay: 基础延迟秒数
        max_delay: 最大延迟秒数
        backoff_factor: 退避因子
        jitter: 抖动系数
        retry_on: 需要重试的异常类型列表

    返回 (Returns):
        Callable: 装饰器函数
    """
    config = {
        "max_retries": max_retries,
        "base_delay": base_delay,
        "max_delay": max_delay,
        "backoff_factor": backoff_factor,
        "jitter": jitter,
    }

    return create_retry_decorator(
        retry_config=config,
        retry_on_exceptions=retry_on,
    )


class RetryManager:
    """重试管理器类"""

    def __init__(
        self,
        default_config: Optional[Dict[str, float]] = None,
        default_exceptions: Optional[List[type]] = None,
    ):
        """
        初始化重试管理器

        参数:
            default_config: 默认重试配置
            default_exceptions: 默认重试异常列表
        """
        self.default_config = default_config or DEFAULT_RETRY_CONFIG.copy()
        self.default_exceptions = default_exceptions or [
            ConnectionError,
            TimeoutError,
            OSError,
        ]

    def execute_with_retry(
        self,
        func: Callable[..., T],
        *args,
        retry_config: Optional[Dict[str, float]] = None,
        retry_on_exceptions: Optional[List[type]] = None,
        **kwargs,
    ) -> T:
        """
        执行函数并应用重试逻辑

        参数:
            func: 要执行的函数
            *args: 函数参数
            retry_config: 重试配置
            retry_on_exceptions: 重试异常列表
            **kwargs: 函数关键字参数

        返回:
            T: 函数执行结果
        """
        config = retry_config or self.default_config
        exceptions = retry_on_exceptions or self.default_exceptions

        decorator = create_retry_decorator(
            retry_config=config,
            retry_on_exceptions=exceptions,
        )

        decorated_func = decorator(func)
        return decorated_func(*args, **kwargs)

    def create_decorator(
        self,
        retry_config: Optional[Dict[str, float]] = None,
        retry_on_exceptions: Optional[List[type]] = None,
    ) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """
        创建重试装饰器

        参数:
            retry_config: 重试配置
            retry_on_exceptions: 重试异常列表

        返回:
            Callable: 装饰器函数
        """
        config = retry_config or self.default_config
        exceptions = retry_on_exceptions or self.default_exceptions

        return create_retry_decorator(
            retry_config=config,
            retry_on_exceptions=exceptions,
        )
