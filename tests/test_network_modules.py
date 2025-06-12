#!/usr/bin/env python3
"""
网络模块测试 - 提高覆盖率
Network Modules Tests - Coverage Boost

重点关注:
- src/core/network/__init__.py (当前0%覆盖率)
- src/core/network/client.py (部分覆盖率)
- src/core/network/retry_manager.py (部分覆盖率)
- src/core/network/state_manager.py (部分覆盖率)
"""

import os
import tempfile
import time

import pytest


# 测试网络模块的导入
def test_network_init_imports():
    """测试网络模块初始化文件的导入功能"""
    # 测试所有主要导入是否正常工作
    try:
        from src.core.network import (  # 重试管理; 状态管理; 网络客户端; 高级装饰器
            DEFAULT_RETRY_CONFIG,
            NetworkClient,
            RetryManager,
            StatefulNetworkClient,
            StateManager,
            api_call,
            calculate_retry_delay,
            clear_state,
            create_retry_decorator,
            create_simple_client,
            create_stateful_client,
            critical_operation,
            get_global_state_manager,
            load_state,
            network_request,
            retry,
            save_state,
            set_global_state_dir,
            with_comprehensive_retry,
            with_retry,
            with_state_management,
        )

        # 验证所有导入都成功
        assert calculate_retry_delay is not None
        assert RetryManager is not None
        assert DEFAULT_RETRY_CONFIG is not None
        assert StateManager is not None
        assert NetworkClient is not None

    except ImportError as e:
        pytest.fail(f"导入失败: {e}")


class TestRetryManager:
    """测试重试管理器的基础功能"""

    def test_retry_manager_initialization(self):
        """测试重试管理器初始化"""
        from src.core.network.retry_manager import RetryManager

        # 使用默认配置初始化
        manager = RetryManager()
        assert manager is not None

        # 使用自定义配置初始化
        custom_config = {
            "max_retries": 5,
            "base_delay": 2.0,
            "max_delay": 60.0,
            "exponential_base": 2.0,
        }
        custom_manager = RetryManager(custom_config)
        assert custom_manager is not None

    def test_calculate_retry_delay(self):
        """测试重试延迟计算"""
        from src.core.network.retry_manager import calculate_retry_delay

        # 测试基本延迟计算
        delay = calculate_retry_delay(
            attempt=1, base_delay=1.0, exponential_base=2.0, max_delay=10.0
        )
        assert isinstance(delay, float)
        assert delay > 0
        assert delay <= 10.0  # 不应超过最大延迟

        # 测试不同尝试次数
        delay1 = calculate_retry_delay(1, base_delay=1.0)
        delay2 = calculate_retry_delay(2, base_delay=1.0)
        assert delay2 >= delay1  # 延迟应该递增

    def test_retry_decorator_basic(self):
        """测试基础重试装饰器"""
        from src.core.network.retry_manager import retry

        # 创建一个会失败几次然后成功的函数
        call_count = 0

        @retry(max_retries=3, base_delay=0.001)  # 很短的延迟用于测试
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("模拟错误")
            return "成功"

        # 测试重试功能
        result = flaky_function()
        assert result == "成功"
        assert call_count == 3  # 应该重试了2次


class TestStateManager:
    """测试状态管理器的基础功能"""

    def setup_method(self):
        """测试前设置"""
        # 创建临时目录用于状态文件
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """测试后清理"""
        # 清理临时目录
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_state_manager_initialization(self):
        """测试状态管理器初始化"""
        from src.core.network.state_manager import StateManager

        manager = StateManager(self.temp_dir)
        assert manager is not None
        assert manager.state_dir == self.temp_dir

    def test_save_and_load_state(self):
        """测试状态保存和加载"""
        from src.core.network.state_manager import load_state, save_state, set_global_state_dir

        # 设置全局状态目录
        set_global_state_dir(self.temp_dir)

        # 测试保存状态
        test_state = {"test_key": "test_value", "number": 42}
        save_state("test_component", test_state)

        # 测试加载状态
        loaded_state = load_state("test_component")
        assert loaded_state == test_state

    def test_clear_state(self):
        """测试清理状态"""
        from src.core.network.state_manager import (
            clear_state,
            load_state,
            save_state,
            set_global_state_dir,
        )

        set_global_state_dir(self.temp_dir)

        # 保存一些状态
        save_state("test_component", {"key": "value"})

        # 验证状态存在
        loaded = load_state("test_component")
        assert loaded is not None

        # 清理状态
        clear_state("test_component")

        # 验证状态被清理
        loaded_after_clear = load_state("test_component")
        assert loaded_after_clear == {}

    def test_global_state_manager(self):
        """测试全局状态管理器"""
        from src.core.network.state_manager import get_global_state_manager, set_global_state_dir

        set_global_state_dir(self.temp_dir)
        manager = get_global_state_manager()
        assert manager is not None


