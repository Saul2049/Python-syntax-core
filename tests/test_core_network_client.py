#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 src.core.network.client 模块的所有功能
Network Client Module Tests

覆盖目标:
- NetworkClient 基类功能
- StatefulNetworkClient 子类功能
- 重试机制集成
- 状态管理集成
- 便捷函数
- 错误处理和边界情况
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import modules to test
try:
    from src.core.network.client import (
        NetworkClient,
        StatefulNetworkClient,
        create_simple_client,
        create_stateful_client,
    )
    from src.core.network.retry_manager import DEFAULT_RETRY_CONFIG
except ImportError:
    pytest.skip("Network client module not available, skipping tests", allow_module_level=True)


class TestNetworkClient(unittest.TestCase):
    """测试 NetworkClient 基类"""

    def setUp(self):
        """设置测试环境"""
        # 🧹 不再需要手动创建临时目录，使用上下文管理器或fixture
        pass

    def tearDown(self):
        """清理测试环境"""
        # 🧹 不再需要手动清理，上下文管理器会自动处理
        pass

    @patch("src.core.network.client.StateManager")
    @patch("src.core.network.client.RetryManager")
    def test_init_default(self, mock_retry_manager, mock_state_manager):
        """测试默认初始化"""
        client = NetworkClient()

        # 验证状态管理器初始化
        mock_state_manager.assert_called_once_with(None)

        # 验证重试管理器初始化
        mock_retry_manager.assert_called_once()
        call_args = mock_retry_manager.call_args
        self.assertEqual(call_args[1]["default_config"], DEFAULT_RETRY_CONFIG)
        self.assertEqual(
            call_args[1]["default_exceptions"], [ConnectionError, TimeoutError, OSError]
        )

        # 验证客户端创建成功
        self.assertIsNotNone(client)

    @patch("src.core.network.client.StateManager")
    @patch("src.core.network.client.RetryManager")
    def test_init_with_custom_config(self, mock_retry_manager, mock_state_manager):
        """测试自定义配置初始化"""
        custom_retry_config = {"max_retries": 5, "base_delay": 2.0}
        custom_exceptions = [ValueError, RuntimeError]

        # 🧹 使用临时目录上下文管理器
        with tempfile.TemporaryDirectory() as temp_dir:
            client = NetworkClient(
                state_dir=str(temp_dir),
                retry_config=custom_retry_config,
                retry_exceptions=custom_exceptions,
            )

            # 验证状态管理器初始化
            mock_state_manager.assert_called_once_with(str(temp_dir))

            # 验证重试管理器初始化
            mock_retry_manager.assert_called_once()
            call_args = mock_retry_manager.call_args
            self.assertEqual(call_args[1]["default_config"], custom_retry_config)
            self.assertEqual(call_args[1]["default_exceptions"], custom_exceptions)

            # 验证客户端创建成功
            self.assertIsNotNone(client)

    def test_get_state_path(self):
        """测试获取状态路径"""
        with patch("src.core.network.client.StateManager") as mock_state_manager:
            mock_instance = Mock()
            mock_instance.get_state_path.return_value = Path("/test/path")
            mock_state_manager.return_value = mock_instance

            client = NetworkClient()
            result = client.get_state_path("test_operation")

            mock_instance.get_state_path.assert_called_once_with("test_operation")
            self.assertEqual(result, Path("/test/path"))

    def test_save_operation_state(self):
        """测试保存操作状态"""
        with patch("src.core.network.client.StateManager") as mock_state_manager:
            mock_instance = Mock()
            mock_instance.save_operation_state.return_value = True
            mock_state_manager.return_value = mock_instance

            client = NetworkClient()
            state_data = {"key": "value"}
            result = client.save_operation_state("test_op", state_data)

            mock_instance.save_operation_state.assert_called_once_with("test_op", state_data)
            self.assertTrue(result)

    def test_load_operation_state(self):
        """测试加载操作状态"""
        with patch("src.core.network.client.StateManager") as mock_state_manager:
            mock_instance = Mock()
            expected_state = {"loaded": "data"}
            mock_instance.load_operation_state.return_value = expected_state
            mock_state_manager.return_value = mock_instance

            client = NetworkClient()
            result = client.load_operation_state("test_op")

            mock_instance.load_operation_state.assert_called_once_with("test_op")
            self.assertEqual(result, expected_state)

    def test_clear_operation_state(self):
        """测试清除操作状态"""
        with patch("src.core.network.client.StateManager") as mock_state_manager:
            mock_instance = Mock()
            mock_instance.clear_operation_state.return_value = True
            mock_state_manager.return_value = mock_instance

            client = NetworkClient()
            result = client.clear_operation_state("test_op")

            mock_instance.clear_operation_state.assert_called_once_with("test_op")
            self.assertTrue(result)

    def test_execute_with_retry(self):
        """测试重试执行"""
        with patch("src.core.network.client.RetryManager") as mock_retry_manager:
            mock_instance = Mock()
            mock_instance.execute_with_retry.return_value = "success"
            mock_retry_manager.return_value = mock_instance

            client = NetworkClient()
            test_func = Mock()
            retry_config = {"max_retries": 3}
            retry_exceptions = [ValueError]

            result = client.execute_with_retry(
                test_func,
                "arg1",
                "arg2",
                retry_config=retry_config,
                retry_on_exceptions=retry_exceptions,
                kwarg1="value1",
            )

            mock_instance.execute_with_retry.assert_called_once_with(
                test_func,
                "arg1",
                "arg2",
                retry_config=retry_config,
                retry_on_exceptions=retry_exceptions,
                kwarg1="value1",
            )
            self.assertEqual(result, "success")

    def test_create_retry_decorator(self):
        """测试创建重试装饰器"""
        with patch("src.core.network.client.RetryManager") as mock_retry_manager:
            mock_instance = Mock()
            mock_decorator = Mock()
            mock_instance.create_decorator.return_value = mock_decorator
            mock_retry_manager.return_value = mock_instance

            client = NetworkClient()
            retry_config = {"max_retries": 2}
            retry_exceptions = [ConnectionError]

            result = client.create_retry_decorator(
                retry_config=retry_config, retry_on_exceptions=retry_exceptions
            )

            mock_instance.create_decorator.assert_called_once_with(
                retry_config=retry_config, retry_on_exceptions=retry_exceptions
            )
            self.assertEqual(result, mock_decorator)

    @patch("src.core.network.client.time.sleep")
    @patch("src.core.network.client.random.random")
    @patch("src.core.network.client.logger")
    def test_example_request_success(self, mock_logger, mock_random, mock_sleep):
        """测试示例请求成功"""
        # 模拟成功情况（不触发随机失败）
        mock_random.return_value = 0.8  # > 0.3，不会失败

        with patch("src.core.network.client.RetryManager") as mock_retry_manager:
            mock_instance = Mock()

            def side_effect(func, *args, **kwargs):
                return func()

            mock_instance.execute_with_retry.side_effect = side_effect
            mock_retry_manager.return_value = mock_instance

            client = NetworkClient()
            result = client.example_request("http://test.com", {"param": "value"})

            # 验证日志记录
            mock_logger.info.assert_called_once_with(
                "Making request to http://test.com with params: {'param': 'value'}"
            )

            # 验证睡眠调用
            mock_sleep.assert_called_once_with(0.5)

            # 验证返回结果
            expected_result = {"status": "success", "data": {"result": "some data"}}
            self.assertEqual(result, expected_result)

    @patch("src.core.network.client.time.sleep")
    @patch("src.core.network.client.random.random")
    @patch("src.core.network.client.logger")
    def test_example_request_failure(self, mock_logger, mock_random, mock_sleep):
        """测试示例请求失败"""
        # 模拟失败情况
        mock_random.return_value = 0.1  # < 0.3，会失败

        with patch("src.core.network.client.RetryManager") as mock_retry_manager:
            mock_instance = Mock()

            def side_effect(func, *args, **kwargs):
                return func()

            mock_instance.execute_with_retry.side_effect = side_effect
            mock_retry_manager.return_value = mock_instance

            client = NetworkClient()

            with self.assertRaises(ConnectionError) as context:
                client.example_request("http://test.com", {"param": "value"})

            self.assertEqual(str(context.exception), "Simulated network error")

    def test_get_status(self):
        """测试获取状态信息"""
        with (
            patch("src.core.network.client.StateManager") as mock_state_manager,
            patch("src.core.network.client.RetryManager") as mock_retry_manager,
        ):

            # 设置状态管理器模拟
            mock_state_instance = Mock()
            mock_state_instance.get_state_summary.return_value = {"states": 5}
            mock_state_manager.return_value = mock_state_instance

            # 设置重试管理器模拟
            mock_retry_instance = Mock()
            mock_retry_instance.default_config = {"max_retries": 3}
            mock_retry_instance.default_exceptions = [ConnectionError, ValueError]
            mock_retry_manager.return_value = mock_retry_instance

            client = NetworkClient()
            status = client.get_status()

            expected_status = {
                "state_manager": {"states": 5},
                "retry_config": {"max_retries": 3},
                "retry_exceptions": ["ConnectionError", "ValueError"],
            }
            self.assertEqual(status, expected_status)


