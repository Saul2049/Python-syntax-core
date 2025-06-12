"""测试配置和清理设置"""

import asyncio
import gc
import logging
import os
import shutil
import tempfile
import threading
import warnings
from pathlib import Path

import pytest

# 全局测试计数器
test_counter = 0


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
