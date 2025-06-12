#!/usr/bin/env python3
"""并行测试运行器 - 使用pytest-xdist提升测试性能"""

import glob
import multiprocessing
import signal
import subprocess
import time


class TimeoutError(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutError("超时!")


def get_test_files():
    """动态获取所有测试文件，排除问题文件"""
    files = glob.glob("tests/test_*.py")
    exclude_files = ["tests/test_trading_loop_coverage_BROKEN.py"]
    files = [f for f in files if f not in exclude_files]
    return sorted(files)


def install_parallel_dependencies():
    """安装并行测试所需依赖"""
    print("🔧 检查并安装并行测试依赖...")

    dependencies = ["pytest-xdist", "pytest-forked"]

    for dep in dependencies:
        try:
            result = subprocess.run(["pip", "show", dep], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {dep} 已安装")
            else:
                print(f"📥 安装 {dep}...")
                install_result = subprocess.run(
                    ["pip", "install", dep], capture_output=True, text=True
                )
                if install_result.returncode == 0:
                    print(f"✅ {dep} 安装成功")
                else:
                    print(f"❌ {dep} 安装失败: {install_result.stderr}")
                    return False
        except Exception as e:
            print(f"❌ 检查 {dep} 时出错: {e}")
            return False

    return True


def run_parallel_test(test_strategy, timeout_seconds=300):
    """运行并行测试"""

    cpu_count = multiprocessing.cpu_count()
    strategies = {
        "auto": "-nauto",  # 自动选择工作进程数
        "cpu": f"-n{cpu_count}",  # 使用CPU核心数
        "half_cpu": f"-n{cpu_count//2}",  # 使用一半CPU核心
        "conservative": f"-n{min(4, cpu_count)}",  # 保守策略，最多4个进程
        "serial": "",  # 串行运行作为对比
    }

    if test_strategy not in strategies:
        print(f"❌ 未知策略: {test_strategy}")
        return False, 0

    parallel_arg = strategies[test_strategy]

    print(f"\n🎯 运行{test_strategy}并行测试")
    print(f"🖥️ CPU核心数: {cpu_count}")
    print(f"⚙️ 并行参数: {parallel_arg if parallel_arg else '串行'}")
    print(f"⏰ 超时设置: {timeout_seconds}秒")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)

    try:
        start_time = time.time()

        cmd = ["pytest", "tests/"]
        if parallel_arg:
            cmd.append(parallel_arg)

        # 添加其他优化参数
        cmd.extend(
            [
                "--tb=no",  # 简化错误输出
                "-q",  # 安静模式
                "--durations=10",  # 显示最慢的10个测试
                "--maxfail=5",  # 最多5个失败后停止
            ]
        )

        # 如果是覆盖率测试
        if test_strategy != "serial":
            cmd.extend(["--cov=src", "--cov-report=term"])

        print(f"🚀 执行命令: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)
        end_time = time.time()
        signal.alarm(0)

        duration = end_time - start_time
        print(f"✅ {test_strategy}测试完成! 耗时: {duration:.2f}秒")
        print(f"📊 返回码: {result.returncode}")

        # 显示测试统计
        if result.stdout:
            lines = result.stdout.split("\n")
            for line in lines[-15:]:
                if ("passed" in line and "failed" in line) or "TOTAL" in line:
                    print(f"📋 {line.strip()}")

        # 显示最慢的测试
        if "--durations=10" in cmd and result.stdout:
            lines = result.stdout.split("\n")
            duration_started = False
            print("\n⏱️ 最慢的测试:")
            for line in lines:
                if "slowest durations" in line.lower():
                    duration_started = True
                    continue
                if duration_started and line.strip():
                    if line.startswith("="):
                        break
                    print(f"   {line.strip()}")

        return True, duration

    except TimeoutError:
        signal.alarm(0)
        print(f"⏰ {test_strategy}测试超时!")
        return False, timeout_seconds
    except Exception as e:
        signal.alarm(0)
        print(f"❌ {test_strategy}测试异常: {e}")
        return False, 0


def benchmark_parallel_strategies():
    """基准测试不同并行策略"""
    print("🏁 并行策略基准测试")

    strategies = ["serial", "conservative", "half_cpu", "auto"]
    results = {}

    for strategy in strategies:
        print(f"\n{'='*60}")
        success, duration = run_parallel_test(strategy, timeout_seconds=240)
        results[strategy] = {"success": success, "duration": duration}

        if not success and strategy == "serial":
            print("❌ 串行测试失败，停止基准测试")
            break

    # 分析结果
    print(f"\n{'='*60}")
    print("📊 并行策略性能对比:")

    if results.get("serial", {}).get("success"):
        serial_time = results["serial"]["duration"]
        print(f"📈 基准(串行): {serial_time:.2f}秒")

        for strategy, data in results.items():
            if strategy != "serial" and data["success"]:
                speedup = serial_time / data["duration"]
                print(f"🚀 {strategy}: {data['duration']:.2f}秒 (加速: {speedup:.1f}x)")

        # 推荐最佳策略
        successful_results = {k: v for k, v in results.items() if v["success"] and k != "serial"}
        if successful_results:
            best_strategy = min(
                successful_results.keys(), key=lambda k: successful_results[k]["duration"]
            )
            best_time = successful_results[best_strategy]["duration"]
            best_speedup = serial_time / best_time
            print(f"\n🎯 推荐策略: {best_strategy}")
            print(f"   耗时: {best_time:.2f}秒")
            print(f"   加速比: {best_speedup:.1f}x")
    else:
        print("❌ 串行测试失败，无法进行对比")

    return results


def create_pytest_config():
    """创建优化的pytest配置文件"""
    config_content = """# pytest.ini - 优化的pytest配置
[tool:pytest]
# 基本设置
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# 性能优化
addopts =
    --tb=short
    --strict-markers
    --disable-warnings
    --maxfail=10
    --durations=10

# 并行测试设置 (取消注释以启用)
# addopts =
#     -nauto
#     --dist=worksteal
#     --tb=short
#     --maxfail=5

# 覆盖率设置
# addopts =
#     --cov=src
#     --cov-report=term-missing
#     --cov-report=html
#     --cov-fail-under=70

# 标记定义
markers =
    slow: 标记运行缓慢的测试
    integration: 标记集成测试
    unit: 标记单元测试
    network: 标记需要网络的测试
"""

    with open("pytest.ini", "w", encoding="utf-8") as f:
        f.write(config_content)

    print("📝 已创建优化的pytest.ini配置文件")


def main():
    print("🚀 并行测试优化器")
    print("🎯 目标: 通过并行化提升全量测试性能")

    # 1. 安装依赖
    if not install_parallel_dependencies():
        print("❌ 依赖安装失败，退出")
        return

    # 2. 创建配置文件
    create_pytest_config()

    # 3. 运行基准测试
    print(f"\n{'='*60}")
    results = benchmark_parallel_strategies()

    # 4. 提供最终建议
    print(f"\n{'='*60}")
    print("💡 优化建议总结:")
    print("1. 🔧 使用推荐的并行策略运行测试")
    print("2. 📝 根据需要编辑pytest.ini配置文件")
    print("3. 🧹 考虑在测试间添加资源清理代码")
    print("4. 💾 监控内存使用，必要时减少并行度")

    # 输出快速命令
    successful_results = {k: v for k, v in results.items() if v["success"] and k != "serial"}
    if successful_results:
        best_strategy = min(
            successful_results.keys(), key=lambda k: successful_results[k]["duration"]
        )
        if best_strategy == "auto":
            print("\n🎯 快速命令: pytest tests/ -nauto --tb=short")
        elif best_strategy == "conservative":
            print("\n🎯 快速命令: pytest tests/ -n4 --tb=short")
        elif best_strategy == "half_cpu":
            cpu_count = multiprocessing.cpu_count()
            print(f"\n🎯 快速命令: pytest tests/ -n{cpu_count//2} --tb=short")


if __name__ == "__main__":
    main()
