#!/usr/bin/env python3
"""
开发工具脚本
提供一键开发环境配置和常用开发任务
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def run_command(cmd: str, description: str = "") -> bool:
    """运行命令并显示进度"""
    if description:
        print(f"🔧 {description}")

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ 成功")
            return True
        else:
            print(f"   ❌ 失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ 异常: {e}")
        return False


def setup_development_environment():
    """一键配置开发环境"""
    print("🚀 开始配置开发环境...")
    print("=" * 50)

    tasks = [
        ("python -m pip install --upgrade pip", "升级pip"),
        ("pip install pytest pytest-cov pytest-xdist", "安装测试工具"),
        ("pip install ruff mypy black isort", "安装代码质量工具"),
        ("pip install prometheus_client requests pandas numpy", "安装核心依赖"),
    ]

    success_count = 0
    for cmd, desc in tasks:
        if run_command(cmd, desc):
            success_count += 1
        time.sleep(0.5)

    print(f"\n📊 安装结果: {success_count}/{len(tasks)} 成功")

    # 创建配置文件
    if not os.path.exists(".env"):
        print("📝 创建环境配置文件...")
        with open(".env", "w") as f:
            f.write(
                """# Python交易系统环境配置
# Trading System Environment Configuration

# 基础配置
ENVIRONMENT=development
LOG_LEVEL=INFO

# 监控配置
METRICS_ENABLED=true
PROMETHEUS_PORT=8000

# 交易配置 (演示模式)
DEMO_MODE=true
ACCOUNT_EQUITY=10000.0
RISK_PERCENT=0.01
ATR_MULTIPLIER=2.0

# API配置 (请填入真实值)
# API_KEY=your_api_key_here
# API_SECRET=your_api_secret_here
# TG_TOKEN=your_telegram_token_here
"""
            )
        print("   ✅ .env 文件已创建")

    # 验证环境
    print("\n🧪 验证开发环境...")
    verification_tasks = [
        ("python -c \"import pandas, numpy, pytest; print('核心包正常')\"", "检查核心包"),
        (
            "python -c \"from src.monitoring.metrics_collector import init_monitoring; print('监控系统正常')\"",
            "检查监控系统",
        ),
        ("python scripts/benchmark_latency.py > /dev/null && echo '基准测试正常'", "验证性能测试"),
    ]

    for cmd, desc in verification_tasks:
        run_command(cmd, desc)
        time.sleep(0.5)

    print("\n🎉 开发环境配置完成！")
    print("\n📋 下一步操作:")
    print("   1. make test          # 运行测试")
    print("   2. make benchmark     # 性能基准测试")
    print("   3. make monitor       # 启动监控面板")
    print("   4. make health        # 系统健康检查")


def create_jupyter_notebook():
    """创建快速入门Jupyter笔记本"""
    print("📓 创建快速入门笔记本...")

    notebook_content = """{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# 🚀 Python交易系统快速入门\\n",
    "\\n",
    "本笔记本提供交易系统的快速上手指南和实时监控示例。"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "source": [
    "# 导入必要的库\\n",
    "import sys\\n",
    "import os\\n",
    "sys.path.append('..')\\n",
    "\\n",
    "from src.monitoring.metrics_collector import init_monitoring\\n",
    "from src.core.signal_processor_optimized import get_trading_signals_optimized\\n",
    "from scripts.benchmark_latency import LatencyBenchmark\\n",
    "\\n",
    "print('📊 交易系统模块加载完成')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "source": [
    "# 启动监控系统\\n",
    "collector = init_monitoring()\\n",
    "print(f'📈 监控系统已启动 - http://localhost:{collector.config.port}/metrics')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "source": [
    "# 运行性能基准测试\\n",
    "benchmark = LatencyBenchmark()\\n",
    "results = benchmark.benchmark_signal_calculation(50)\\n",
    "\\n",
    "print(f\\"🧪 信号计算性能测试结果:\\")\\n",
    "print(f\\"   平均延迟: {results['mean']*1000:.1f}ms\\")\\n",
    "print(f\\"   P95延迟: {results['p95']*1000:.1f}ms\\")\\n",
    "print(f\\"   状态: {'✅ 达标' if results['p95']*1000 < 500 else '⚠️ 需优化'}\\")"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}"""

    # 创建docs目录
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)

    # 写入笔记本
    notebook_path = docs_dir / "quickstart.ipynb"
    with open(notebook_path, "w") as f:
        f.write(notebook_content)

    print(f"   ✅ 笔记本已创建: {notebook_path}")
    print("   💡 使用 'jupyter notebook docs/quickstart.ipynb' 打开")


def run_development_checks():
    """运行开发检查"""
    print("🔍 运行开发检查...")
    print("=" * 50)

    checks = [
        ("make health", "健康检查"),
        ("make benchmark-quick", "快速性能测试"),
        ("python -m pytest tests/ -x --tb=short", "快速测试"),
    ]

    for cmd, desc in checks:
        print(f"\n{desc}:")
        run_command(cmd, f"执行{desc}")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("🛠️ Python交易系统开发工具")
        print("\n可用命令:")
        print("  setup    - 一键配置开发环境")
        print("  notebook - 创建快速入门笔记本")
        print("  check    - 运行开发检查")
        print("  all      - 执行所有操作")
        return

    command = sys.argv[1]

    if command == "setup":
        setup_development_environment()
    elif command == "notebook":
        create_jupyter_notebook()
    elif command == "check":
        run_development_checks()
    elif command == "all":
        setup_development_environment()
        create_jupyter_notebook()
        run_development_checks()
    else:
        print(f"❌ 未知命令: {command}")


if __name__ == "__main__":
    main()
