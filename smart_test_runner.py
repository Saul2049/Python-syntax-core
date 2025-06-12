#!/usr/bin/env python3
"""
🧠 智能测试运行器 (Smart Test Runner)

提供分层测试策略，根据不同场景优化执行
"""

import argparse
import subprocess
import sys


class SmartTestRunner:
    def __init__(self):
        self.base_cmd = "python -m pytest"

    def run_smoke_tests(self):
        """🔥 冒烟测试 - 核心功能验证 (最快)"""
        print("🔥 运行冒烟测试...")

        # 只测试最关键的模块
        critical_tests = [
            "tests/test_data_processors.py::TestDataProcessorFunctions::test_load_data_success",
            "tests/test_broker_enhanced_coverage.py::TestBrokerInternalMethods::test_execute_order_internal",
            "tests/test_config.py::TestConfigCreation::test_create_default_config",
            "tests/test_backtest.py::TestRunBacktest::test_run_backtest_basic",
        ]

        cmd = f"{self.base_cmd} {' '.join(critical_tests)} -v"
        return self._run_with_timing(cmd, "冒烟测试")

    def run_fast_tests(self):
        """⚡ 快速测试 - 核心模块 (1-2分钟)"""
        print("⚡ 运行快速测试...")

        fast_modules = [
            "tests/test_data_processors.py",
            "tests/test_broker_enhanced_coverage.py",
            "tests/test_config.py",
            "tests/test_backtest.py",
            "tests/test_broker.py",
        ]

        cmd = f"{self.base_cmd} {' '.join(fast_modules)} -n auto --tb=short -q"
        return self._run_with_timing(cmd, "快速测试")

    def run_parallel_all(self):
        """🚀 并行全量测试 - 所有测试并行执行"""
        print("🚀 运行并行全量测试...")

        cmd = f"{self.base_cmd} tests/ -n auto --tb=short -q --maxfail=10"
        return self._run_with_timing(cmd, "并行全量测试")

    def run_performance_optimized(self):
        """🎯 性能优化测试 - 最优化配置"""
        print("🎯 运行性能优化测试...")

        # 最优化的参数组合
        cmd = f"{self.base_cmd} tests/ -n auto --tb=line -q --disable-warnings --maxfail=5 --durations=5"
        return self._run_with_timing(cmd, "性能优化测试")

    def run_failing_tests_only(self):
        """🔍 只运行失败的测试"""
        print("🔍 运行上次失败的测试...")

        cmd = f"{self.base_cmd} --lf -n auto --tb=short"
        return self._run_with_timing(cmd, "失败测试重跑")

    def run_modified_tests_only(self):
        """📝 只运行修改过的测试"""
        print("📝 运行修改过的测试...")

        # 基于git diff检测变更的文件
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1", "HEAD", "--", "tests/"],
                capture_output=True,
                text=True,
            )

            if result.stdout.strip():
                modified_files = result.stdout.strip().split("\n")
                modified_tests = [f for f in modified_files if f.endswith(".py")]

                if modified_tests:
                    cmd = f"{self.base_cmd} {' '.join(modified_tests)} -n auto -v"
                    return self._run_with_timing(cmd, "修改测试")
                else:
                    print("📝 没有检测到测试文件修改")
                    return False
            else:
                print("📝 没有检测到文件修改")
                return False
        except:
            print("📝 无法检测git变更，运行快速测试...")
            return self.run_fast_tests()

    def _run_with_timing(self, cmd, description):
        """执行命令并显示耗时"""
        import time

        print(f"📝 执行: {cmd}")
        start_time = time.time()

        result = subprocess.run(cmd, shell=True)

        end_time = time.time()
        duration = end_time - start_time

        if result.returncode == 0:
            print(f"✅ {description} 完成! 耗时: {duration:.1f}秒")
            return True
        else:
            print(f"❌ {description} 失败! 耗时: {duration:.1f}秒")
            return False


def main():
    parser = argparse.ArgumentParser(description="🧠 智能测试运行器")
    parser.add_argument(
        "strategy",
        choices=["smoke", "fast", "parallel", "optimized", "failed", "modified", "all"],
        help="测试策略",
    )

    args = parser.parse_args()

    runner = SmartTestRunner()

    strategies = {
        "smoke": ("🔥 冒烟测试 (10-30秒)", runner.run_smoke_tests),
        "fast": ("⚡ 快速测试 (1-2分钟)", runner.run_fast_tests),
        "parallel": ("🚀 并行全量测试 (2-3分钟)", runner.run_parallel_all),
        "optimized": ("🎯 性能优化测试 (最优配置)", runner.run_performance_optimized),
        "failed": ("🔍 失败测试重跑", runner.run_failing_tests_only),
        "modified": ("📝 修改测试检测", runner.run_modified_tests_only),
        "all": ("🌟 运行所有策略对比", lambda: run_all_strategies(runner)),
    }

    description, func = strategies[args.strategy]
    print(f"\n{description}")
    print("=" * 50)

    success = func()
    sys.exit(0 if success else 1)


def run_all_strategies(runner):
    """运行所有策略进行对比"""
    strategies = [
        ("冒烟测试", runner.run_smoke_tests),
        ("快速测试", runner.run_fast_tests),
        ("并行全量测试", runner.run_parallel_all),
    ]

    results = []
    for name, func in strategies:
        print(f"\n{'='*50}")
        success = func()
        results.append((name, success))

    print(f"\n{'='*50}")
    print("📊 策略对比结果:")
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")

    return all(success for _, success in results)


if __name__ == "__main__":
    main()
