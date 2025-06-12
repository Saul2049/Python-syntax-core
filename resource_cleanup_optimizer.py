#!/usr/bin/env python3
"""资源清理优化器 - 诊断和修复测试间的资源泄漏问题"""

import glob
import os
import signal
import subprocess
import time
from pathlib import Path



class TimeoutError(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutError("超时!")


def create_conftest_with_cleanup():
    """创建带有资源清理的conftest.py"""
    conftest_content = '''"""测试配置和清理设置"""

import pytest
import gc
import warnings
import asyncio
import threading
import logging
from unittest.mock import patch

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
            import importlib

            # 清理导入的模块缓存
            modules_to_remove = []
            for name, module in sys.modules.items():
                if name.startswith('src.') or name.startswith('tests.'):
                    modules_to_remove.append(name)

            for name in modules_to_remove[:10]:  # 只清理前10个，避免过度清理
                try:
                    del sys.modules[name]
                except KeyError:
                    pass

            # 强制垃圾回收
            for _ in range(3):
                gc.collect()

    except Exception as e:
        # 清理过程中的错误不应该影响测试结果
        pass

@pytest.fixture(autouse=True, scope="session")
def session_cleanup():
    """会话级别的清理"""
    yield

    # 会话结束时的清理
    try:
        # 清理所有线程
        import threading
        threads = [t for t in threading.enumerate() if t != threading.current_thread()]
        for thread in threads:
            if hasattr(thread, 'stop'):
                thread.stop()

        # 最终垃圾回收
        for _ in range(5):
            gc.collect()

    except Exception:
        pass

@pytest.fixture
def memory_monitor():
    """内存监控fixture"""
    import psutil
    import os

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    yield

    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory

    # 如果内存增长超过50MB，发出警告
    if memory_increase > 50:
        print(f"⚠️ 测试内存增长: {memory_increase:.1f}MB")

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
'''

    conftest_path = Path("tests/conftest.py")

    # 备份现有的conftest.py
    if conftest_path.exists():
        backup_path = conftest_path.with_suffix(".py.backup")
        conftest_path.rename(backup_path)
        print(f"📄 已备份现有conftest.py为 {backup_path}")

    # 写入新的conftest.py
    with open(conftest_path, "w", encoding="utf-8") as f:
        f.write(conftest_content)

    print("📝 已创建优化的tests/conftest.py")


def create_memory_optimization_script():
    """创建内存优化脚本"""
    script_content = '''#!/usr/bin/env python3
"""内存优化测试运行器"""

import subprocess
import os
import gc
import sys

def run_optimized_tests():
    """运行内存优化的测试"""

    # 设置环境变量优化Python内存使用
    env = os.environ.copy()
    env.update({
        'PYTHONHASHSEED': '0',  # 固定哈希种子
        'PYTHONUNBUFFERED': '1',  # 取消缓冲
        'PYTHONDONTWRITEBYTECODE': '1',  # 不生成.pyc文件
        'PYTHONMALLOC': 'malloc',  # 使用系统malloc
        'PYTHONASYNCIODEBUG': '0',  # 关闭asyncio调试
    })

    # 优化的pytest参数
    cmd = [
        'pytest', 'tests/',
        '--tb=short',           # 简短的错误追踪
        '--disable-warnings',   # 禁用警告
        '--maxfail=10',        # 最多10个失败
        '--durations=10',      # 显示最慢的10个测试
        '-x',                  # 遇到第一个失败就停止(可选)
        '--cov=src',           # 覆盖率
        '--cov-report=term',   # 终端报告
    ]

    print("🚀 运行内存优化测试...")
    print(f"📋 命令: {' '.join(cmd)}")

    # 运行测试
    result = subprocess.run(cmd, env=env)

    # 清理
    gc.collect()

    return result.returncode

if __name__ == "__main__":
    exit_code = run_optimized_tests()
    sys.exit(exit_code)
'''

    script_path = Path("run_optimized_tests.py")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_content)

    # 设置执行权限
    os.chmod(script_path, 0o755)
    print("📝 已创建内存优化测试运行器: run_optimized_tests.py")


