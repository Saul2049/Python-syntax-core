"""
核心网络模块测试 (Core Network Module Tests)

提供网络相关功能的全面测试覆盖
"""

import time
import unittest.mock as mock
from unittest.mock import patch

import pytest
import requests

from src.core.network.decorators import RetryExecutor, with_retry
from src.core.network.retry_manager import RetryManager, SimpleRetryExecutor, create_retry_decorator
from src.core.network.client import NetworkClient
from src.core.network.state_manager import StateManager


class TestRetryDecorator:
    """测试重试装饰器功能"""

    def test_with_retry_decorator_success(self):
        """测试with_retry装饰器成功场景"""
        @with_retry(retry_config={"max_retries": 2}, retry_on_exceptions=[Exception])
        def test_function(x, y):
            return x + y

        result = test_function(1, 2)
        assert result == 3

    def test_with_retry_decorator_with_retries(self):
        """测试with_retry装饰器重试场景"""
        call_count = {"count": 0}
        
        @with_retry(retry_config={"max_retries": 2}, retry_on_exceptions=[ValueError])
        def test_function():
            call_count["count"] += 1
            if call_count["count"] < 3:
                raise ValueError("not ready")
            return "success"

        result = test_function()
        assert result == "success"
        assert call_count["count"] == 3

    def test_with_retry_decorator_default_config(self):
        """测试with_retry装饰器默认配置"""
        @with_retry()
        def test_function(value):
            return value * 2

        result = test_function(5)
        assert result == 10


class TestRetryManager:
    """测试重试管理器功能"""

    def test_simple_retry_executor_success(self):
        """测试简单重试执行器成功场景"""
        func = mock.Mock(return_value="success")
        retry_config = {"max_retries": 3}
        executor = SimpleRetryExecutor(
            func=func,
            retry_config=retry_config,
            retry_on_exceptions=[Exception],
            logger=mock.Mock()
        )
        
        result = executor.execute("test_arg")
        
        assert result == "success"
        func.assert_called_once_with("test_arg")

    def test_simple_retry_executor_with_retries(self):
        """测试简单重试执行器重试场景"""
        func = mock.Mock(side_effect=[ConnectionError("fail"), "success"])
        retry_config = {"max_retries": 2}
        executor = SimpleRetryExecutor(
            func=func,
            retry_config=retry_config,
            retry_on_exceptions=[ConnectionError],
            logger=mock.Mock()
        )
        
        result = executor.execute()
        
        assert result == "success"
        assert func.call_count == 2

    def test_create_retry_decorator_basic(self):
        """测试创建重试装饰器基本功能"""
        decorator = create_retry_decorator(
            retry_config={"max_retries": 2, "base_delay": 0.01}
        )
        
        @decorator
        def test_func(value):
            return value * 2

        result = test_func(5)
        assert result == 10

    def test_retry_manager_initialization(self):
        """测试重试管理器初始化"""
        config = {"max_retries": 5, "base_delay": 0.1, "max_delay": 10.0}
        manager = RetryManager(default_config=config)
        
        assert manager.default_config["max_retries"] == 5
        assert manager.default_config["base_delay"] == 0.1
        assert manager.default_config["max_delay"] == 10.0

    @patch('time.sleep')
    def test_retry_manager_execute_with_retries(self, mock_sleep):
        """测试重试管理器执行重试逻辑"""
        config = {"max_retries": 2, "base_delay": 0.1}
        manager = RetryManager(default_config=config)
        func = mock.Mock(side_effect=[Exception("fail"), Exception("fail"), "success"])
        
        result = manager.execute_with_retry(
            func, "test_arg", 
            retry_on_exceptions=[Exception]
        )
        
        assert result == "success"
        assert func.call_count == 3
        assert mock_sleep.call_count == 2  # 两次重试，两次睡眠


class TestNetworkClient:
    """测试网络客户端功能"""

    def test_network_client_initialization(self):
        """测试网络客户端初始化"""
        client = NetworkClient()
        
        assert client.state_manager is not None
        assert client.retry_manager is not None

    def test_network_client_with_custom_config(self):
        """测试网络客户端自定义配置"""
        retry_config = {"max_retries": 3, "base_delay": 0.5}
        client = NetworkClient(retry_config=retry_config)
        
        assert client.retry_manager.default_config["max_retries"] == 3
        assert client.retry_manager.default_config["base_delay"] == 0.5

    def test_network_client_example_request(self):
        """测试网络客户端示例请求"""
        client = NetworkClient()
        
        with patch.object(client, 'execute_with_retry') as mock_execute:
            mock_execute.return_value = {"status": "success"}
            
            result = client.example_request("https://api.test.com", {"param": "value"})
            
            assert result == {"status": "success"}
            mock_execute.assert_called_once()


