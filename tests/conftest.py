"""测试配置和清理设置"""

import asyncio
import gc
import logging
import os
import shutil
import tempfile
import threading
import time
import warnings
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# 全局测试计数器
test_counter = 0

# 测试环境变量
TEST_ENV_VARS = {
    "TG_TOKEN": "test_telegram_token_123456789",
    "TG_CHAT_ID": "test_chat_id_123456789",
    "TG_CHAT": "test_chat_id_123456789",
    "API_KEY": "test_api_key_123456789",
    "API_SECRET": "test_api_secret_123456789",
    "SYMBOLS": "BTCUSDT,ETHUSDT",
    "RISK_PERCENT": "0.01",
    "FAST_MA": "7",
    "SLOW_MA": "25",
    "TEST_MODE": "true",
    "ACCOUNT_EQUITY": "10000.0",
    "LOG_LEVEL": "INFO",
    "LOG_DIR": "test_logs",
    "TRADES_DIR": "test_trades",
    "USE_BINANCE_TESTNET": "true",
    "MONITORING_PORT": "9091",
}

from src.monitoring.metrics_collector import MetricsCollector

# 监控相关依赖
from src.monitoring.prometheus_exporter import PrometheusExporter

# ---------------------------------------------------------------------------
# 常用 Prometheus / Collector fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def registry():
    """返回独立的 CollectorRegistry，避免跨测试冲突。"""
    from prometheus_client import CollectorRegistry

    return CollectorRegistry()


@pytest.fixture
def mock_exporter(registry):
    exporter = PrometheusExporter(registry=registry)

    # 为常用指标创建 mock，避免真实 Prometheus 行为
    for name in (
        "trade_count",
        "error_count",
        "price",
        "data_source_status",
        "portfolio_value",
        "strategy_returns",
        "memory_usage",
    ):
        metric = Mock()
        metric.labels.return_value = Mock()
        setattr(exporter, name, metric)

    # 桩掉 start/stop
    exporter.start = Mock()
    exporter.stop = Mock()
    return exporter


@pytest.fixture
def fresh_collector(mock_exporter):
    return MetricsCollector(exporter=mock_exporter)


# Telegram fixtures -----------------------------------------------------------


@pytest.fixture
def token():
    return "TEST_TOKEN_1234567890"


@pytest.fixture
def chat_id():
    return "123456789"


# Broker / notifier -----------------------------------------------------------


@pytest.fixture
def mock_broker(monkeypatch):
    with patch("src.core.trading_engine.Broker") as broker_cls:
        broker = broker_cls.return_value
        broker.notifier = Mock()
        yield broker


@pytest.fixture(autouse=True, scope="session")
def setup_test_environment():
    """设置测试环境变量"""
    original_env = {}

    # 保存原始环境变量
    for key in TEST_ENV_VARS:
        if key in os.environ:
            original_env[key] = os.environ[key]

    # 设置测试环境变量
    for key, value in TEST_ENV_VARS.items():
        os.environ[key] = value

    yield

    # 恢复原始环境变量
    for key in TEST_ENV_VARS:
        if key in original_env:
            os.environ[key] = original_env[key]
        elif key in os.environ:
            del os.environ[key]


@pytest.fixture(autouse=True, scope="function")
def auto_cleanup():
    """每个测试后自动清理资源"""
    global test_counter
    test_counter += 1

    # 测试前的准备
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

    yield  # 运行测试

    # 测试后的清理
    try:
        # 1. 清理异步循环
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果循环正在运行，清理待处理的任务
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    if not task.done():
                        task.cancel()
                        try:
                            loop.run_until_complete(task)
                        except asyncio.CancelledError:
                            pass
        except RuntimeError:
            # 没有事件循环，跳过
            pass

        # 2. 清理线程
        active_threads = threading.active_count()
        if active_threads > 1:
            # 等待一小段时间让线程自然结束
            time.sleep(0.1)

        # 3. 清理全局变量和模块状态
        # 重置logging配置
        logging.getLogger().handlers.clear()
        logging.getLogger().setLevel(logging.WARNING)

        # 4. 强制垃圾回收
        gc.collect()

        # 5. 每100个测试做一次深度清理
        if test_counter % 100 == 0:
            import sys

            # 清理导入的模块缓存
            modules_to_remove = []
            for name, module in sys.modules.items():
                if name.startswith("src.") or name.startswith("tests."):
                    modules_to_remove.append(name)

            for name in modules_to_remove[:10]:  # 只清理前10个，避免过度清理
                try:
                    del sys.modules[name]
                except KeyError:
                    pass

            # 强制垃圾回收
            for _ in range(3):
                gc.collect()

    except Exception:
        # 清理过程中的错误不应该影响测试结果
        pass


@pytest.fixture(autouse=True, scope="session")
def session_cleanup():
    """会话级别的清理（增强版 - 包含tempfile清理）"""
    yield

    # 会话结束时的清理
    try:
        # 清理所有线程
        import threading

        threads = [t for t in threading.enumerate() if t != threading.current_thread()]
        for thread in threads:
            if hasattr(thread, "stop"):
                thread.stop()

        # 🧹 清理遗留的临时文件
        temp_dir = tempfile.gettempdir()
        try:
            for item in Path(temp_dir).glob("tmp*"):
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                except:
                    pass
        except:
            pass

        # 最终垃圾回收
        for _ in range(5):
            gc.collect()

    except Exception:
        pass


@pytest.fixture
def memory_monitor():
    """内存监控fixture"""
    import os

    import psutil

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    yield

    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory

    # 如果内存增长超过50MB，发出警告
    if memory_increase > 50:
        print(f"⚠️ 测试内存增长: {memory_increase:.1f}MB")


# 🧹 Tempfile清理功能
@pytest.fixture
def temp_directory():
    """提供一个自动清理的临时目录"""
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    finally:
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass


@pytest.fixture
def temp_file():
    """提供一个自动清理的临时文件"""
    fd, temp_path = tempfile.mkstemp()
    os.close(fd)  # 关闭文件描述符
    try:
        yield temp_path
    finally:
        try:
            os.unlink(temp_path)
        except:
            pass


class TempFileManager:
    """临时文件管理器"""

    def __init__(self):
        self.temp_files = []
        self.temp_dirs = []

    def create_temp_file(self, suffix="", prefix="tmp", dir=None):
        """创建临时文件"""
        fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir)
        os.close(fd)
        self.temp_files.append(path)
        return path

    def create_temp_dir(self, suffix="", prefix="tmp", dir=None):
        """创建临时目录"""
        path = tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=dir)
        self.temp_dirs.append(path)
        return path

    def cleanup(self):
        """清理所有临时文件和目录"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except:
                pass

        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass

        self.temp_files.clear()
        self.temp_dirs.clear()


@pytest.fixture
def temp_manager():
    """提供临时文件管理器"""
    manager = TempFileManager()
    try:
        yield manager
    finally:
        manager.cleanup()


# 配置pytest插件
def pytest_configure(config):
    """pytest配置"""
    # 禁用一些可能影响性能的警告
    import warnings

    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
    warnings.filterwarnings("ignore", category=ResourceWarning)

    # 设置更严格的超时
    config.addinivalue_line("markers", "timeout: 标记有超时限制的测试")


def pytest_runtest_setup(item):
    """测试设置钩子"""
    # 在每个测试前清理一次
    gc.collect()


def pytest_runtest_teardown(item, nextitem):
    """测试清理钩子"""
    # 在每个测试后清理
    gc.collect()

    # 如果下一个测试是None（最后一个测试），做深度清理
    if nextitem is None:
        for _ in range(3):
            gc.collect()