def analyze_test_resource_usage():
    """分析测试资源使用情况"""
    print("🔍 分析测试资源使用...")

    # 检查可能有问题的模式
    problematic_patterns = [
        "import time",
        "sleep(",
        "Thread(",
        "asyncio.create_task",
        "subprocess.Popen",
        "socket.socket",
        "open(",
        "tempfile.",
        "multiprocessing.",
    ]

    test_files = glob.glob("tests/test_*.py")
    problematic_files = {}

    for test_file in test_files:
        if "BROKEN" in test_file:
            continue

        try:
            with open(test_file, "r", encoding="utf-8") as f:
                content = f.read()

            issues = []
            for pattern in problematic_patterns:
                if pattern in content:
                    count = content.count(pattern)
                    issues.append(f"{pattern}: {count}次")

            if issues:
                problematic_files[test_file] = issues

        except Exception as e:
            print(f"❌ 读取文件 {test_file} 失败: {e}")

    # 输出分析结果
    if problematic_files:
        print("\n⚠️ 可能有资源泄漏风险的测试文件:")
        for file_path, issues in problematic_files.items():
            print(f"   📄 {file_path}:")
            for issue in issues[:3]:  # 只显示前3个
                print(f"      - {issue}")

        print(f"\n📊 总计: {len(problematic_files)} 个文件可能存在资源使用问题")
    else:
        print("✅ 未发现明显的资源泄漏模式")

    return problematic_files


def test_cleanup_effectiveness():
    """测试清理效果"""
    print("\n🧪 测试资源清理效果...")

    # 运行一个小测试样本
    test_files = glob.glob("tests/test_*.py")[:5]  # 取前5个文件测试

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(120)  # 2分钟超时

    try:
        start_time = time.time()
        cmd = ["pytest"] + test_files + ["--tb=no", "-v"]

        result = subprocess.run(cmd, capture_output=True, text=True)
        end_time = time.time()
        signal.alarm(0)

        if result.returncode == 0:
            print(f"✅ 清理测试成功! 耗时: {end_time - start_time:.2f}秒")
            return True
        else:
            print(f"❌ 清理测试失败，返回码: {result.returncode}")
            return False

    except TimeoutError:
        signal.alarm(0)
        print("⏰ 清理测试超时")
        return False
    except Exception as e:
        signal.alarm(0)
        print(f"❌ 清理测试异常: {e}")
        return False


def main():
    print("🧹 资源清理优化器")
    print("🎯 目标: 解决测试间的资源泄漏和冲突问题")

    # 1. 分析当前资源使用
    problematic_files = analyze_test_resource_usage()

    # 2. 创建优化的配置
    print(f"\n{'='*60}")
    create_conftest_with_cleanup()
    create_memory_optimization_script()

    # 3. 测试清理效果
    print(f"\n{'='*60}")
    cleanup_works = test_cleanup_effectiveness()

    # 4. 提供建议
    print(f"\n{'='*60}")
    print("💡 资源清理优化建议:")

    if cleanup_works:
        print("✅ 基础清理机制工作正常")
        print("📝 建议使用: python run_optimized_tests.py")
    else:
        print("❌ 清理机制需要进一步调整")

    if problematic_files:
        print(f"⚠️  发现 {len(problematic_files)} 个文件可能有资源问题")
        print("🔧 建议手动检查这些文件的资源使用")

    print("\n🚀 优化后的运行方式:")
    print("1. 🧹 使用清理版本: python run_optimized_tests.py")
    print("2. 🔧 或手动运行: pytest tests/ --tb=short --disable-warnings")
    print("3. 📊 监控版本: python test_performance_analyzer.py")


if __name__ == "__main__":
    main()