class TestNetworkClient:
    """测试网络客户端的基础功能"""

    def test_network_client_creation(self):
        """测试网络客户端创建"""
        from src.core.network.client import NetworkClient, create_simple_client

        # 测试基础客户端创建
        client = NetworkClient()
        assert client is not None

        # 测试简单客户端创建函数
        simple_client = create_simple_client()
        assert simple_client is not None

    def test_stateful_client_creation(self):
        """测试状态化客户端创建"""
        from src.core.network.client import StatefulNetworkClient, create_stateful_client

        # 测试状态化客户端创建
        stateful_client = StatefulNetworkClient(
            state_dir=self.temp_dir if hasattr(self, "temp_dir") else None
        )
        assert stateful_client is not None

        # 测试状态化客户端创建函数
        created_client = create_stateful_client()
        assert created_client is not None


class TestNetworkDecorators:
    """测试网络装饰器的基础功能"""

    def test_with_retry_decorator(self):
        """测试重试装饰器"""
        from src.core.network.decorators import with_retry

        call_count = 0

        @with_retry(max_retries=2, base_delay=0.001)
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("测试异常")
            return "成功"

        result = test_function()
        assert result == "成功"
        assert call_count == 2

    def test_network_request_decorator(self):
        """测试网络请求装饰器"""
        from src.core.network.decorators import network_request

        @network_request
        def mock_api_call():
            return {"status": "success", "data": "test"}

        result = mock_api_call()
        assert isinstance(result, dict)

    def test_api_call_decorator(self):
        """测试API调用装饰器"""
        from src.core.network.decorators import api_call

        @api_call
        def mock_api_function():
            return {"response": "ok"}

        result = mock_api_function()
        assert isinstance(result, dict)

    def test_critical_operation_decorator(self):
        """测试关键操作装饰器"""
        from src.core.network.decorators import critical_operation

        @critical_operation
        def critical_function():
            return "关键操作完成"

        result = critical_function()
        assert result == "关键操作完成"


class TestIntegrationScenarios:
    """测试集成场景"""

    def setup_method(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """测试后清理"""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_stateful_client_with_retry(self):
        """测试带重试的状态化客户端"""
        from src.core.network.client import StatefulNetworkClient
        from src.core.network.decorators import with_retry
        from src.core.network.state_manager import set_global_state_dir

        set_global_state_dir(self.temp_dir)

        client = StatefulNetworkClient(state_dir=self.temp_dir)

        # 为客户端添加重试装饰的方法
        @with_retry(max_retries=2, base_delay=0.001)
        def test_operation():
            return "操作成功"

        result = test_operation()
        assert result == "操作成功"

    def test_comprehensive_workflow(self):
        """测试综合工作流程"""
        from src.core.network import (
            NetworkClient,
            load_state,
            save_state,
            set_global_state_dir,
        )

        # 设置全局状态目录
        set_global_state_dir(self.temp_dir)

        # 创建客户端
        client = NetworkClient()

        # 保存一些状态
        test_state = {"client_id": "test", "last_request": time.time()}
        save_state("network_client", test_state)

        # 加载状态
        loaded_state = load_state("network_client")
        assert loaded_state["client_id"] == "test"

        # 验证集成正常工作
        assert client is not None
        assert loaded_state is not None


def test_module_constants():
    """测试模块常量"""
    from src.core.network.retry_manager import DEFAULT_RETRY_CONFIG

    # 验证默认重试配置存在且合理
    assert isinstance(DEFAULT_RETRY_CONFIG, dict)
    assert "max_retries" in DEFAULT_RETRY_CONFIG
    assert "base_delay" in DEFAULT_RETRY_CONFIG
    assert DEFAULT_RETRY_CONFIG["max_retries"] > 0
    assert DEFAULT_RETRY_CONFIG["base_delay"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
