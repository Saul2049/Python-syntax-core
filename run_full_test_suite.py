#!/usr/bin/env python3
"""运行完整测试套件，带超时保护"""

import signal
import subprocess
import time


class TimeoutError(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutError("测试套件超时!")


def main():
    print("🚀 运行完整测试套件")
    print("📊 预期: 1237个测试")
    print("⏰ 超时设置: 5分钟")

    # 设置5分钟超时
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)  # 5分钟

    try:
        start_time = time.time()
        cmd = ["pytest", "--cov=src", "--cov-report=term", "--tb=no", "-q"]

        print("📝 执行命令: pytest --cov=src --cov-report=term --tb=no -q")
        print("🏃 开始运行...")

        result = subprocess.run(cmd, capture_output=True, text=True)
        end_time = time.time()
        signal.alarm(0)

        print("\n✅ 测试套件完成!")
        print(f"⏰ 总耗时: {end_time - start_time:.2f}秒")
        print(f"📊 返回码: {result.returncode}")

        # 显示覆盖率报告
        print("\n" + "=" * 60)
        print("📋 覆盖率报告:")
        print("=" * 60)
        print(result.stdout)

        if result.stderr:
            print("\n⚠️ 错误输出:")
            print(result.stderr)

        return True

    except TimeoutError:
        signal.alarm(0)
        print("\n⏰ 测试套件在5分钟内未完成")
        print("🔍 可能仍有卡死问题，或测试套件确实很大")
        return False
    except Exception as e:
        signal.alarm(0)
        print(f"\n❌ 执行异常: {e}")
        return False


if __name__ == "__main__":
    success = main()

    if success:
        print("\n🎉 成功获得完整项目覆盖率!")
    else:
        print("\n❌ 测试套件执行有问题")