class TestStatefulNetworkClient(unittest.TestCase):
    """测试 StatefulNetworkClient 子类"""

    def setUp(self):
        """设置测试环境"""
        # 🧹 不再需要手动创建临时目录，使用上下文管理器或fixture
        pass

    def tearDown(self):
        """清理测试环境"""
        # 🧹 不再需要手动清理，上下文管理器会自动处理
        pass

    @patch("src.core.network.client.StateManager")
    @patch("src.core.network.client.RetryManager")
    def test_init(self, mock_retry_manager, mock_state_manager):
        """测试初始化"""
        # 🧹 使用临时目录上下文管理器
        with tempfile.TemporaryDirectory() as temp_dir:
            client = StatefulNetworkClient(state_dir=str(temp_dir))

            # 验证继承的初始化
            mock_state_manager.assert_called_once_with(str(temp_dir))
            mock_retry_manager.assert_called_once()

            # 验证操作计数器初始化
            self.assertEqual(client._operation_counter, 0)

    def test_get_next_operation_id(self):
        """测试获取下一个操作ID"""
        with (
            patch("src.core.network.client.StateManager"),
            patch("src.core.network.client.RetryManager"),
        ):

            client = StatefulNetworkClient()

            # 测试连续获取操作ID
            id1 = client._get_next_operation_id()
            id2 = client._get_next_operation_id()
            id3 = client._get_next_operation_id()

            self.assertEqual(id1, "operation_1")
            self.assertEqual(id2, "operation_2")
            self.assertEqual(id3, "operation_3")
            self.assertEqual(client._operation_counter, 3)

    def test_stateful_request_success_with_auto_id(self):
        """测试有状态请求成功（自动生成ID）"""
        with (
            patch("src.core.network.client.StateManager") as mock_state_manager,
            patch("src.core.network.client.RetryManager") as mock_retry_manager,
        ):

            # 设置模拟
            mock_state_instance = Mock()
            mock_state_manager.return_value = mock_state_instance

            mock_retry_instance = Mock()
            mock_retry_instance.execute_with_retry.return_value = "success_result"
            mock_retry_manager.return_value = mock_retry_instance

            client = StatefulNetworkClient()
            test_func = Mock()

            result = client.stateful_request(test_func, "arg1", "arg2", kwarg1="value1")

            # 验证结果
            self.assertEqual(result, "success_result")

            # 验证状态保存调用
            self.assertEqual(mock_state_instance.save_operation_state.call_count, 2)

            # 验证开始状态保存
            start_call = mock_state_instance.save_operation_state.call_args_list[0]
            self.assertEqual(start_call[0][0], "operation_1")
            start_state = start_call[0][1]
            self.assertEqual(start_state["status"], "started")
            self.assertEqual(start_state["operation_id"], "operation_1")

            # 验证成功状态保存
            success_call = mock_state_instance.save_operation_state.call_args_list[1]
            self.assertEqual(success_call[0][0], "operation_1")
            success_state = success_call[0][1]
            self.assertEqual(success_state["status"], "completed")
            self.assertEqual(success_state["operation_id"], "operation_1")

    def test_stateful_request_success_with_custom_id(self):
        """测试有状态请求成功（自定义ID）"""
        with (
            patch("src.core.network.client.StateManager") as mock_state_manager,
            patch("src.core.network.client.RetryManager") as mock_retry_manager,
        ):

            # 设置模拟
            mock_state_instance = Mock()
            mock_state_manager.return_value = mock_state_instance

            mock_retry_instance = Mock()
            mock_retry_instance.execute_with_retry.return_value = "custom_result"
            mock_retry_manager.return_value = mock_retry_instance

            client = StatefulNetworkClient()
            test_func = Mock()

            result = client.stateful_request(
                test_func, "arg1", operation_id="custom_op_123", kwarg1="value1"
            )

            # 验证结果
            self.assertEqual(result, "custom_result")

            # 验证状态保存使用自定义ID
            calls = mock_state_instance.save_operation_state.call_args_list
            self.assertEqual(len(calls), 2)

            # 验证所有调用都使用自定义ID
            for call_args in calls:
                self.assertEqual(call_args[0][0], "custom_op_123")

    def test_stateful_request_failure(self):
        """测试有状态请求失败"""
        with (
            patch("src.core.network.client.StateManager") as mock_state_manager,
            patch("src.core.network.client.RetryManager") as mock_retry_manager,
        ):

            # 设置模拟
            mock_state_instance = Mock()
            mock_state_manager.return_value = mock_state_instance

            mock_retry_instance = Mock()
            test_error = ValueError("Test error")
            mock_retry_instance.execute_with_retry.side_effect = test_error
            mock_retry_manager.return_value = mock_retry_instance

            client = StatefulNetworkClient()
            test_func = Mock()

            with self.assertRaises(ValueError) as context:
                client.stateful_request(test_func, "arg1", operation_id="fail_op")

            self.assertEqual(str(context.exception), "Test error")

            # 验证状态保存调用
            self.assertEqual(mock_state_instance.save_operation_state.call_count, 2)

            # 验证失败状态保存
            error_call = mock_state_instance.save_operation_state.call_args_list[1]
            self.assertEqual(error_call[0][0], "fail_op")
            error_state = error_call[0][1]
            self.assertEqual(error_state["status"], "failed")
            self.assertEqual(error_state["error"], "Test error")

    def test_stateful_request_no_save_state(self):
        """测试有状态请求不保存状态"""
        with (
            patch("src.core.network.client.StateManager") as mock_state_manager,
            patch("src.core.network.client.RetryManager") as mock_retry_manager,
        ):

            # 设置模拟
            mock_state_instance = Mock()
            mock_state_manager.return_value = mock_state_instance

            mock_retry_instance = Mock()
            mock_retry_instance.execute_with_retry.return_value = "no_save_result"
            mock_retry_manager.return_value = mock_retry_instance

            client = StatefulNetworkClient()
            test_func = Mock()

            result = client.stateful_request(test_func, "arg1", save_state=False)

            # 验证结果
            self.assertEqual(result, "no_save_result")

            # 验证没有状态保存调用
            mock_state_instance.save_operation_state.assert_not_called()

    def test_stateful_request_password_filtering(self):
        """测试有状态请求过滤密码参数"""
        with (
            patch("src.core.network.client.StateManager") as mock_state_manager,
            patch("src.core.network.client.RetryManager") as mock_retry_manager,
        ):

            # 设置模拟
            mock_state_instance = Mock()
            mock_state_manager.return_value = mock_state_instance

            mock_retry_instance = Mock()
            mock_retry_instance.execute_with_retry.return_value = "filtered_result"
            mock_retry_manager.return_value = mock_retry_instance

            client = StatefulNetworkClient()
            test_func = Mock()

            result = client.stateful_request(
                test_func, username="user", password="secret123", api_key="key123"
            )

            # 验证结果
            self.assertEqual(result, "filtered_result")

            # 验证开始状态不包含密码
            start_call = mock_state_instance.save_operation_state.call_args_list[0]
            start_state = start_call[0][1]
            saved_kwargs = start_state["kwargs"]

            # 密码应该被过滤掉
            self.assertNotIn("password", saved_kwargs)
            # 其他参数应该保留
            self.assertIn("api_key", saved_kwargs)

    def test_stateful_request_long_result_truncation(self):
        """测试有状态请求长结果截断"""
        with (
            patch("src.core.network.client.StateManager") as mock_state_manager,
            patch("src.core.network.client.RetryManager") as mock_retry_manager,
        ):

            # 设置模拟
            mock_state_instance = Mock()
            mock_state_manager.return_value = mock_state_instance

            # 创建长结果
            long_result = "x" * 200  # 超过100字符的结果
            mock_retry_instance = Mock()
            mock_retry_instance.execute_with_retry.return_value = long_result
            mock_retry_manager.return_value = mock_retry_instance

            client = StatefulNetworkClient()
            test_func = Mock()

            result = client.stateful_request(test_func)

            # 验证结果
            self.assertEqual(result, long_result)

            # 验证成功状态中的结果被截断
            success_call = mock_state_instance.save_operation_state.call_args_list[1]
            success_state = success_call[0][1]
            result_summary = success_state["result_summary"]

            # 结果摘要应该被截断到100字符
            self.assertEqual(len(result_summary), 100)
            self.assertEqual(result_summary, "x" * 100)


