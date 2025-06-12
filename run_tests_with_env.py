#!/usr/bin/env python3
"""
带环境变量的测试运行脚本
自动设置测试环境并运行pytest
"""

import subprocess
import sys

from test_env_setup import setup_test_environment


def run_tests_with_environment(test_args=None):
    """设置环境变量并运行测试"""
    print("🔧 正在设置测试环境...")
    setup_test_environment()

    # 构建pytest命令
    if test_args is None:
        test_args = ["tests/", "-v", "--tb=short"]

    pytest_cmd = ["python3", "-m", "pytest"] + test_args

    print(f"\n🚀 运行测试命令: {' '.join(pytest_cmd)}")
    print("=" * 60)

    # 运行测试
    try:
        result = subprocess.run(pytest_cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n❌ 运行测试时出错: {e}")
        return 1


def main():
    """主函数"""
    # 从命令行参数获取测试参数
    test_args = sys.argv[1:] if len(sys.argv) > 1 else None

    exit_code = run_tests_with_environment(test_args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
