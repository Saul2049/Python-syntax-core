#!/usr/bin/env python3
"""覆盖率收集器 - 分批运行测试，汇总覆盖率报告"""

import glob
import os
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


def run_batch_with_coverage(files, batch_name, timeout_seconds=120):
    """运行一批测试并收集覆盖率"""
    print(f"\n🎯 运行批次: {batch_name}")
    print(f"📂 文件数量: {len(files)}")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)

    try:
        start_time = time.time()
        # 使用 --cov-append 来累积覆盖率数据
        cmd = (
            ["pytest"]
            + files
            + [
                "--cov=src",
                "--cov-append",  # 关键参数：累积覆盖率
                "--cov-report=",  # 不在每个批次生成报告
                "--tb=no",
                "-q",
            ]
        )

        result = subprocess.run(cmd, capture_output=True, text=True)
        end_time = time.time()
        signal.alarm(0)

        print(f"✅ 批次完成! 耗时: {end_time - start_time:.2f}秒")

        # 提取测试统计
        if result.stdout:
            lines = result.stdout.split("\n")
            for line in lines:
                if " passed" in line or " failed" in line:
                    print(f"📊 {line.strip()}")

        return True

    except TimeoutError:
        signal.alarm(0)
        print(f"⏰ 批次 {batch_name} 超时!")
        return False
    except Exception as e:
        signal.alarm(0)
        print(f"❌ 批次异常: {e}")
        return False


def generate_final_coverage_report():
    """生成最终的覆盖率报告"""
    print("\n📊 生成最终覆盖率报告...")

    # 生成终端报告
    cmd_term = ["coverage", "report", "--show-missing"]
    result_term = subprocess.run(cmd_term, capture_output=True, text=True)

    if result_term.returncode == 0:
        print("📋 终端覆盖率报告:")
        print(result_term.stdout)

    # 生成HTML报告
    cmd_html = ["coverage", "html"]
    result_html = subprocess.run(cmd_html, capture_output=True, text=True)

    if result_html.returncode == 0:
        print("📊 HTML报告已生成到 htmlcov/ 目录")

    return result_term.returncode == 0


def main():
    # 清理之前的覆盖率数据
    if os.path.exists(".coverage"):
        os.remove(".coverage")
        print("🧹 清理之前的覆盖率数据")

    all_files = get_test_files()

    print("🔍 分批覆盖率收集器")
    print(f"📂 总文件数: {len(all_files)}")
    print("🎯 策略: 分批运行，累积覆盖率")

    # 分成3批运行
    batch_size = 20
    total_passed = 0
    total_failed = 0

    for i in range(0, len(all_files), batch_size):
        batch_files = all_files[i : i + batch_size]
        batch_name = f"第{i//batch_size + 1}批"

        print(f"\n{'='*60}")
        success = run_batch_with_coverage(batch_files, batch_name)

        if not success:
            print(f"🚨 {batch_name} 失败，但继续后续批次...")
            continue

    print(f"\n{'='*60}")
    print("📊 所有批次完成，生成最终报告...")

    # 生成最终覆盖率报告
    if generate_final_coverage_report():
        print("\n🎉 覆盖率分析完成!")
        print("📋 查看详细报告:")
        print("   - 终端报告: 已显示在上方")
        print("   - HTML报告: 打开 htmlcov/index.html")
    else:
        print("\n❌ 生成覆盖率报告时出错")


if __name__ == "__main__":
    main()
