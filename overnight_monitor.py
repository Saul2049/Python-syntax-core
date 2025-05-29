#!/usr/bin/env python3
"""
🌙 过夜监控脚本
每小时记录一次W3+W4状态，方便明早查看
"""

import datetime
import subprocess
import time


def log_status():
    """记录当前状态"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # 运行状态检查
        result = subprocess.run(
            ["python", "scripts/status_check.py"], capture_output=True, text=True, timeout=30
        )

        with open("overnight_log.txt", "a") as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"⏰ 监控时间: {timestamp}\n")
            f.write("=" * 80 + "\n")
            f.write(result.stdout)
            f.write("\n")

        print(f"✅ {timestamp} - 状态已记录")

    except Exception as e:
        with open("overnight_log.txt", "a") as f:
            f.write(f"\n❌ {timestamp} - 监控错误: {e}\n")
        print(f"❌ {timestamp} - 监控错误: {e}")


def main():
    """主监控循环"""
    print("🌙 启动过夜监控...")
    print("📝 状态将每小时记录到 overnight_log.txt")
    print("🛑 按 Ctrl+C 停止监控")

    # 初始记录
    log_status()

    try:
        while True:
            # 等待1小时
            time.sleep(3600)
            log_status()

    except KeyboardInterrupt:
        print("\n⏸️ 监控已停止")


if __name__ == "__main__":
    main()
