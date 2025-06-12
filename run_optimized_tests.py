#!/usr/bin/env python3
"""内存优化测试运行器"""

import gc
import os
import subprocess
import sys


def run_optimized_tests():
    """运行内存优化的测试"""

    # 设置环境变量优化Python内存使用
    env = os.environ.copy()
    env.update(
        {
            "PYTHONHASHSEED": "0",  # 固定哈希种子
            "PYTHONUNBUFFERED": "1",  # 取消缓冲
            "PYTHONDONTWRITEBYTECODE": "1",  # 不生成.pyc文件
            "PYTHONMALLOC": "malloc",  # 使用系统malloc
            "PYTHONASYNCIODEBUG": "0",  # 关闭asyncio调试
        }
    )

    # 优化的pytest参数
    cmd = [
        "pytest",
        "tests/",
        "--tb=short",  # 简短的错误追踪
        "--disable-warnings",  # 禁用警告
        "--maxfail=10",  # 最多10个失败
        "--durations=10",  # 显示最慢的10个测试
        "-x",  # 遇到第一个失败就停止(可选)
        "--cov=src",  # 覆盖率
        "--cov-report=term",  # 终端报告
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
