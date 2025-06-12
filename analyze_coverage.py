#!/usr/bin/env python3
"""
📊 测试覆盖率分析工具
"""

import json
from pathlib import Path


def load_coverage_data():
    """加载coverage.json数据"""
    coverage_file = Path("coverage.json")
    if not coverage_file.exists():
        print("❌ coverage.json 文件不存在")
        return None

    with coverage_file.open("r") as f:
        return json.load(f)


def analyze_coverage():
    """分析覆盖率数据"""
    data = load_coverage_data()
    if not data:
        return

    print("📊 Python 交易框架覆盖率分析报告")
    print("=" * 50)

    # 获取总体统计
    summary = data.get("totals", {})
    total_statements = summary.get("num_statements", 0)
    covered_statements = summary.get("covered_lines", 0)
    missing_statements = summary.get("missing_lines", 0)
    overall_coverage = summary.get("percent_covered", 0)

    print(f"📈 总体覆盖率: {overall_coverage:.1f}%")
    print(f"📋 总代码行数: {total_statements:,} 行")
    print(f"✅ 已覆盖行数: {covered_statements:,} 行")
    print(f"❌ 未覆盖行数: {missing_statements:,} 行")
    print()

    # 分析各文件覆盖率
    files = data.get("files", {})

    # 计算模块覆盖率
    modules = {}
    for filepath, file_data in files.items():
        if not filepath.startswith("src/"):
            continue

        # 提取模块名
        parts = filepath.replace("src/", "").split("/")
        if len(parts) > 1:
            module = parts[0]
        else:
            module = "root"

        executed = len(file_data.get("executed_lines", []))
        missing = len(file_data.get("missing_lines", []))
        total = executed + missing

        if module not in modules:
            modules[module] = {"executed": 0, "missing": 0, "total": 0, "files": 0}

        modules[module]["executed"] += executed
        modules[module]["missing"] += missing
        modules[module]["total"] += total
        modules[module]["files"] += 1

    # 显示模块覆盖率
    print("🔍 各模块覆盖率分析:")
    print("-" * 60)
    module_list = []
    for module, stats in modules.items():
        if stats["total"] > 0:
            coverage = (stats["executed"] / stats["total"]) * 100
            module_list.append((coverage, module, stats))

    # 按覆盖率排序
    module_list.sort(key=lambda x: x[0])

    for coverage, module, stats in module_list:
        print(
            f"{module:25} | {coverage:5.1f}% | {stats['executed']:4d}/{stats['total']:4d} lines | {stats['files']:2d} files"
        )

    print("\n" + "=" * 50)

    # 找出需要重点关注的低覆盖率文件
    print("🎯 需要重点关注的低覆盖率文件 (<30%):")
    print("-" * 60)

    low_coverage_files = []
    for filepath, file_data in files.items():
        if not filepath.startswith("src/"):
            continue

        executed = len(file_data.get("executed_lines", []))
        missing = len(file_data.get("missing_lines", []))
        total = executed + missing

        if total > 0:
            coverage = (executed / total) * 100
            if coverage < 30:
                low_coverage_files.append((coverage, filepath, executed, missing, total))

    # 按覆盖率排序，最低的在前
    low_coverage_files.sort(key=lambda x: x[0])

    for coverage, filepath, executed, missing, total in low_coverage_files:
        print(f"{filepath:50} | {coverage:5.1f}% | {executed:3d}/{total:3d} lines")

    print(f"\n📌 发现 {len(low_coverage_files)} 个低覆盖率文件")

    # 高覆盖率文件（表扬）
    print("\n🏆 高覆盖率文件 (>80%):")
    print("-" * 60)

    high_coverage_files = []
    for filepath, file_data in files.items():
        if not filepath.startswith("src/"):
            continue

        executed = len(file_data.get("executed_lines", []))
        missing = len(file_data.get("missing_lines", []))
        total = executed + missing

        if total > 0:
            coverage = (executed / total) * 100
            if coverage > 80:
                high_coverage_files.append((coverage, filepath, executed, missing, total))

    # 按覆盖率排序，最高的在前
    high_coverage_files.sort(key=lambda x: x[0], reverse=True)

    for coverage, filepath, executed, missing, total in high_coverage_files[:10]:  # 只显示前10个
        print(f"{filepath:50} | {coverage:5.1f}% | {executed:3d}/{total:3d} lines")

    print(f"\n🎉 发现 {len(high_coverage_files)} 个高覆盖率文件")


if __name__ == "__main__":
    analyze_coverage()