class TestConvenienceFunctions(unittest.TestCase):
    """测试便捷函数"""

    @patch("src.core.network.client.NetworkClient")
    def test_create_simple_client_default(self, mock_network_client):
        """测试创建简单客户端（默认参数）"""
        mock_instance = Mock()
        mock_network_client.return_value = mock_instance

        result = create_simple_client()

        mock_network_client.assert_called_once_with(state_dir=None)
        self.assertEqual(result, mock_instance)

    @patch("src.core.network.client.NetworkClient")
    def test_create_simple_client_with_state_dir(self, mock_network_client):
        """测试创建简单客户端（指定状态目录）"""
        mock_instance = Mock()
        mock_network_client.return_value = mock_instance

        result = create_simple_client(state_dir="/test/state")

        mock_network_client.assert_called_once_with(state_dir="/test/state")
        self.assertEqual(result, mock_instance)

    @patch("src.core.network.client.StatefulNetworkClient")
    def test_create_stateful_client_default(self, mock_stateful_client):
        """测试创建有状态客户端（默认参数）"""
        mock_instance = Mock()
        mock_stateful_client.return_value = mock_instance

        result = create_stateful_client()

        mock_stateful_client.assert_called_once_with(state_dir=None)
        self.assertEqual(result, mock_instance)

    @patch("src.core.network.client.StatefulNetworkClient")
    def test_create_stateful_client_with_state_dir(self, mock_stateful_client):
        """测试创建有状态客户端（指定状态目录）"""
        mock_instance = Mock()
        mock_stateful_client.return_value = mock_instance

        result = create_stateful_client(state_dir="/test/stateful")

        mock_stateful_client.assert_called_once_with(state_dir="/test/stateful")
        self.assertEqual(result, mock_instance)


