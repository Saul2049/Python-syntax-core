#!/usr/bin/env python3
"""渐进式测试查找器 - 找出导致卡死的临界文件数量"""

import glob
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


def test_progressive_batches(all_files, timeout_seconds=300):
    """渐进式测试，逐步增加文件数量"""

    # 测试不同大小的批次
    batch_sizes = [30, 40, 50, 60]  # 从30个文件开始，逐步增加

    for batch_size in batch_sizes:
        if batch_size > len(all_files):
            batch_size = len(all_files)

        files_subset = all_files[:batch_size]

        print(f"\n{'='*60}")
        print(f"🎯 测试 {batch_size} 个文件")
        print(f"⏰ 超时设置: {timeout_seconds}秒")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)

        try:
            start_time = time.time()
            cmd = ["pytest"] + files_subset + ["--cov=src", "--cov-report=term", "--tb=no", "-q"]

            result = subprocess.run(cmd, capture_output=True, text=True)
            end_time = time.time()
            signal.alarm(0)

            print(f"✅ {batch_size}个文件测试完成! 耗时: {end_time - start_time:.2f}秒")
            print(f"📊 返回码: {result.returncode}")

            # 显示测试统计
            if result.stdout:
                lines = result.stdout.split("\n")
                for line in lines[-10:]:
                    if "====" in line and ("passed" in line or "failed" in line or "TOTAL" in line):
                        print(f"📋 结果: {line.strip()}")

        except TimeoutError:
            signal.alarm(0)
            print(f"⏰ {batch_size}个文件测试超时!")
            print(
                f"🚨 临界点找到: 介于{batch_sizes[batch_sizes.index(batch_size)-1] if batch_sizes.index(batch_size) > 0 else 0}和{batch_size}个文件之间"
            )
            return batch_size
        except Exception as e:
            signal.alarm(0)
            print(f"❌ {batch_size}个文件测试异常: {e}")
            return batch_size

    print("\n🎉 所有批次大小都测试成功!")
    print(f"💭 问题可能需要全部{len(all_files)}个文件才会出现")
    return None


def main():
    all_files = get_test_files()

    print("🔍 渐进式测试查找器")
    print(f"📂 总文件数: {len(all_files)}")
    print("🎯 目标: 找出导致卡死的临界文件数量")

    problem_size = test_progressive_batches(all_files)

    if problem_size:
        print("\n📋 问题定位:")
        print(f"🚨 在{problem_size}个文件时开始出现问题")
        print("💡 建议检查内存使用和资源管理")
    else:
        # 如果前面都成功，测试全部文件
        print(f"\n🔍 最终测试: 全部{len(all_files)}个文件")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(600)  # 10分钟超时

        try:
            start_time = time.time()
            cmd = ["pytest", "tests/", "--cov=src", "--cov-report=term", "--tb=no", "-q"]

            result = subprocess.run(cmd, capture_output=True, text=True)
            end_time = time.time()
            signal.alarm(0)

            print(f"✅ 全部文件测试完成! 耗时: {end_time - start_time:.2f}秒")
            print("📊 这很奇怪 - 看起来问题已经解决了")

        except TimeoutError:
            signal.alarm(0)
            print("⏰ 全部文件测试确实超时!")
            print("🤔 问题确实存在于全量测试中")


if __name__ == "__main__":
    main()
