import json
import logging
import random
import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar

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
    backoff_factor = config.get("backoff_factor", DEFAULT_RETRY_CONFIG["backoff_factor"])
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
            max_retries = retry_config.get("max_retries", DEFAULT_RETRY_CONFIG["max_retries"])
            
            # Initialize state and potentially update kwargs from saved state
            state_path, initial_kwargs = _initialize_retry_state(
                state_file, func.__name__, 
                kwargs.pop("resume_params", False), # Pass and remove resume_params from kwargs
                kwargs 
            )
            # Update kwargs with those potentially restored from state
            kwargs = initial_kwargs

            attempt = 0
            last_exception = None

            while attempt <= max_retries:
                try:
                    if attempt > 0:
                        delay = calculate_retry_delay(attempt, retry_config)
                        logger.info(f"Retry {attempt}/{max_retries} after {delay:.2f}s delay for {func.__name__}")
                        time.sleep(delay)

                    # Save current ("running") state before attempting the function call
                    _save_retry_state(state_path, func.__name__, "running", attempt, args, kwargs)

                    # Execute original function
                    result = func(*args, **kwargs)

                    # Save "completed" state
                    _save_retry_state(state_path, func.__name__, "completed", attempt, args, kwargs)
                    
                    return result

                except Exception as e:
                    attempt += 1
                    last_exception = e

                    should_retry = any(isinstance(e, exc_type) for exc_type in retry_on_exceptions)

                    if should_retry and attempt <= max_retries:
                        logger.warning(f"Attempt {attempt}/{max_retries} for {func.__name__} failed: {e}")
                        # State for "running" (next attempt) will be saved at the start of the next loop iteration
                    else:
                        logger.error(f"All {attempt-1} attempts for {func.__name__} failed, or exception {type(e).__name__} not in retry list. Last error: {e}")
                        _save_retry_state(state_path, func.__name__, "failed", attempt -1 , args, kwargs, error_message=str(e))
                        raise
            
            # This part should ideally not be reached if max_retries is sensible and exceptions are re-raised.
            if last_exception:
                # This case might occur if loop finishes due to attempt > max_retries without re-raising inside loop
                logger.error(f"Exiting retry loop for {func.__name__} after {attempt-1} attempts. Last error: {last_exception}")
                _save_retry_state(state_path, func.__name__, "failed", attempt -1, args, kwargs, error_message=str(last_exception))
                raise last_exception # Ensure exception is always raised if function fails

            return None # Should be unreachable

        return wrapper
    return decorator


def _initialize_retry_state(
    state_file_name: Optional[str], 
    func_name: str, 
    resume_params: bool, 
    original_kwargs: Dict[str, Any]
) -> tuple[Optional[Path], Dict[str, Any]]:
    """
    Initializes state file path, loads existing state, and restores parameters if requested.
    Returns the state_path and potentially modified kwargs.
    """
    state_path = None
    loaded_state_data = {}
    updated_kwargs = original_kwargs.copy()

    if state_file_name:
        state_dir = Path(utils.get_trades_dir()) / "states"
        state_path = state_dir / f"{state_file_name}.json"
        loaded_state_data = load_state(state_path)

        if loaded_state_data.get("status") == "completed":
            logger.info(f"Function {func_name} for state file {state_file_name} was already completed. Skipping.")
            # Potentially return a marker or raise a specific exception to skip execution
            # For now, this will lead to re-execution if not handled by caller or by ensuring 'result' is in state
        
        if resume_params and loaded_state_data.get("status") == "running":
            if "saved_args" in loaded_state_data and "saved_kwargs" in loaded_state_data:
                logger.info(f"Resuming {func_name} from saved state in {state_path} with saved_kwargs.")
                # Args are not typically restored this way as they are positional.
                # Focus on kwargs for named parameter restoration.
                saved_kwargs_from_state = loaded_state_data["saved_kwargs"]
                for key, value in saved_kwargs_from_state.items():
                    if key not in updated_kwargs: # Prioritize kwargs passed directly to the function call
                        updated_kwargs[key] = value
            else:
                logger.info(f"resume_params was True for {func_name}, but no saved_args/saved_kwargs found in state or state was not 'running'.")
        elif resume_params:
            logger.info(f"resume_params was True for {func_name}, but state status was not 'running' (was '{loaded_state_data.get('status')}'). Not restoring params.")


    return state_path, updated_kwargs


def _save_retry_state(
    state_path: Optional[Path],
    func_name: str,
    status: str, # "running", "completed", "failed"
    attempt: int,
    args: tuple, # Using tuple for args type hint
    kwargs: Dict[str, Any],
    error_message: Optional[str] = None,
) -> None:
    """
    Saves the current state of a function call to a state file.
    """
    if not state_path:
        return

    data_to_save: Dict[str, Any] = {
        "function": func_name,
        "status": status,
        "attempt": attempt,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    if status == "running":
        # For "running" state, save current args and kwargs
        data_to_save["saved_args"] = [str(arg) for arg in args] # Simplified serialization
        data_to_save["saved_kwargs"] = {k: str(v) for k, v in kwargs.items() if k != "password"}
    elif status == "failed":
        data_to_save["error"] = error_message
        # Optionally, could also save args/kwargs for failed state for debugging
        data_to_save["saved_args_on_fail"] = [str(arg) for arg in args]
        data_to_save["saved_kwargs_on_fail"] = {k: str(v) for k, v in kwargs.items() if k != "password"}


    # Call the original save_state utility
    save_state(state_path, data_to_save)

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
