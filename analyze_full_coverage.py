#!/usr/bin/env python3
"""
📊 完整测试覆盖率分析工具 - 包括测试文件
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


def analyze_full_coverage():
    """分析完整覆盖率数据 - 包括测试文件"""
    data = load_coverage_data()
    if not data:
        return

    print("📊 Python 交易框架完整覆盖率分析报告")
    print("=" * 60)

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

    # 分别统计源码和测试文件
    src_stats = {"executed": 0, "missing": 0, "total": 0, "files": 0}
    test_stats = {"executed": 0, "missing": 0, "total": 0, "files": 0}
    other_stats = {"executed": 0, "missing": 0, "total": 0, "files": 0}

    # 计算模块覆盖率
    src_modules = {}
    test_modules = {}

    for filepath, file_data in files.items():
        executed = len(file_data.get("executed_lines", []))
        missing = len(file_data.get("missing_lines", []))
        total = executed + missing

        if filepath.startswith("src/"):
            # 源码文件
            src_stats["executed"] += executed
            src_stats["missing"] += missing
            src_stats["total"] += total
            src_stats["files"] += 1

            # 提取源码模块名
            parts = filepath.replace("src/", "").split("/")
            if len(parts) > 1:
                module = parts[0]
            else:
                module = "root"

            if module not in src_modules:
                src_modules[module] = {"executed": 0, "missing": 0, "total": 0, "files": 0}

            src_modules[module]["executed"] += executed
            src_modules[module]["missing"] += missing
            src_modules[module]["total"] += total
            src_modules[module]["files"] += 1

        elif filepath.startswith("tests/"):
            # 测试文件
            test_stats["executed"] += executed
            test_stats["missing"] += missing
            test_stats["total"] += total
            test_stats["files"] += 1

        else:
            # 其他文件
            other_stats["executed"] += executed
            other_stats["missing"] += missing
            other_stats["total"] += total
            other_stats["files"] += 1

    # 显示分类统计
    print("📁 分类覆盖率统计:")
    print("-" * 60)

    for category, stats in [
        ("源码文件 (src/)", src_stats),
        ("测试文件 (tests/)", test_stats),
        ("其他文件", other_stats),
    ]:
        if stats["total"] > 0:
            coverage = (stats["executed"] / stats["total"]) * 100
            print(
                f"{category:20} | {coverage:5.1f}% | {stats['executed']:4d}/{stats['total']:4d} lines | {stats['files']:3d} files"
            )

    print()

    # 显示源码模块覆盖率
    print("🔍 源码模块覆盖率分析:")
    print("-" * 60)
    module_list = []
    for module, stats in src_modules.items():
        if stats["total"] > 0:
            coverage = (stats["executed"] / stats["total"]) * 100
            module_list.append((coverage, module, stats))

    # 按覆盖率排序
    module_list.sort(key=lambda x: x[0])

    for coverage, module, stats in module_list:
        print(
            f"{module:25} | {coverage:5.1f}% | {stats['executed']:4d}/{stats['total']:4d} lines | {stats['files']:2d} files"
        )

    print("\n" + "=" * 60)

    # 找出需要重点关注的低覆盖率源码文件
    print("🎯 需要重点关注的低覆盖率源码文件 (<30%):")
    print("-" * 80)

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
        print(f"{filepath:60} | {coverage:5.1f}% | {executed:3d}/{total:3d} lines")

    print(f"\n📌 发现 {len(low_coverage_files)} 个低覆盖率源码文件")

    # 显示测试文件覆盖率情况
    print("\n🧪 测试文件覆盖率情况:")
    print("-" * 80)

    test_files = []
    for filepath, file_data in files.items():
        if not filepath.startswith("tests/"):
            continue

        executed = len(file_data.get("executed_lines", []))
        missing = len(file_data.get("missing_lines", []))
        total = executed + missing

        if total > 0:
            coverage = (executed / total) * 100
            test_files.append((coverage, filepath, executed, missing, total))

    # 按覆盖率排序，最低的在前
    test_files.sort(key=lambda x: x[0])

    for coverage, filepath, executed, missing, total in test_files[
        -10:
    ]:  # 显示覆盖率最高的10个测试文件
        print(f"{filepath:60} | {coverage:5.1f}% | {executed:3d}/{total:3d} lines")

    print(f"\n🧪 共有 {len(test_files)} 个测试文件")

    # 高覆盖率源码文件（表扬）
    print("\n🏆 高覆盖率源码文件 (>80%):")
    print("-" * 80)

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

    for coverage, filepath, executed, missing, total in high_coverage_files[:15]:  # 显示前15个
        print(f"{filepath:60} | {coverage:5.1f}% | {executed:3d}/{total:3d} lines")

    print(f"\n🎉 发现 {len(high_coverage_files)} 个高覆盖率源码文件")


if __name__ == "__main__":
    analyze_full_coverage()
