#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 src.core.network.retry_manager 模块的所有功能
Retry Manager Module Tests

覆盖目标:
- calculate_retry_delay 函数
- create_retry_decorator 函数
- SimpleRetryExecutor 类
- retry 装饰器
- RetryManager 类
- 边界情况和错误处理
"""

import logging
from unittest.mock import Mock, patch

import pytest

from src.core.network.retry_manager import (
    DEFAULT_RETRY_CONFIG,
    RetryManager,
    SimpleRetryExecutor,
    calculate_retry_delay,
    create_retry_decorator,
    retry,
)


class TestCalculateRetryDelay:
    """测试 calculate_retry_delay 函数"""

    def test_calculate_retry_delay_basic(self):
        """测试基础延迟计算"""
        config = DEFAULT_RETRY_CONFIG.copy()

        # 第一次重试
        delay1 = calculate_retry_delay(1, config)
        assert 0.9 <= delay1 <= 1.1  # 基础延迟1.0 ± 10%抖动

        # 第二次重试
        delay2 = calculate_retry_delay(2, config)
        assert 1.8 <= delay2 <= 2.2  # 2.0 ± 10%抖动

        # 第三次重试
        delay3 = calculate_retry_delay(3, config)
        assert 3.6 <= delay3 <= 4.4  # 4.0 ± 10%抖动

    def test_calculate_retry_delay_max_delay_limit(self):
        """测试最大延迟限制"""
        config = {
            "base_delay": 10.0,
            "max_delay": 15.0,
            "backoff_factor": 2.0,
            "jitter": 0.1,
        }

        # 高次重试应该被限制在max_delay
        delay = calculate_retry_delay(10, config)
        assert delay <= 16.5  # max_delay + 10%抖动

    def test_calculate_retry_delay_custom_config(self):
        """测试自定义配置"""
        config = {
            "base_delay": 0.5,
            "max_delay": 30.0,
            "backoff_factor": 3.0,
            "jitter": 0.2,
        }

        delay1 = calculate_retry_delay(1, config)
        assert 0.4 <= delay1 <= 0.6  # 0.5 ± 20%抖动

        delay2 = calculate_retry_delay(2, config)
        assert 1.2 <= delay2 <= 1.8  # 1.5 ± 20%抖动

    def test_calculate_retry_delay_zero_jitter(self):
        """测试零抖动"""
        config = {
            "base_delay": 2.0,
            "max_delay": 60.0,
            "backoff_factor": 2.0,
            "jitter": 0.0,
        }

        delay1 = calculate_retry_delay(1, config)
        assert delay1 == 2.0

        delay2 = calculate_retry_delay(2, config)
        assert delay2 == 4.0

    def test_calculate_retry_delay_missing_config_keys(self):
        """测试配置键缺失时使用默认值"""
        config = {"base_delay": 3.0}  # 只提供部分配置

        delay = calculate_retry_delay(1, config)
        # 应该使用base_delay=3.0，其他使用默认值
        assert 2.7 <= delay <= 3.3  # 3.0 ± 10%抖动

    def test_calculate_retry_delay_negative_prevention(self):
        """测试防止负延迟"""
        config = {
            "base_delay": 0.1,
            "max_delay": 60.0,
            "backoff_factor": 2.0,
            "jitter": 1.0,  # 100%抖动，可能产生负值
        }

        delay = calculate_retry_delay(1, config)
        assert delay >= 0  # 确保延迟非负

    @patch("src.core.network.retry_manager.random.uniform")
    def test_calculate_retry_delay_jitter_calculation(self, mock_uniform):
        """测试抖动计算逻辑"""
        mock_uniform.return_value = 1.05  # 固定抖动值

        config = {
            "base_delay": 1.0,
            "max_delay": 60.0,
            "backoff_factor": 2.0,
            "jitter": 0.1,
        }

        delay = calculate_retry_delay(1, config)

        # 验证uniform被正确调用
        mock_uniform.assert_called_once_with(0.9, 1.1)  # 1.0 ± 10%
        assert delay == 1.05


class TestCreateRetryDecorator:
    """测试 create_retry_decorator 函数"""

    def test_create_retry_decorator_basic(self):
        """测试基础装饰器创建"""
        decorator = create_retry_decorator()

        # 验证返回的是装饰器函数
        assert callable(decorator)

        # 测试装饰器应用
        @decorator
        def test_func():
            return "success"

        result = test_func()
        assert result == "success"

    def test_create_retry_decorator_with_config(self):
        """测试带配置的装饰器创建"""
        config = {
            "max_retries": 3,
            "base_delay": 0.1,
            "max_delay": 10.0,
            "backoff_factor": 1.5,
            "jitter": 0.05,
        }

        decorator = create_retry_decorator(retry_config=config)

        @decorator
        def test_func():
            return "configured"

        result = test_func()
        assert result == "configured"

    def test_create_retry_decorator_with_custom_exceptions(self):
        """测试自定义异常列表"""
        custom_exceptions = [ValueError, TypeError]

        decorator = create_retry_decorator(retry_on_exceptions=custom_exceptions)

        @decorator
        def test_func():
            return "custom_exceptions"

        result = test_func()
        assert result == "custom_exceptions"

    def test_create_retry_decorator_with_logger_name(self):
        """测试自定义日志记录器名称"""
        decorator = create_retry_decorator(logger_name="test_logger")

        @decorator
        def test_func():
            return "custom_logger"

        result = test_func()
        assert result == "custom_logger"

    def test_create_retry_decorator_preserves_function_metadata(self):
        """测试装饰器保留函数元数据"""
        decorator = create_retry_decorator()

        @decorator
        def test_func_with_metadata():
            """Test function docstring"""
            return "metadata"

        assert test_func_with_metadata.__name__ == "test_func_with_metadata"
        assert test_func_with_metadata.__doc__ == "Test function docstring"


class TestSimpleRetryExecutor:
    """测试 SimpleRetryExecutor 类"""

    def setup_method(self):
        """测试设置"""
        self.mock_func = Mock(return_value="success")
        self.mock_logger = Mock(spec=logging.Logger)
        self.config = DEFAULT_RETRY_CONFIG.copy()
        self.exceptions = [ConnectionError, TimeoutError]

        self.executor = SimpleRetryExecutor(
            func=self.mock_func,
            retry_config=self.config,
            retry_on_exceptions=self.exceptions,
            logger=self.mock_logger,
        )

    def test_simple_retry_executor_init(self):
        """测试SimpleRetryExecutor初始化"""
        assert self.executor.func is self.mock_func
        assert self.executor.retry_config == self.config
        assert self.executor.retry_on_exceptions == self.exceptions
        assert self.executor.logger is self.mock_logger
        assert self.executor.max_retries == 5

    def test_execute_success_first_attempt(self):
        """测试第一次尝试成功"""
        result = self.executor.execute("arg1", kwarg1="value1")

        assert result == "success"
        self.mock_func.assert_called_once_with("arg1", kwarg1="value1")

        # 不应该有重试日志
        self.mock_logger.info.assert_not_called()
        self.mock_logger.warning.assert_not_called()

    @patch("src.core.network.retry_manager.time.sleep")
    def test_execute_success_after_retries(self, mock_sleep):
        """测试重试后成功"""
        # 前两次失败，第三次成功
        self.mock_func.side_effect = [
            ConnectionError("Connection failed"),
            TimeoutError("Timeout"),
            "success",
        ]

        result = self.executor.execute("arg1")

        assert result == "success"
        assert self.mock_func.call_count == 3

        # 验证重试日志
        assert self.mock_logger.warning.call_count == 2
        assert self.mock_logger.info.call_count == 2  # 重试延迟日志

    @patch("src.core.network.retry_manager.time.sleep")
    def test_execute_max_retries_exceeded(self, mock_sleep):
        """测试超过最大重试次数"""
        # 所有尝试都失败
        self.mock_func.side_effect = ConnectionError("Always fails")

        with pytest.raises(ConnectionError, match="Always fails"):
            self.executor.execute()

        # 验证尝试次数：初始 + max_retries
        assert self.mock_func.call_count == 6  # 1 + 5 retries

        # 验证错误日志
        self.mock_logger.error.assert_called_once()

    def test_execute_non_retryable_exception(self):
        """测试不可重试的异常"""
        self.mock_func.side_effect = ValueError("Not retryable")

        with pytest.raises(ValueError, match="Not retryable"):
            self.executor.execute()

        # 只应该尝试一次
        assert self.mock_func.call_count == 1

        # 应该有最终失败日志
        self.mock_logger.error.assert_called_once()

    @patch("src.core.network.retry_manager.calculate_retry_delay")
    @patch("src.core.network.retry_manager.time.sleep")
    def test_apply_retry_delay(self, mock_sleep, mock_calculate_delay):
        """测试重试延迟应用"""
        mock_calculate_delay.return_value = 2.5
        self.mock_func.side_effect = [ConnectionError("Fail"), "success"]

        result = self.executor.execute()

        assert result == "success"
        mock_calculate_delay.assert_called_once_with(1, self.config)
        mock_sleep.assert_called_once_with(2.5)

    def test_should_continue_retry_logic(self):
        """测试重试判断逻辑"""
        # 可重试异常
        assert self.executor._should_continue_retry(ConnectionError(), 1) is True
        assert self.executor._should_continue_retry(TimeoutError(), 3) is True

        # 不可重试异常
        assert self.executor._should_continue_retry(ValueError(), 1) is False

        # 超过最大重试次数
        assert self.executor._should_continue_retry(ConnectionError(), 6) is False

    def test_log_retry_attempt(self):
        """测试重试尝试日志"""
        exception = ConnectionError("Test error")
        self.executor._log_retry_attempt(exception, 2)

        self.mock_logger.warning.assert_called_once_with("Attempt 2/5 failed: Test error")

    def test_handle_final_failure(self):
        """测试最终失败处理"""
        exception = TimeoutError("Final error")
        self.executor._handle_final_failure(exception, 6)

        self.mock_logger.error.assert_called_once_with(
            "All 6 attempts failed, last error: Final error"
        )


class TestRetryDecorator:
    """测试 retry 装饰器"""

    def test_retry_decorator_basic(self):
        """测试基础retry装饰器"""

        @retry(max_retries=2, base_delay=0.01)
        def test_func():
            return "decorated"

        result = test_func()
        assert result == "decorated"

    @patch("src.core.network.retry_manager.time.sleep")
    def test_retry_decorator_with_failures(self, mock_sleep):
        """测试带失败的retry装饰器"""
        call_count = 0

        @retry(max_retries=2, base_delay=0.01)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success_after_retries"

        result = test_func()
        assert result == "success_after_retries"
        assert call_count == 3

    def test_retry_decorator_custom_exceptions(self):
        """测试自定义异常的retry装饰器"""

        @retry(max_retries=1, retry_on=[ValueError])
        def test_func():
            raise TypeError("Not retryable")

        with pytest.raises(TypeError):
            test_func()

    def test_retry_decorator_parameters(self):
        """测试retry装饰器参数传递"""

        @retry(
            max_retries=3,
            base_delay=0.5,
            max_delay=10.0,
            backoff_factor=1.5,
            jitter=0.2,
        )
        def test_func():
            return "parameters"

        result = test_func()
        assert result == "parameters"


class TestRetryManager:
    """测试 RetryManager 类"""

    def setup_method(self):
        """测试设置"""
        self.manager = RetryManager()

    def test_retry_manager_init_default(self):
        """测试RetryManager默认初始化"""
        assert self.manager.default_config == DEFAULT_RETRY_CONFIG
        assert ConnectionError in self.manager.default_exceptions
        assert TimeoutError in self.manager.default_exceptions
        assert OSError in self.manager.default_exceptions

    def test_retry_manager_init_custom(self):
        """测试RetryManager自定义初始化"""
        custom_config = {"max_retries": 3, "base_delay": 0.5}
        custom_exceptions = [ValueError, TypeError]

        manager = RetryManager(
            default_config=custom_config,
            default_exceptions=custom_exceptions,
        )

        assert manager.default_config == custom_config
        assert manager.default_exceptions == custom_exceptions

    def test_execute_with_retry_success(self):
        """测试execute_with_retry成功执行"""

        def test_func(x, y=None):
            return f"result: {x}, {y}"

        result = self.manager.execute_with_retry(test_func, "arg1", y="kwarg1")
        assert result == "result: arg1, kwarg1"

    @patch("src.core.network.retry_manager.time.sleep")
    def test_execute_with_retry_with_failures(self, mock_sleep):
        """测试execute_with_retry带失败"""
        call_count = 0

        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"

        result = self.manager.execute_with_retry(test_func)
        assert result == "success"
        assert call_count == 3

    def test_execute_with_retry_custom_config(self):
        """测试execute_with_retry自定义配置"""
        custom_config = {"max_retries": 1, "base_delay": 0.01}

        def test_func():
            return "custom_config"

        result = self.manager.execute_with_retry(
            test_func,
            retry_config=custom_config,
        )
        assert result == "custom_config"

    def test_execute_with_retry_custom_exceptions(self):
        """测试execute_with_retry自定义异常"""

        def test_func():
            raise ValueError("Custom exception")

        with pytest.raises(ValueError):
            self.manager.execute_with_retry(
                test_func,
                retry_on_exceptions=[TypeError],  # ValueError不在列表中
            )

    def test_create_decorator(self):
        """测试create_decorator方法"""
        decorator = self.manager.create_decorator()

        assert callable(decorator)

        @decorator
        def test_func():
            return "decorator_created"

        result = test_func()
        assert result == "decorator_created"

    def test_create_decorator_with_custom_params(self):
        """测试create_decorator自定义参数"""
        custom_config = {"max_retries": 2}
        custom_exceptions = [ValueError]

        decorator = self.manager.create_decorator(
            retry_config=custom_config,
            retry_on_exceptions=custom_exceptions,
        )

        @decorator
        def test_func():
            return "custom_decorator"

        result = test_func()
        assert result == "custom_decorator"


class TestRetryManagerIntegration:
    """测试重试管理器集成功能"""

    @patch("src.core.network.retry_manager.time.sleep")
    def test_full_retry_workflow(self, mock_sleep):
        """测试完整的重试工作流"""
        manager = RetryManager()
        call_count = 0

        def flaky_function(data):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                raise ConnectionError("Network error")
            elif call_count == 2:
                raise TimeoutError("Timeout error")
            else:
                return f"processed: {data}"

        result = manager.execute_with_retry(flaky_function, "test_data")

        assert result == "processed: test_data"
        assert call_count == 3
        assert mock_sleep.call_count == 2  # 两次重试延迟

    def test_retry_with_different_exception_types(self):
        """测试不同异常类型的重试行为"""
        manager = RetryManager()

        # 可重试异常
        def retryable_func():
            raise ConnectionError("Retryable")

        with pytest.raises(ConnectionError):
            manager.execute_with_retry(
                retryable_func,
                retry_config={"max_retries": 1},
            )

        # 不可重试异常
        def non_retryable_func():
            raise ValueError("Not retryable")

        with pytest.raises(ValueError):
            manager.execute_with_retry(non_retryable_func)

    @patch("src.core.network.retry_manager.logging.getLogger")
    def test_logging_integration(self, mock_get_logger):
        """测试日志集成"""
        mock_logger = Mock(spec=logging.Logger)
        mock_get_logger.return_value = mock_logger

        decorator = create_retry_decorator(logger_name="test_logger")

        @decorator
        def test_func():
            return "logged"

        result = test_func()
        assert result == "logged"

        mock_get_logger.assert_called_with("test_logger")


class TestEdgeCases:
    """测试边界情况"""

    def test_zero_max_retries(self):
        """测试零重试次数"""
        config = {"max_retries": 0}
        manager = RetryManager(default_config=config)

        def failing_func():
            raise ConnectionError("Always fails")

        with pytest.raises(ConnectionError):
            manager.execute_with_retry(failing_func)

    def test_negative_max_retries(self):
        """测试负重试次数"""
        config = {"max_retries": -1}
        manager = RetryManager(default_config=config)

        def failing_func():
            raise ConnectionError("Always fails")

        # 当max_retries为负数时，while循环不会执行，直接返回None
        result = manager.execute_with_retry(failing_func)
        assert result is None

    def test_empty_retry_exceptions_list(self):
        """测试空重试异常列表"""
        manager = RetryManager(default_exceptions=[])

        def failing_func():
            raise ConnectionError("Should not retry")

        with pytest.raises(ConnectionError):
            manager.execute_with_retry(failing_func)

    def test_function_with_no_return_value(self):
        """测试无返回值的函数"""
        manager = RetryManager()

        def void_func():
            pass  # 无返回值

        result = manager.execute_with_retry(void_func)
        assert result is None

    @patch("src.core.network.retry_manager.time.sleep")
    def test_very_large_delay_values(self, mock_sleep):
        """测试非常大的延迟值"""
        config = {
            "max_retries": 1,
            "base_delay": 1000.0,
            "max_delay": 2000.0,
            "backoff_factor": 10.0,
            "jitter": 0.0,
        }

        manager = RetryManager(default_config=config)
        call_count = 0

        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Fail once")
            return "success"

        result = manager.execute_with_retry(test_func)
        assert result == "success"

        # 验证大延迟值被正确处理
        mock_sleep.assert_called_once()
        delay_used = mock_sleep.call_args[0][0]
        assert delay_used >= 1000.0


class TestDefaultRetryConfig:
    """测试默认重试配置"""

    def test_default_config_values(self):
        """测试默认配置值"""
        assert DEFAULT_RETRY_CONFIG["max_retries"] == 5
        assert DEFAULT_RETRY_CONFIG["base_delay"] == 1.0
        assert DEFAULT_RETRY_CONFIG["max_delay"] == 60.0
        assert DEFAULT_RETRY_CONFIG["backoff_factor"] == 2.0
        assert DEFAULT_RETRY_CONFIG["jitter"] == 0.1

    def test_default_config_immutability(self):
        """测试默认配置不被意外修改"""
        original_config = DEFAULT_RETRY_CONFIG.copy()

        # 使用配置
        manager = RetryManager()
        manager.execute_with_retry(lambda: "test")

        # 验证原始配置未被修改
        assert DEFAULT_RETRY_CONFIG == original_config
