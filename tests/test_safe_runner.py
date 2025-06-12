"""
安全测试运行器 (Safe Test Runner)
避免测试卡死的实用工具

主要解决问题：
1. 网络请求超时
2. 异步任务死锁
3. 无限循环
4. 资源锁定
"""

import asyncio
import signal
import time
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest


class TestTimeoutError(Exception):
    """测试超时异常"""

    pass


def timeout_handler(signum, frame):
    """超时信号处理器"""
    raise TestTimeoutError("Test execution timed out")


@contextmanager
def test_timeout(seconds=10):
    """为测试设置超时限制"""
    # 设置信号处理器
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        # 清理
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


@contextmanager
def mock_all_sleeps():
    """Mock所有可能的睡眠调用"""
    with patch("time.sleep") as mock_time_sleep, patch("asyncio.sleep") as mock_async_sleep:

        # time.sleep直接返回
        mock_time_sleep.return_value = None

        # asyncio.sleep返回已完成的future
        async def instant_sleep(seconds):
            return None

        mock_async_sleep.side_effect = instant_sleep

        yield {"time_sleep": mock_time_sleep, "async_sleep": mock_async_sleep}


@contextmanager
def mock_all_network():
    """Mock所有网络调用"""
    with (
        patch("requests.get") as mock_get,
        patch("requests.post") as mock_post,
        patch("aiohttp.ClientSession") as mock_session,
    ):

        # 配置默认响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.text = '{"success": true}'

        mock_get.return_value = mock_response
        mock_post.return_value = mock_response

        # Mock aiohttp session
        mock_session_instance = MagicMock()
        mock_session.return_value.__aenter__.return_value = mock_session_instance

        yield {"get": mock_get, "post": mock_post, "session": mock_session}


def run_safe_test(test_function, timeout_seconds=5):
    """安全运行单个测试"""
    try:
        with test_timeout(timeout_seconds):
            with mock_all_sleeps():
                with mock_all_network():
                    if asyncio.iscoroutinefunction(test_function):
                        asyncio.run(test_function())
                    else:
                        test_function()
        return True, None
    except TestTimeoutError:
        return False, "Test timed out"
    except Exception as e:
        return False, str(e)


class TestSafeRunner:
    """测试安全运行器的功能"""

    def test_timeout_protection(self):
        """测试超时保护功能"""

        def slow_test():
            time.sleep(0.1)  # 会被mock掉
            return "completed"

        success, error = run_safe_test(slow_test, timeout_seconds=1)
        assert success is True
        assert error is None

    def test_sleep_mocking(self):
        """测试睡眠Mock功能"""

        def sleep_test():
            import time

            start = time.time()
            time.sleep(5)  # 应该被mock掉
            end = time.time()
            # 由于被mock，时间差应该很小
            assert end - start < 1

        success, error = run_safe_test(sleep_test)
        assert success is True

    @pytest.mark.asyncio
    async def test_async_sleep_mocking(self):
        """测试异步睡眠Mock功能"""

        async def async_sleep_test():
            start = time.time()
            await asyncio.sleep(5)  # 应该被mock掉
            end = time.time()
            # 由于被mock，时间差应该很小
            assert end - start < 1

        success, error = run_safe_test(async_sleep_test)
        assert success is True

    def test_network_mocking(self):
        """测试网络请求Mock功能"""

        def network_test():
            import requests

            response = requests.get("https://api.example.com/data")
            assert response.status_code == 200
            assert response.json()["success"] is True

        success, error = run_safe_test(network_test)
        assert success is True


if __name__ == "__main__":
    # 运行安全测试
    pytest.main([__file__, "-v"])
