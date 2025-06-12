#!/usr/bin/env python3
"""
覆盖率分析脚本
分析各模块的测试覆盖率情况
"""

import json


def analyze_coverage():
    """分析覆盖率数据"""
    with open("coverage.json", "r") as f:
        data = json.load(f)

    files = data["files"]
    total = data["totals"]

    # 按模块分组统计
    modules = {}
    for file_path, info in files.items():
        if file_path.startswith("src/"):
            parts = file_path.split("/")
            if len(parts) >= 2:
                module = parts[1]
            else:
                module = "root"
        else:
            module = "other"

        if module not in modules:
            modules[module] = {"statements": 0, "missing": 0, "files": 0}
        modules[module]["statements"] += info["summary"]["num_statements"]
        modules[module]["missing"] += info["summary"]["missing_lines"]
        modules[module]["files"] += 1

    print("🎯 项目整体覆盖率报告")
    print("=" * 70)
    print(f'📊 总体覆盖率: {total["percent_covered"]:.1f}%')
    print(f'📝 总代码行数: {total["num_statements"]:,}')
    print(f'✅ 已覆盖行数: {total["num_statements"] - total["missing_lines"]:,}')
    print(f'❌ 未覆盖行数: {total["missing_lines"]:,}')
    print()

    print("📋 各模块覆盖率详情:")
    print("=" * 70)
    print(f'{"模块名":<20} | {"覆盖率":<8} | {"代码行数":<8} | {"文件数":<6} | {"状态":<10}')
    print("-" * 70)

    for module, stats in sorted(modules.items()):
        if stats["statements"] > 0:
            coverage = (stats["statements"] - stats["missing"]) / stats["statements"] * 100

            # 状态评估
            if coverage >= 80:
                status = "🟢 优秀"
            elif coverage >= 60:
                status = "🟡 良好"
            elif coverage >= 40:
                status = "🟠 待改进"
            else:
                status = "🔴 需关注"

            print(
                f'{module:<20} | {coverage:6.1f}% | {stats["statements"]:6d}行 | {stats["files"]:4d}个 | {status}'
            )

    print()
    print("🎯 优化建议:")
    print("=" * 70)

    # 找出覆盖率最低的模块
    low_coverage_modules = []
    for module, stats in modules.items():
        if stats["statements"] > 0:
            coverage = (stats["statements"] - stats["missing"]) / stats["statements"] * 100
            if coverage < 30 and stats["statements"] > 50:  # 只关注代码量较大的模块
                low_coverage_modules.append((module, coverage, stats["statements"]))

    if low_coverage_modules:
        print("🔴 需要优先提升覆盖率的模块:")
        for module, coverage, lines in sorted(low_coverage_modules, key=lambda x: x[1]):
            print(f"   • {module}: {coverage:.1f}% ({lines}行代码)")
        print()

    # 找出表现优秀的模块
    good_modules = []
    for module, stats in modules.items():
        if stats["statements"] > 0:
            coverage = (stats["statements"] - stats["missing"]) / stats["statements"] * 100
            if coverage >= 70:
                good_modules.append((module, coverage))

    if good_modules:
        print("🟢 覆盖率表现优秀的模块:")
        for module, coverage in sorted(good_modules, key=lambda x: x[1], reverse=True):
            print(f"   • {module}: {coverage:.1f}%")
        print()

    # 计算达到不同覆盖率目标需要的工作量
    current_covered = total["num_statements"] - total["missing_lines"]
    total_lines = total["num_statements"]

    print("📈 覆盖率目标分析:")
    for target in [30, 40, 50, 60, 70, 80]:
        if total["percent_covered"] < target:
            needed_lines = int(total_lines * target / 100) - current_covered
            print(f"   • 达到 {target}% 需要再覆盖 {needed_lines:,} 行代码")


if __name__ == "__main__":
    analyze_coverage()