class TestIntegrationScenarios(unittest.TestCase):
    """测试集成场景"""

    def setUp(self):
        """设置测试环境"""
        # 🧹 不再需要手动创建临时目录，使用上下文管理器或fixture
        pass

    def tearDown(self):
        """清理测试环境"""
        # 🧹 不再需要手动清理，上下文管理器会自动处理
        pass

    def test_network_client_integration(self):
        """测试网络客户端集成"""
        # 🧹 使用临时目录上下文管理器
        with tempfile.TemporaryDirectory() as temp_dir:
            # 测试完整的客户端工作流程
            with (
                patch("src.core.network.client.time.sleep"),
                patch("src.core.network.client.random.random", return_value=0.8),
            ):

                client = NetworkClient(state_dir=str(temp_dir))

                # 执行示例请求
                result = client.example_request("http://integration.test", {"test": True})

                # 验证结果
                expected_result = {"status": "success", "data": {"result": "some data"}}
                self.assertEqual(result, expected_result)

                # 测试状态操作
                state_data = {"integration": "test_data"}
                saved = client.save_operation_state("integration_test", state_data)
                self.assertTrue(saved)

                loaded = client.load_operation_state("integration_test")
                # 注意：由于使用了模拟，loaded可能为None或模拟值

    def test_stateful_client_workflow(self):
        """测试有状态客户端工作流"""
        with (
            patch("src.core.network.client.StateManager") as mock_state_manager,
            patch("src.core.network.client.RetryManager") as mock_retry_manager,
        ):

            # 设置模拟
            mock_state_instance = Mock()
            mock_state_manager.return_value = mock_state_instance

            mock_retry_instance = Mock()
            mock_retry_instance.execute_with_retry.return_value = "workflow_result"
            mock_retry_manager.return_value = mock_retry_instance

            # 创建有状态客户端
            client = StatefulNetworkClient()

            # 执行多个操作
            test_func = Mock()

            result1 = client.stateful_request(test_func, "op1")
            result2 = client.stateful_request(test_func, "op2")

            # 验证结果
            self.assertEqual(result1, "workflow_result")
            self.assertEqual(result2, "workflow_result")

            # 验证操作ID递增
            calls = mock_state_instance.save_operation_state.call_args_list

            # 应该有4次调用（每个操作2次：开始和完成）
            self.assertEqual(len(calls), 4)

            # 验证操作ID
            self.assertEqual(calls[0][0][0], "operation_1")  # 第一个操作开始
            self.assertEqual(calls[1][0][0], "operation_1")  # 第一个操作完成
            self.assertEqual(calls[2][0][0], "operation_2")  # 第二个操作开始
            self.assertEqual(calls[3][0][0], "operation_2")  # 第二个操作完成