class TestStateManager:
    """测试状态管理器功能"""

    def test_state_manager_initialization(self):
        """测试状态管理器初始化"""
        manager = StateManager()
        
        assert manager.state_dir is not None
        assert manager.state_dir.exists()

    def test_state_manager_save_load_state(self):
        """测试状态管理器保存和加载状态"""
        manager = StateManager()
        
        # 测试数据
        test_data = {
            "operation": "test",
            "status": "completed",
            "value": 123
        }
        
        # 保存状态
        success = manager.save_operation_state("test_operation", test_data)
        assert success is True
        
        # 加载状态
        loaded_data = manager.load_operation_state("test_operation")
        assert loaded_data["operation"] == "test"
        assert loaded_data["status"] == "completed"
        assert loaded_data["value"] == 123
        assert "last_updated" in loaded_data

    def test_state_manager_clear_state(self):
        """测试状态管理器清除状态"""
        manager = StateManager()
        
        # 先保存一个状态
        test_data = {"test": "data"}
        manager.save_operation_state("clear_test", test_data)
        
        # 验证状态存在
        loaded_data = manager.load_operation_state("clear_test")
        assert loaded_data["test"] == "data"
        
        # 清除状态
        success = manager.clear_operation_state("clear_test")
        assert success is True
        
        # 验证状态已被清除
        loaded_data = manager.load_operation_state("clear_test")
        assert loaded_data == {}

    def test_state_manager_list_operations(self):
        """测试状态管理器列出操作"""
        manager = StateManager()
        
        # 创建几个测试状态
        operations = ["op1", "op2", "op3"]
        for op in operations:
            manager.save_operation_state(op, {"test": f"data_{op}"})
        
        # 获取操作列表
        listed_operations = manager.list_operations()
        
        # 验证所有操作都在列表中
        for op in operations:
            assert op in listed_operations


# 集成测试
class TestNetworkIntegration:
    """网络模块集成测试"""

    def test_client_with_retry_integration(self):
        """测试客户端与重试机制的集成"""
        retry_config = {"max_retries": 3, "base_delay": 0.01}
        client = NetworkClient(retry_config=retry_config)
        
        call_count = {"count": 0}
        
        def mock_request():
            call_count["count"] += 1
            if call_count["count"] <= 2:
                raise requests.ConnectionError("connection failed")
            return {"result": "success"}
        
        result = client.execute_with_retry(mock_request)
        assert result == {"result": "success"}
        assert call_count["count"] == 3

    def test_decorator_and_manager_integration(self):
        """测试装饰器和管理器的集成使用"""
        config = {"max_retries": 2, "base_delay": 0.01}
        manager = RetryManager(default_config=config)
        
        call_count = {"count": 0}
        
        def network_operation():
            call_count["count"] += 1
            if call_count["count"] < 2:
                raise requests.RequestException("network error")
            return "completed"
        
        result = manager.execute_with_retry(network_operation)
        assert result == "completed"
        assert call_count["count"] == 2

    def test_state_manager_with_client_integration(self):
        """测试状态管理器与客户端的集成"""
        state_manager = StateManager()
        
        # 模拟网络操作状态管理
        operation_state = {
            "url": "https://api.example.com/data",
            "last_request": "2023-01-01T10:00:00",
            "retry_count": 0,
            "status": "pending"
        }
        
        # 保存操作状态
        state_manager.save_operation_state("api_request", operation_state)
        
        # 模拟操作失败，更新重试次数
        loaded_state = state_manager.load_operation_state("api_request")
        loaded_state["retry_count"] += 1
        loaded_state["status"] = "retrying"
        
        # 保存更新后的状态
        state_manager.save_operation_state("api_request", loaded_state)
        
        # 验证状态更新
        final_state = state_manager.load_operation_state("api_request")
        assert final_state["retry_count"] == 1
        assert final_state["status"] == "retrying" 