#!/usr/bin/env python3
"""分批测试定位器 - 找出导致卡死的文件组合"""

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
    # 排除已知问题文件
    exclude_files = ["tests/test_trading_loop_coverage_BROKEN.py"]
    files = [f for f in files if f not in exclude_files]
    return sorted(files)


def test_file_batch(files, batch_name, timeout_seconds=120):
    """测试一批文件"""
    print(f"\n🎯 测试批次: {batch_name}")
    print(f"📂 文件数量: {len(files)}")
    print(f"⏰ 超时设置: {timeout_seconds}秒")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)

    try:
        start_time = time.time()
        cmd = ["pytest"] + files + ["--cov=src", "--cov-report=term", "--tb=no", "-q"]

        result = subprocess.run(cmd, capture_output=True, text=True)
        end_time = time.time()
        signal.alarm(0)

        print(f"✅ 批次完成! 耗时: {end_time - start_time:.2f}秒")
        print(f"📊 返回码: {result.returncode}")

        # 显示测试统计
        if result.stdout:
            lines = result.stdout.split("\n")
            for line in lines[-10:]:
                if "====" in line and ("passed" in line or "failed" in line or "TOTAL" in line):
                    print(f"📋 结果: {line.strip()}")

        return True, result

    except TimeoutError:
        signal.alarm(0)
        print(f"⏰ 批次 {batch_name} 超时!")
        return False, None
    except Exception as e:
        signal.alarm(0)
        print(f"❌ 批次异常: {e}")
        return False, None


def main():
    # 动态获取所有测试文件
    all_files = get_test_files()

    print("🔍 分批测试定位器")
    print(f"📂 总文件数: {len(all_files)}")

    # 分成3批测试
    batch_size = 20
    batches = [
        (all_files[:batch_size], "第1批 (前20个)"),
        (all_files[batch_size : batch_size * 2], "第2批 (中20个)"),
        (all_files[batch_size * 2 :], f"第3批 (后{len(all_files[batch_size*2:])}个)"),
    ]

    for i, (batch_files, batch_name) in enumerate(batches, 1):
        print(f"\n{'='*60}")
        print(f"🎯 开始测试 {batch_name}")

        success, result = test_file_batch(batch_files, batch_name, timeout_seconds=150)

        if not success:
            print(f"\n🚨 {batch_name} 卡死!")
            print("🔍 需要进一步细分这个批次...")

            # 如果批次卡死，进一步细分
            sub_batch_size = 10
            for j in range(0, len(batch_files), sub_batch_size):
                sub_batch = batch_files[j : j + sub_batch_size]
                sub_name = f"{batch_name} 子批次 {j//sub_batch_size + 1}"

                print(f"\n🔍 测试子批次: {sub_name}")
                sub_success, _ = test_file_batch(sub_batch, sub_name, timeout_seconds=90)

                if not sub_success:
                    print(f"🚨 找到问题子批次: {sub_name}")
                    print("📋 问题文件:")
                    for f in sub_batch:
                        print(f"  - {f}")
                    return sub_batch

            break
        else:
            print(f"✅ {batch_name} 正常完成")

    print("\n🎉 所有批次都正常完成!")
    print("💭 可能问题在于全部文件一起运行时的资源冲突")
    return None


if __name__ == "__main__":
    problem_batch = main()

    if problem_batch:
        print("\n📋 问题定位:")
        print(f"🚨 问题批次包含 {len(problem_batch)} 个文件")
        print("💡 建议逐一检查这些文件中的资源使用")
    else:
        print("\n📋 结论:")
        print("✅ 分批测试都正常")
        print("🤔 问题可能是全局资源冲突或内存问题")
