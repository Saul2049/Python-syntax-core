#!/usr/bin/env python3
"""
精确卡死定位器
基于88%进度信息，定位具体哪个测试导致卡死
"""

import signal
import subprocess


class TimeoutError(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutError("测试超时!")


def get_test_list():
    """获取所有测试的列表"""
    print("📋 收集测试列表...")
    try:
        result = subprocess.run(
            ["pytest", "--collect-only", "-q"], capture_output=True, text=True, timeout=30
        )

        # 解析测试列表
        tests = []
        for line in result.stdout.split("\n"):
            if "::" in line and "test_" in line:
                # 提取测试名称，格式如 tests/test_file.py::TestClass::test_method
                tests.append(line.strip())

        print(f"✅ 收集到 {len(tests)} 个测试")
        return tests
    except Exception as e:
        print(f"❌ 收集测试失败: {e}")
        return []


def run_tests_until_position(tests, target_position, timeout_seconds=120):
    """运行测试直到指定位置"""

    if target_position > len(tests):
        target_position = len(tests)

    target_tests = tests[:target_position]
    print(f"🎯 运行前 {target_position} 个测试 (约{target_position/len(tests)*100:.1f}%)")

    # 设置超时
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)

    try:
        # 将测试写入临时文件
        with open("temp_test_list.txt", "w") as f:
            for test in target_tests:
                f.write(f"{test}\n")

        # 运行pytest
        cmd = ["pytest", "--tb=no", "-v"] + target_tests
        print(f"📝 运行命令: pytest --tb=no -v [前{target_position}个测试]")

        result = subprocess.run(cmd, capture_output=True, text=True)
        signal.alarm(0)

        print(f"✅ 测试完成! 返回码: {result.returncode}")
        return True, result

    except TimeoutError:
        signal.alarm(0)
        print(f"⏰ 测试在位置 {target_position} 附近超时!")
        return False, None
    except Exception as e:
        signal.alarm(0)
        print(f"❌ 执行异常: {e}")
        return False, None


def binary_search_hang_position(tests):
    """二分查找卡死位置"""
    print("🔍 开始二分查找卡死位置...")

    total_tests = len(tests)
    left = 0
    right = total_tests
    last_working_position = 0

    # 基于88%的信息，从85%开始搜索
    start_position = int(total_tests * 0.85)  # 从85%开始
    print(f"📍 基于88%卡死信息，从位置 {start_position} (85%) 开始搜索")

    # 先测试85%位置
    success, _ = run_tests_until_position(tests, start_position, timeout_seconds=90)

    if success:
        print("✅ 85%位置正常，问题在85%-100%之间")
        left = start_position
        last_working_position = start_position
    else:
        print("❌ 85%位置就有问题，问题在更早位置")
        right = start_position

    # 二分查找
    while left < right - 10:  # 精确到10个测试范围内
        mid = (left + right) // 2
        print(f"\n🎯 测试中点位置: {mid} ({mid/total_tests*100:.1f}%)")

        success, result = run_tests_until_position(tests, mid, timeout_seconds=90)

        if success:
            print(f"✅ 位置 {mid} 正常")
            left = mid
            last_working_position = mid
        else:
            print(f"❌ 位置 {mid} 卡死")
            right = mid

    print("\n🎯 定位结果:")
    print(
        f"✅ 最后正常位置: {last_working_position} ({last_working_position/total_tests*100:.1f}%)"
    )
    print(f"❌ 卡死开始位置: 约 {right} ({right/total_tests*100:.1f}%)")

    # 显示可能的问题测试
    if right < len(tests):
        problem_range = tests[last_working_position : right + 5]
        print(f"\n🚨 可能导致卡死的测试 (位置 {last_working_position}-{right+5}):")
        for i, test in enumerate(problem_range):
            pos = last_working_position + i
            print(f"  {pos:4d}: {test}")


def main():
    print("🔍 精确卡死定位器启动")
    print("📊 基于信息: 总测试数1237，在88%处卡死")

    # 获取测试列表
    tests = get_test_list()

    if not tests:
        print("❌ 无法获取测试列表")
        return

    print(f"📋 总测试数: {len(tests)}")
    print(f"📍 88%位置约为: {int(len(tests) * 0.88)}")

    # 开始二分查找
    binary_search_hang_position(tests)


if __name__ == "__main__":
    main()
