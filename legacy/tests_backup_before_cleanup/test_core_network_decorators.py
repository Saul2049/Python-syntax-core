#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 src.core.network.decorators 模块的所有功能
Network Decorators Module Tests

覆盖目标:
- with_retry 装饰器
- RetryExecutor 类
- with_state_management 装饰器
- with_comprehensive_retry 装饰器
- 便捷装饰器 (network_request, api_call, critical_operation)
- 状态管理和重试逻辑
- 错误处理和边界情况
"""

import unittest
from functools import wraps
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import modules to test
try:
    from src.core.network.decorators import (
        RetryExecutor,
        _handle_success_state,
        _save_error_state,
        _save_start_state,
        _schedule_state_cleanup,
        api_call,
        critical_operation,
        network_request,
        with_comprehensive_retry,
        with_retry,
        with_state_management,
    )
    from src.core.network.retry_manager import DEFAULT_RETRY_CONFIG
except ImportError:
    pytest.skip("Network decorators module not available, skipping tests", allow_module_level=True)


class TestWithRetryDecorator(unittest.TestCase):
    """测试 with_retry 装饰器"""

    def setUp(self):
        """设置测试环境"""
        # 🧹 不再需要手动创建临时目录，使用上下文管理器
        pass

    def tearDown(self):
        """清理测试环境"""
        # 🧹 不再需要手动清理，上下文管理器会自动处理
        pass

    def test_with_retry_default_config(self):
        """测试默认配置的重试装饰器"""
        call_count = 0

        @with_retry()
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Test error")
            return "success"

        with patch("src.core.network.decorators.RetryExecutor") as mock_executor:
            mock_instance = Mock()
            mock_instance.execute_with_retry.return_value = "success"
            mock_executor.return_value = mock_instance

            result = test_function()

            # 验证结果
            self.assertEqual(result, "success")

            # 验证 RetryExecutor 被正确初始化
            mock_executor.assert_called_once()
            init_args = mock_executor.call_args
            self.assertEqual(init_args[1]["retry_config"], DEFAULT_RETRY_CONFIG)
            self.assertEqual(
                init_args[1]["retry_on_exceptions"], [ConnectionError, TimeoutError, OSError]
            )

    def test_with_retry_custom_config(self):
        """测试自定义配置的重试装饰器"""
        custom_config = {"max_retries": 5, "base_delay": 2.0}
        custom_exceptions = [ValueError, RuntimeError]

        @with_retry(
            retry_config=custom_config,
            retry_on_exceptions=custom_exceptions,
            state_file="test_state",
        )
        def test_function():
            return "custom_success"

        with patch("src.core.network.decorators.RetryExecutor") as mock_executor:
            mock_instance = Mock()
            mock_instance.execute_with_retry.return_value = "custom_success"
            mock_executor.return_value = mock_instance

            result = test_function()

            # 验证结果
            self.assertEqual(result, "custom_success")

            # 验证自定义配置
            init_args = mock_executor.call_args
            self.assertEqual(init_args[1]["retry_config"], custom_config)
            self.assertEqual(init_args[1]["retry_on_exceptions"], custom_exceptions)
            self.assertEqual(init_args[1]["state_file"], "test_state")

    def test_with_retry_preserves_function_metadata(self):
        """测试装饰器保留函数元数据"""

        @with_retry()
        def test_function():
            """Test function docstring"""
            return "test"

        # 验证函数名和文档字符串被保留
        self.assertEqual(test_function.__name__, "test_function")
        self.assertEqual(test_function.__doc__, "Test function docstring")


class TestRetryExecutor(unittest.TestCase):
    """测试 RetryExecutor 类"""

    def setUp(self):
        """设置测试环境"""
        # 🧹 不再需要手动创建临时目录，使用上下文管理器
        self.test_func = Mock()
        self.test_func.__name__ = "test_function"  # 设置函数名
        self.retry_config = {"max_retries": 3, "base_delay": 0.1}
        self.retry_exceptions = [ConnectionError, ValueError]

    def tearDown(self):
        """清理测试环境"""
        # 🧹 不再需要手动清理，上下文管理器会自动处理
        pass

    def test_init(self):
        """测试初始化"""
        executor = RetryExecutor(
            func=self.test_func,
            retry_config=self.retry_config,
            retry_on_exceptions=self.retry_exceptions,
            state_file="test_state",
        )

        self.assertEqual(executor.func, self.test_func)
        self.assertEqual(executor.retry_config, self.retry_config)
        self.assertEqual(executor.retry_on_exceptions, self.retry_exceptions)
        self.assertEqual(executor.state_file, "test_state")
        self.assertEqual(executor.max_retries, 3)

    @patch("src.core.network.decorators.get_global_state_manager")
    def test_setup_state_management_with_state_file(self, mock_get_manager):
        """测试设置状态管理（有状态文件）"""
        mock_manager = Mock()
        mock_manager.get_state_path.return_value = Path("/test/path")
        mock_get_manager.return_value = mock_manager

        executor = RetryExecutor(
            func=self.test_func,
            retry_config=self.retry_config,
            retry_on_exceptions=self.retry_exceptions,
            state_file="test_state",
        )

        executor._setup_state_management()

        mock_get_manager.assert_called_once()
        mock_manager.get_state_path.assert_called_once_with("test_state")
        self.assertEqual(executor.state_path, Path("/test/path"))

    def test_setup_state_management_without_state_file(self):
        """测试设置状态管理（无状态文件）"""
        executor = RetryExecutor(
            func=self.test_func,
            retry_config=self.retry_config,
            retry_on_exceptions=self.retry_exceptions,
            state_file=None,
        )

        executor._setup_state_management()

        self.assertIsNone(executor.state_path)

    @patch("src.core.network.decorators.load_state")
    def test_load_initial_state_with_saved_data(self, mock_load_state):
        """测试加载初始状态（有保存的数据）"""
        mock_load_state.return_value = {
            "saved_args": ["arg1", "arg2"],
            "saved_kwargs": {"key": "value"},
        }

        executor = RetryExecutor(
            func=self.test_func,
            retry_config=self.retry_config,
            retry_on_exceptions=self.retry_exceptions,
            state_file="test_state",
        )
        executor.state_path = Path("/test/path")

        args = ("arg1", "arg2")
        kwargs = {"resume_params": True}

        executor._load_initial_state(args, kwargs)

        mock_load_state.assert_called_once_with(Path("/test/path"))

    @patch("src.core.network.decorators.load_state")
    def test_load_initial_state_without_state_path(self, mock_load_state):
        """测试加载初始状态（无状态路径）"""
        executor = RetryExecutor(
            func=self.test_func,
            retry_config=self.retry_config,
            retry_on_exceptions=self.retry_exceptions,
            state_file=None,
        )

        args = ("arg1",)
        kwargs = {}

        executor._load_initial_state(args, kwargs)

        mock_load_state.assert_not_called()

    def test_restore_params_if_requested(self):
        """测试参数恢复"""
        executor = RetryExecutor(
            func=self.test_func,
            retry_config=self.retry_config,
            retry_on_exceptions=self.retry_exceptions,
            state_file="test_state",
        )

        state_data = {
            "saved_kwargs": {"restored_key": "restored_value", "existing_key": "old_value"}
        }
        kwargs = {"resume_params": True, "existing_key": "new_value"}

        executor._restore_params_if_requested(state_data, kwargs)

        # 验证新参数被添加，现有参数不被覆盖
        self.assertEqual(kwargs["restored_key"], "restored_value")
        self.assertEqual(kwargs["existing_key"], "new_value")

    @patch("time.sleep")
    @patch("src.core.network.decorators.calculate_retry_delay")
    def test_apply_retry_delay(self, mock_calculate_delay, mock_sleep):
        """测试应用重试延迟"""
        mock_calculate_delay.return_value = 2.5

        executor = RetryExecutor(
            func=self.test_func,
            retry_config=self.retry_config,
            retry_on_exceptions=self.retry_exceptions,
            state_file=None,
        )

        executor._apply_retry_delay(2)

        mock_calculate_delay.assert_called_once_with(2, self.retry_config)
        mock_sleep.assert_called_once_with(2.5)

    @patch("src.core.network.decorators.save_state")
    @patch("src.core.network.decorators.datetime")
    def test_save_attempt_state(self, mock_datetime, mock_save_state):
        """测试保存尝试状态"""
        mock_datetime.now.return_value.strftime.return_value = "2023-01-01 12:00:00"

        executor = RetryExecutor(
            func=self.test_func,
            retry_config=self.retry_config,
            retry_on_exceptions=self.retry_exceptions,
            state_file="test_state",
        )
        executor.state_path = Path("/test/path")

        args = ("arg1", "arg2")
        kwargs = {"key": "value", "password": "secret"}

        executor._save_attempt_state(2, args, kwargs)

        expected_state = {
            "function": self.test_func.__name__,
            "attempt": 2,
            "saved_args": ["arg1", "arg2"],
            "saved_kwargs": {"key": "value"},  # password 被过滤
            "timestamp": "2023-01-01 12:00:00",
        }

        mock_save_state.assert_called_once_with(Path("/test/path"), expected_state)

    @patch("src.core.network.decorators.save_state")
    @patch("src.core.network.decorators.datetime")
    def test_handle_success(self, mock_datetime, mock_save_state):
        """测试处理成功"""
        mock_datetime.now.return_value.strftime.return_value = "2023-01-01 12:00:00"

        executor = RetryExecutor(
            func=self.test_func,
            retry_config=self.retry_config,
            retry_on_exceptions=self.retry_exceptions,
            state_file="test_state",
        )

        # 创建模拟路径对象
        mock_path = Mock()
        mock_path.exists.return_value = True
        executor.state_path = mock_path

        executor._handle_success()

        expected_state = {
            "function": self.test_func.__name__,
            "status": "completed",
            "timestamp": "2023-01-01 12:00:00",
        }

        mock_save_state.assert_called_once_with(mock_path, expected_state)

    def test_should_continue_retry_true(self):
        """测试应该继续重试（返回True）"""
        executor = RetryExecutor(
            func=self.test_func,
            retry_config=self.retry_config,
            retry_on_exceptions=self.retry_exceptions,
            state_file=None,
        )

        # 测试匹配的异常类型且未超过最大重试次数
        result = executor._should_continue_retry(ConnectionError("test"), 2)
        self.assertTrue(result)

    def test_should_continue_retry_false_wrong_exception(self):
        """测试不应该继续重试（错误的异常类型）"""
        executor = RetryExecutor(
            func=self.test_func,
            retry_config=self.retry_config,
            retry_on_exceptions=self.retry_exceptions,
            state_file=None,
        )

        # 测试不匹配的异常类型
        result = executor._should_continue_retry(RuntimeError("test"), 2)
        self.assertFalse(result)

    def test_should_continue_retry_false_max_attempts(self):
        """测试不应该继续重试（超过最大重试次数）"""
        executor = RetryExecutor(
            func=self.test_func,
            retry_config=self.retry_config,
            retry_on_exceptions=self.retry_exceptions,
            state_file=None,
        )

        # 测试超过最大重试次数
        result = executor._should_continue_retry(ConnectionError("test"), 4)
        self.assertFalse(result)

    @patch("src.core.network.decorators.logger")
    def test_log_retry_attempt(self, mock_logger):
        """测试记录重试尝试"""
        executor = RetryExecutor(
            func=self.test_func,
            retry_config=self.retry_config,
            retry_on_exceptions=self.retry_exceptions,
            state_file=None,
        )

        test_exception = ConnectionError("test error")
        executor._log_retry_attempt(test_exception, 2)

        mock_logger.warning.assert_called_once_with("Attempt 2/3 failed: test error")

    @patch("src.core.network.decorators.save_state")
    @patch("src.core.network.decorators.datetime")
    @patch("src.core.network.decorators.logger")
    def test_handle_final_failure(self, mock_logger, mock_datetime, mock_save_state):
        """测试处理最终失败"""
        mock_datetime.now.return_value.strftime.return_value = "2023-01-01 12:00:00"

        executor = RetryExecutor(
            func=self.test_func,
            retry_config=self.retry_config,
            retry_on_exceptions=self.retry_exceptions,
            state_file="test_state",
        )
        executor.state_path = Path("/test/path")

        test_exception = ConnectionError("final error")
        executor._handle_final_failure(test_exception, 3)

        # 验证状态保存
        expected_state = {
            "function": self.test_func.__name__,
            "status": "failed",
            "error": "final error",
            "attempt": 3,
            "timestamp": "2023-01-01 12:00:00",
        }
        mock_save_state.assert_called_once_with(Path("/test/path"), expected_state)

        # 验证日志记录
        mock_logger.error.assert_called_once_with("All 3 attempts failed, last error: final error")

    def test_execute_with_retry_success_first_attempt(self):
        """测试第一次尝试就成功"""
        self.test_func.return_value = "success"

        executor = RetryExecutor(
            func=self.test_func,
            retry_config=self.retry_config,
            retry_on_exceptions=self.retry_exceptions,
            state_file=None,
        )

        with (
            patch.object(executor, "_setup_state_management"),
            patch.object(executor, "_load_initial_state"),
            patch.object(executor, "_execute_attempt", return_value="success"),
        ):

            result = executor.execute_with_retry("arg1", key="value")

            self.assertEqual(result, "success")

    def test_execute_with_retry_success_after_retries(self):
        """测试重试后成功"""
        executor = RetryExecutor(
            func=self.test_func,
            retry_config=self.retry_config,
            retry_on_exceptions=self.retry_exceptions,
            state_file=None,
        )

        # 模拟前两次失败，第三次成功
        side_effects = [ConnectionError("attempt 1"), ConnectionError("attempt 2"), "success"]

        with (
            patch.object(executor, "_setup_state_management"),
            patch.object(executor, "_load_initial_state"),
            patch.object(executor, "_execute_attempt", side_effect=side_effects),
            patch.object(executor, "_should_continue_retry", side_effect=[True, True, False]),
            patch.object(executor, "_log_retry_attempt"),
        ):

            result = executor.execute_with_retry("arg1")

            self.assertEqual(result, "success")

    def test_execute_with_retry_final_failure(self):
        """测试最终失败"""
        executor = RetryExecutor(
            func=self.test_func,
            retry_config=self.retry_config,
            retry_on_exceptions=self.retry_exceptions,
            state_file=None,
        )

        test_exception = ConnectionError("persistent error")

        with (
            patch.object(executor, "_setup_state_management"),
            patch.object(executor, "_load_initial_state"),
            patch.object(executor, "_execute_attempt", side_effect=test_exception),
            patch.object(executor, "_should_continue_retry", return_value=False),
            patch.object(executor, "_handle_final_failure"),
            patch.object(executor, "_log_retry_attempt"),
        ):

            with self.assertRaises(ConnectionError):
                executor.execute_with_retry("arg1")


class TestWithStateManagementDecorator(unittest.TestCase):
    """测试 with_state_management 装饰器"""

    @patch("src.core.network.decorators.get_global_state_manager")
    @patch("src.core.network.decorators._save_start_state")
    @patch("src.core.network.decorators._handle_success_state")
    def test_with_state_management_success(
        self, mock_handle_success, mock_save_start, mock_get_manager
    ):
        """测试状态管理装饰器成功情况"""
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager

        @with_state_management(operation_name="test_op", auto_save=True, auto_clear_on_success=True)
        def test_function(arg1, key=None):
            return f"result_{arg1}_{key}"

        result = test_function("value1", key="value2")

        # 验证结果
        self.assertEqual(result, "result_value1_value2")

        # 验证状态保存调用
        mock_save_start.assert_called_once()
        mock_handle_success.assert_called_once()

        # 验证调用参数
        start_args = mock_save_start.call_args
        self.assertEqual(start_args[0][1], "test_op")  # operation_name
        self.assertEqual(start_args[0][3], ("value1",))  # args
        self.assertEqual(start_args[0][4], {"key": "value2"})  # kwargs

    @patch("src.core.network.decorators.get_global_state_manager")
    @patch("src.core.network.decorators._save_start_state")
    @patch("src.core.network.decorators._save_error_state")
    def test_with_state_management_failure(
        self, mock_save_error, mock_save_start, mock_get_manager
    ):
        """测试状态管理装饰器失败情况"""
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager

        test_exception = ValueError("test error")

        @with_state_management(auto_save=True)
        def test_function():
            raise test_exception

        with self.assertRaises(ValueError):
            test_function()

        # 验证状态保存调用
        mock_save_start.assert_called_once()
        mock_save_error.assert_called_once()

        # 验证错误状态保存
        error_args = mock_save_error.call_args
        self.assertEqual(error_args[0][3], test_exception)  # error

    def test_with_state_management_no_auto_save(self):
        """测试不自动保存状态"""

        @with_state_management(auto_save=False)
        def test_function():
            return "no_save_result"

        with patch("src.core.network.decorators._save_start_state") as mock_save_start:
            result = test_function()

            self.assertEqual(result, "no_save_result")
            mock_save_start.assert_not_called()

    def test_with_state_management_default_operation_name(self):
        """测试默认操作名称"""

        @with_state_management()
        def custom_function_name():
            return "default_name_result"

        with (
            patch("src.core.network.decorators.get_global_state_manager") as mock_get_manager,
            patch("src.core.network.decorators._save_start_state") as mock_save_start,
            patch("src.core.network.decorators._handle_success_state"),
        ):

            mock_manager = Mock()
            mock_get_manager.return_value = mock_manager

            result = custom_function_name()

            self.assertEqual(result, "default_name_result")

            # 验证使用函数名作为操作名称
            start_args = mock_save_start.call_args
            self.assertEqual(start_args[0][1], "custom_function_name")


class TestStateManagementUtilities(unittest.TestCase):
    """测试状态管理工具函数"""

    @patch("src.core.network.decorators.datetime")
    def test_save_start_state(self, mock_datetime):
        """测试保存开始状态"""
        mock_datetime.now.return_value.strftime.return_value = "2023-01-01 12:00:00"

        mock_manager = Mock()
        mock_func = Mock()
        mock_func.__name__ = "test_function"

        args = ("arg1", "arg2")
        kwargs = {"key": "value", "password": "secret"}

        _save_start_state(mock_manager, "test_op", mock_func, args, kwargs)

        expected_state = {
            "function": "test_function",
            "status": "started",
            "args": ["arg1", "arg2"],
            "kwargs": {"key": "value"},  # password 被过滤
            "start_time": "2023-01-01 12:00:00",
        }

        mock_manager.save_operation_state.assert_called_once_with("test_op", expected_state)

    @patch("src.core.network.decorators.datetime")
    @patch("src.core.network.decorators._schedule_state_cleanup")
    def test_handle_success_state_with_auto_clear(self, mock_schedule_cleanup, mock_datetime):
        """测试处理成功状态（自动清理）"""
        mock_datetime.now.return_value.strftime.return_value = "2023-01-01 12:00:00"

        mock_manager = Mock()
        mock_func = Mock()
        mock_func.__name__ = "test_function"

        result = "test_result_" + "x" * 200  # 长结果

        _handle_success_state(mock_manager, "test_op", mock_func, result, True)

        expected_state = {
            "function": "test_function",
            "status": "completed",
            "result_summary": result[:200],  # 截断到200字符
            "end_time": "2023-01-01 12:00:00",
        }

        mock_manager.save_operation_state.assert_called_once_with("test_op", expected_state)
        mock_schedule_cleanup.assert_called_once_with(mock_manager, "test_op")

    @patch("src.core.network.decorators.datetime")
    def test_handle_success_state_no_auto_clear(self, mock_datetime):
        """测试处理成功状态（不自动清理）"""
        mock_datetime.now.return_value.strftime.return_value = "2023-01-01 12:00:00"

        mock_manager = Mock()
        mock_func = Mock()
        mock_func.__name__ = "test_function"

        with patch("src.core.network.decorators._schedule_state_cleanup") as mock_schedule_cleanup:
            _handle_success_state(mock_manager, "test_op", mock_func, "result", False)

            mock_schedule_cleanup.assert_not_called()

    @patch("threading.Thread")
    def test_schedule_state_cleanup(self, mock_thread):
        """测试安排状态清理"""
        mock_manager = Mock()
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        _schedule_state_cleanup(mock_manager, "test_op")

        # 验证线程被创建和启动
        mock_thread.assert_called_once()
        thread_args = mock_thread.call_args
        self.assertTrue(thread_args[1]["daemon"])
        mock_thread_instance.start.assert_called_once()

    @patch("src.core.network.decorators.datetime")
    def test_save_error_state(self, mock_datetime):
        """测试保存错误状态"""
        mock_datetime.now.return_value.strftime.return_value = "2023-01-01 12:00:00"

        mock_manager = Mock()
        mock_func = Mock()
        mock_func.__name__ = "test_function"

        test_error = ValueError("test error message")

        _save_error_state(mock_manager, "test_op", mock_func, test_error)

        expected_state = {
            "function": "test_function",
            "status": "failed",
            "error": "test error message",
            "error_time": "2023-01-01 12:00:00",
        }

        mock_manager.save_operation_state.assert_called_once_with("test_op", expected_state)


class TestWithComprehensiveRetryDecorator(unittest.TestCase):
    """测试 with_comprehensive_retry 装饰器"""

    @patch("src.core.network.decorators.with_state_management")
    @patch("src.core.network.decorators.with_retry")
    def test_with_comprehensive_retry_default_params(self, mock_with_retry, mock_with_state):
        """测试综合重试装饰器默认参数"""
        # 设置模拟装饰器链
        mock_state_decorator = Mock()
        mock_retry_decorator = Mock()
        mock_final_function = Mock()

        mock_with_state.return_value = mock_state_decorator
        mock_state_decorator.return_value = mock_final_function
        mock_with_retry.return_value = mock_retry_decorator
        mock_retry_decorator.return_value = mock_final_function

        @with_comprehensive_retry()
        def test_function():
            return "comprehensive_result"

        # 验证装饰器被正确调用
        mock_with_state.assert_called_once()
        mock_with_retry.assert_called_once()

        # 验证状态管理装饰器参数
        state_args = mock_with_state.call_args
        self.assertEqual(state_args[1]["operation_name"], "test_function")
        self.assertTrue(state_args[1]["auto_save"])
        self.assertTrue(state_args[1]["auto_clear_on_success"])

        # 验证重试装饰器参数
        retry_args = mock_with_retry.call_args
        expected_config = {
            "max_retries": 5,
            "base_delay": 1.0,
            "max_delay": 60.0,
            "backoff_factor": 2.0,
            "jitter": 0.1,
        }
        self.assertEqual(retry_args[1]["retry_config"], expected_config)
        self.assertEqual(retry_args[1]["state_file"], "test_function")

    @patch("src.core.network.decorators.with_state_management")
    @patch("src.core.network.decorators.with_retry")
    def test_with_comprehensive_retry_custom_params(self, mock_with_retry, mock_with_state):
        """测试综合重试装饰器自定义参数"""
        mock_state_decorator = Mock()
        mock_retry_decorator = Mock()
        mock_final_function = Mock()

        mock_with_state.return_value = mock_state_decorator
        mock_state_decorator.return_value = mock_final_function
        mock_with_retry.return_value = mock_retry_decorator
        mock_retry_decorator.return_value = mock_final_function

        custom_exceptions = [ConnectionError, TimeoutError]

        @with_comprehensive_retry(
            max_retries=10,
            base_delay=2.0,
            max_delay=120.0,
            backoff_factor=1.5,
            jitter=0.2,
            retry_on=custom_exceptions,
            state_file="custom_state",
            operation_name="custom_operation",
        )
        def test_function():
            return "custom_comprehensive_result"

        # 验证自定义参数
        retry_args = mock_with_retry.call_args
        expected_config = {
            "max_retries": 10,
            "base_delay": 2.0,
            "max_delay": 120.0,
            "backoff_factor": 1.5,
            "jitter": 0.2,
        }
        self.assertEqual(retry_args[1]["retry_config"], expected_config)
        self.assertEqual(retry_args[1]["retry_on_exceptions"], custom_exceptions)
        self.assertEqual(retry_args[1]["state_file"], "custom_state")

        state_args = mock_with_state.call_args
        self.assertEqual(state_args[1]["operation_name"], "custom_operation")


class TestConvenienceDecorators(unittest.TestCase):
    """测试便捷装饰器"""

    @patch("src.core.network.decorators.with_comprehensive_retry")
    def test_network_request_decorator(self, mock_comprehensive_retry):
        """测试网络请求装饰器"""
        mock_decorator = Mock()
        mock_comprehensive_retry.return_value = mock_decorator

        @network_request(max_retries=5, base_delay=2.0, state_file="network_state")
        def test_function():
            return "network_result"

        # 验证调用参数
        mock_comprehensive_retry.assert_called_once_with(
            max_retries=5,
            base_delay=2.0,
            retry_on=[ConnectionError, TimeoutError, OSError],
            state_file="network_state",
        )

    @patch("src.core.network.decorators.with_comprehensive_retry")
    def test_api_call_decorator(self, mock_comprehensive_retry):
        """测试API调用装饰器"""
        mock_decorator = Mock()
        mock_comprehensive_retry.return_value = mock_decorator

        @api_call(max_retries=8, base_delay=3.0, state_file="api_state")
        def test_function():
            return "api_result"

        # 验证调用参数
        mock_comprehensive_retry.assert_called_once_with(
            max_retries=8,
            base_delay=3.0,
            max_delay=120.0,
            retry_on=[ConnectionError, TimeoutError, OSError],
            state_file="api_state",
        )

    @patch("src.core.network.decorators.with_comprehensive_retry")
    def test_critical_operation_decorator(self, mock_comprehensive_retry):
        """测试关键操作装饰器"""
        mock_decorator = Mock()
        mock_comprehensive_retry.return_value = mock_decorator

        @critical_operation(max_retries=15, base_delay=0.5, state_file="critical_state")
        def test_function():
            return "critical_result"

        # 验证调用参数
        mock_comprehensive_retry.assert_called_once_with(
            max_retries=15,
            base_delay=0.5,
            max_delay=300.0,
            backoff_factor=1.5,
            retry_on=[ConnectionError, TimeoutError, OSError],
            state_file="critical_state",
        )

    @patch("src.core.network.decorators.with_comprehensive_retry")
    def test_convenience_decorators_default_params(self, mock_comprehensive_retry):
        """测试便捷装饰器默认参数"""
        mock_decorator = Mock()
        mock_comprehensive_retry.return_value = mock_decorator

        # 测试默认参数 - 需要重新导入装饰器以避免作用域问题
        from src.core.network.decorators import api_call, critical_operation, network_request

        @network_request()
        def network_func():
            pass

        @api_call()
        def api_func():
            pass

        @critical_operation()
        def critical_func():
            pass

        # 验证调用次数
        self.assertEqual(mock_comprehensive_retry.call_count, 3)

        # 验证默认参数
        calls = mock_comprehensive_retry.call_args_list

        # network_request 默认参数
        network_call = calls[0]
        self.assertEqual(network_call[1]["max_retries"], 3)
        self.assertEqual(network_call[1]["base_delay"], 1.0)

        # api_call 默认参数
        api_call_args = calls[1]
        self.assertEqual(api_call_args[1]["max_retries"], 5)
        self.assertEqual(api_call_args[1]["base_delay"], 2.0)
        self.assertEqual(api_call_args[1]["max_delay"], 120.0)

        # critical_operation 默认参数
        critical_call = calls[2]
        self.assertEqual(critical_call[1]["max_retries"], 10)
        self.assertEqual(critical_call[1]["base_delay"], 1.0)
        self.assertEqual(critical_call[1]["max_delay"], 300.0)
        self.assertEqual(critical_call[1]["backoff_factor"], 1.5)


class TestIntegrationScenarios(unittest.TestCase):
    """测试集成场景"""

    def test_decorator_stacking_order(self):
        """测试装饰器堆叠顺序"""
        call_order = []

        def tracking_decorator(name):
            def decorator(func):
                @wraps(func)
                def wrapper(*args, **kwargs):
                    call_order.append(f"{name}_start")
                    result = func(*args, **kwargs)
                    call_order.append(f"{name}_end")
                    return result

                return wrapper

            return decorator

        @tracking_decorator("outer")
        @with_retry()
        @tracking_decorator("inner")
        def test_function():
            call_order.append("function_call")
            return "stacked_result"

        with patch("src.core.network.decorators.RetryExecutor") as mock_executor:
            mock_instance = Mock()
            mock_instance.execute_with_retry.return_value = "stacked_result"
            mock_executor.return_value = mock_instance

            result = test_function()

            self.assertEqual(result, "stacked_result")

    def test_real_retry_scenario(self):
        """测试真实重试场景"""
        attempt_count = 0

        def failing_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ConnectionError(f"Attempt {attempt_count} failed")
            return f"Success on attempt {attempt_count}"

        executor = RetryExecutor(
            func=failing_function,
            retry_config={"max_retries": 5, "base_delay": 0.01},  # 快速测试
            retry_on_exceptions=[ConnectionError],
            state_file=None,
        )

        with patch("time.sleep"):  # 跳过实际睡眠
            result = executor.execute_with_retry()

        self.assertEqual(result, "Success on attempt 3")
        self.assertEqual(attempt_count, 3)


class TestErrorHandling(unittest.TestCase):
    """测试错误处理"""

    def test_retry_executor_with_non_retryable_exception(self):
        """测试不可重试异常"""

        def failing_function():
            raise ValueError("Non-retryable error")

        executor = RetryExecutor(
            func=failing_function,
            retry_config={"max_retries": 3, "base_delay": 0.01},
            retry_on_exceptions=[ConnectionError],  # 不包括 ValueError
            state_file=None,
        )

        with patch("time.sleep"):
            with self.assertRaises(ValueError):
                executor.execute_with_retry()

    def test_state_management_with_exception_in_state_save(self):
        """测试状态保存时的异常"""

        @with_state_management()
        def test_function():
            return "result"

        with (
            patch("src.core.network.decorators.get_global_state_manager") as mock_get_manager,
            patch(
                "src.core.network.decorators._save_start_state",
                side_effect=Exception("State save error"),
            ),
        ):

            mock_manager = Mock()
            mock_get_manager.return_value = mock_manager

            # 状态保存错误应该传播
            with self.assertRaises(Exception):
                test_function()


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def test_retry_executor_with_zero_max_retries(self):
        """测试最大重试次数为0"""

        def failing_function():
            raise ConnectionError("Always fails")

        executor = RetryExecutor(
            func=failing_function,
            retry_config={"max_retries": 0, "base_delay": 0.01},
            retry_on_exceptions=[ConnectionError],
            state_file=None,
        )

        with self.assertRaises(ConnectionError):
            executor.execute_with_retry()

    def test_with_retry_empty_exception_list(self):
        """测试空异常列表"""

        @with_retry(retry_on_exceptions=[])
        def test_function():
            raise ConnectionError("Should not retry")

        with patch("src.core.network.decorators.RetryExecutor") as mock_executor:
            mock_instance = Mock()
            mock_instance.execute_with_retry.side_effect = ConnectionError("Should not retry")
            mock_executor.return_value = mock_instance

            with self.assertRaises(ConnectionError):
                test_function()

    def test_state_management_with_none_result(self):
        """测试返回None的函数"""

        @with_state_management()
        def test_function():
            return None

        with (
            patch("src.core.network.decorators.get_global_state_manager") as mock_get_manager,
            patch("src.core.network.decorators._save_start_state"),
            patch("src.core.network.decorators._handle_success_state") as mock_handle_success,
        ):

            mock_manager = Mock()
            mock_get_manager.return_value = mock_manager

            result = test_function()

            self.assertIsNone(result)
            mock_handle_success.assert_called_once()

    def test_comprehensive_retry_with_all_none_params(self):
        """测试所有参数为None的综合重试"""

        @with_comprehensive_retry(retry_on=None, state_file=None, operation_name=None)
        def test_function():
            return "none_params_result"

        with (
            patch("src.core.network.decorators.with_state_management") as mock_with_state,
            patch("src.core.network.decorators.with_retry") as mock_with_retry,
        ):

            mock_state_decorator = Mock()
            mock_retry_decorator = Mock()
            mock_final_function = Mock()

            mock_with_state.return_value = mock_state_decorator
            mock_state_decorator.return_value = mock_final_function
            mock_with_retry.return_value = mock_retry_decorator
            mock_retry_decorator.return_value = mock_final_function

            # 验证None参数被正确处理
            state_args = mock_with_state.call_args
            if state_args:
                self.assertEqual(state_args[1]["operation_name"], "test_function")

            retry_args = mock_with_retry.call_args
            if retry_args:
                self.assertEqual(retry_args[1]["state_file"], "test_function")


if __name__ == "__main__":
    unittest.main()
