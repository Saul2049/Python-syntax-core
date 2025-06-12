#!/usr/bin/env python3
"""
🚀 快速测试运行器 (Fast Test Runner)

提供多种测试执行策略以优化性能
"""

import subprocess
import time


def run_command(cmd, description):
    """执行命令并计时"""
    print(f"\n🚀 {description}")
    print(f"📝 命令: {cmd}")

    start_time = time.time()
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    end_time = time.time()

    duration = end_time - start_time
    print(f"⏱️  耗时: {duration:.2f}秒")

    if result.returncode == 0:
        print("✅ 成功!")
        # 提取通过的测试数量
        output_lines = result.stdout.split("\n")
        for line in output_lines:
            if "passed" in line and ("failed" in line or "error" in line):
                print(f"📊 结果: {line.strip()}")
                break
    else:
        print(f"❌ 失败 (返回码: {result.returncode})")
        if result.stderr:
            print(f"🚨 错误: {result.stderr[:200]}...")

    return duration, result.returncode == 0


def main():
    """运行不同的测试策略并比较性能"""
    print("🧪 测试性能优化对比分析")
    print("=" * 50)

    strategies = [
        {
            "name": "基础串行执行",
            "cmd": "python -m pytest tests/ --tb=no -q",
            "description": "传统单线程执行",
        },
        {
            "name": "并行执行 (auto)",
            "cmd": "python -m pytest tests/ -n auto --tb=no -q",
            "description": "自动检测CPU核心数并行",
        },
        {
            "name": "并行执行 (4进程)",
            "cmd": "python -m pytest tests/ -n 4 --tb=no -q",
            "description": "固定4个进程并行",
        },
        {
            "name": "并行执行 (8进程)",
            "cmd": "python -m pytest tests/ -n 8 --tb=no -q",
            "description": "固定8个进程并行",
        },
        {
            "name": "快速失败模式",
            "cmd": "python -m pytest tests/ -n auto --tb=no -q --maxfail=3",
            "description": "并行 + 快速失败",
        },
        {
            "name": "只跑快速测试",
            "cmd": "python -m pytest tests/test_data_processors.py tests/test_broker_enhanced_coverage.py -n auto --tb=no -q",
            "description": "只测试核心修复的文件",
        },
    ]

    results = []

    for strategy in strategies:
        duration, success = run_command(
            strategy["cmd"], f"{strategy['name']} - {strategy['description']}"
        )
        results.append({"name": strategy["name"], "duration": duration, "success": success})

        # 避免过热，稍微休息
        time.sleep(2)

    # 输出对比结果
    print("\n" + "=" * 50)
    print("📈 性能对比结果:")
    print("=" * 50)

    # 按时间排序
    results.sort(key=lambda x: x["duration"])

    baseline = None
    for i, result in enumerate(results, 1):
        status = "✅" if result["success"] else "❌"

        if baseline is None and result["success"]:
            baseline = result["duration"]
            speedup = "基准"
        elif baseline and result["success"]:
            speedup = (
                f"{baseline/result['duration']:.1f}x"
                if result["duration"] < baseline
                else f"{result['duration']/baseline:.1f}x慢"
            )
        else:
            speedup = "失败"

        print(f"{i:2d}. {status} {result['name']:20s} {result['duration']:6.1f}s  ({speedup})")

    # 推荐策略
    fastest = min([r for r in results if r["success"]], key=lambda x: x["duration"], default=None)
    if fastest:
        print(f"\n🎯 推荐策略: {fastest['name']} ({fastest['duration']:.1f}秒)")

        # 保存推荐配置
        save_optimal_config(fastest["name"])


def save_optimal_config(best_strategy):
    """保存最优配置"""
    config_map = {
        "并行执行 (auto)": "-n auto --tb=no -q",
        "并行执行 (4进程)": "-n 4 --tb=no -q",
        "并行执行 (8进程)": "-n 8 --tb=no -q",
        "快速失败模式": "-n auto --tb=no -q --maxfail=3",
    }

    if best_strategy in config_map:
        optimal_cmd = f"python -m pytest tests/ {config_map[best_strategy]}"

        with open("optimal_test_command.txt", "w") as f:
            f.write("# 🚀 推荐的最优测试命令\n")
            f.write(f"# 基于性能测试结果: {best_strategy}\n")
            f.write(f"{optimal_cmd}\n")

        print("💾 最优命令已保存到 optimal_test_command.txt")


if __name__ == "__main__":
    main()