class TestErrorHandling(unittest.TestCase):
    """测试错误处理"""

    def test_network_client_state_manager_error(self):
        """测试网络客户端状态管理器错误"""
        with patch("src.core.network.client.StateManager") as mock_state_manager:
            mock_state_manager.side_effect = Exception("StateManager init error")

            with self.assertRaises(Exception) as context:
                NetworkClient()

            self.assertEqual(str(context.exception), "StateManager init error")

    def test_network_client_retry_manager_error(self):
        """测试网络客户端重试管理器错误"""
        with (
            patch("src.core.network.client.StateManager"),
            patch("src.core.network.client.RetryManager") as mock_retry_manager,
        ):

            mock_retry_manager.side_effect = Exception("RetryManager init error")

            with self.assertRaises(Exception) as context:
                NetworkClient()

            self.assertEqual(str(context.exception), "RetryManager init error")

    def test_stateful_request_state_save_error(self):
        """测试有状态请求状态保存错误"""
        with (
            patch("src.core.network.client.StateManager") as mock_state_manager,
            patch("src.core.network.client.RetryManager") as mock_retry_manager,
        ):

            # 设置状态保存失败
            mock_state_instance = Mock()
            mock_state_instance.save_operation_state.side_effect = Exception("Save error")
            mock_state_manager.return_value = mock_state_instance

            mock_retry_instance = Mock()
            mock_retry_manager.return_value = mock_retry_instance

            client = StatefulNetworkClient()
            test_func = Mock()

            # 状态保存错误应该传播
            with self.assertRaises(Exception) as context:
                client.stateful_request(test_func)

            self.assertEqual(str(context.exception), "Save error")


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def test_empty_state_data(self):
        """测试空状态数据"""
        with (
            patch("src.core.network.client.StateManager") as mock_state_manager,
            patch("src.core.network.client.RetryManager"),
        ):

            mock_state_instance = Mock()
            mock_state_manager.return_value = mock_state_instance

            client = NetworkClient()

            # 测试空字典
            client.save_operation_state("empty", {})
            mock_state_instance.save_operation_state.assert_called_with("empty", {})

    def test_none_parameters(self):
        """测试None参数"""
        with (
            patch("src.core.network.client.StateManager") as mock_state_manager,
            patch("src.core.network.client.RetryManager") as mock_retry_manager,
        ):

            mock_state_instance = Mock()
            mock_state_manager.return_value = mock_state_instance

            mock_retry_instance = Mock()
            mock_retry_instance.execute_with_retry.return_value = None
            mock_retry_manager.return_value = mock_retry_instance

            client = StatefulNetworkClient()
            test_func = Mock()

            # 测试None结果
            result = client.stateful_request(test_func)
            self.assertIsNone(result)

    def test_large_operation_counter(self):
        """测试大操作计数器"""
        with (
            patch("src.core.network.client.StateManager"),
            patch("src.core.network.client.RetryManager"),
        ):

            client = StatefulNetworkClient()

            # 设置大计数器值
            client._operation_counter = 999999

            operation_id = client._get_next_operation_id()
            self.assertEqual(operation_id, "operation_1000000")
            self.assertEqual(client._operation_counter, 1000000)


if __name__ == "__main__":
    unittest.main()
