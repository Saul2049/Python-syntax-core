#!/usr/bin/env python3
"""
M5内存优化完成度检查脚本
M5 Memory Optimization Completion Check
"""

import json
import os
import subprocess
from datetime import datetime


def check_makefile_commands():
    """检查Makefile命令集成"""
    print("\n📋 检查1: Makefile命令集成")
    makefile_commands = [
        "mem-baseline",
        "mem-benchmark",
        "mem-snapshot",
        "gc-profile",
        "mem-health",
        "mem-clean",
    ]

    if not os.path.exists("Makefile"):
        return False

    with open("Makefile", "r") as f:
        makefile_content = f.read()

    commands_found = 0
    for cmd in makefile_commands:
        if f"{cmd}:" in makefile_content:
            commands_found += 1
            print(f"   ✅ {cmd}")
        else:
            print(f"   ❌ {cmd}")

    return commands_found >= len(makefile_commands) * 0.8


def check_memory_tools():
    """检查内存工具脚本"""
    print("\n🛠️ 检查2: 内存工具脚本")
    tool_scripts = {
        "scripts/memory/mem_snapshot.py": "内存快照工具",
        "scripts/memory/gc_profiler.py": "GC性能分析器",
        "scripts/memory/mem_baseline.py": "内存基线采集器",
    }

    tools_working = 0
    for script, name in tool_scripts.items():
        if os.path.exists(script):
            try:
                result = subprocess.run(
                    ["python", "-m", "py_compile", script], capture_output=True, text=True
                )
                if result.returncode == 0:
                    print(f"   ✅ {name}")
                    tools_working += 1
                else:
                    print(f"   ❌ {name} (语法错误)")
            except Exception:
                print(f"   ❌ {name} (测试失败)")
        else:
            print(f"   ❌ {name} (文件不存在)")

    return tools_working >= len(tool_scripts)


def check_monitoring_integration():
    """检查监控系统集成"""
    print("\n📊 检查3: 监控系统集成")
    metrics_file = "src/monitoring/metrics_collector.py"

    if not os.path.exists(metrics_file):
        return False

    with open(metrics_file, "r") as f:
        metrics_content = f.read()

    m5_metrics = [
        "process_memory_rss_bytes",
        "gc_pause_duration",
        "memory_growth_rate",
        "update_process_memory_stats",
        "record_gc_event",
    ]

    metrics_found = sum(1 for metric in m5_metrics if metric in metrics_content)
    integration_ok = metrics_found >= len(m5_metrics) * 0.8

    print(f"   M5指标集成: {metrics_found}/{len(m5_metrics)} ({'✅' if integration_ok else '❌'})")
    return integration_ok


def check_functionality():
    """检查功能验证"""
    print("\n🧪 检查4: 功能验证")

    # 测试内存健康检查
    try:
        result = subprocess.run(["make", "mem-health"], capture_output=True, text=True, timeout=10)
        mem_health_works = result.returncode == 0
        print(f"   内存健康检查: {'✅' if mem_health_works else '❌'}")
    except Exception:
        mem_health_works = False
        print("   内存健康检查: ❌ (执行失败)")

    # 测试快照工具
    try:
        result = subprocess.run(
            ["python", "scripts/memory/mem_snapshot.py", "--save"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        snapshot_works = result.returncode == 0
        print(f"   内存快照工具: {'✅' if snapshot_works else '❌'}")
    except Exception:
        snapshot_works = False
        print("   内存快照工具: ❌ (执行失败)")

    return mem_health_works and snapshot_works


def check_output_structure():
    """检查输出结构"""
    print("\n📁 检查5: 输出结构")
    if not os.path.exists("output"):
        print("   输出目录: ❌ (不存在)")
        return False

    output_files = [f for f in os.listdir("output") if f.startswith(("mem_", "gc_"))]
    has_files = len(output_files) > 0
    print(f"   输出文件: {len(output_files)}个 ({'✅' if has_files else '❌'})")
    return has_files


def check_documentation():
    """检查文档完整性"""
    print("\n📚 检查6: 文档完整性")
    doc_files = {
        "docs/M5_MEMORY_OPTIMIZATION_GUIDE.md": "M5内存优化指南",
        "docs/M4_INCIDENT_RUNBOOK.md": "M4故障处理手册",
    }

    docs_found = 0
    for doc_file, name in doc_files.items():
        if os.path.exists(doc_file):
            print(f"   ✅ {name}")
            docs_found += 1
        else:
            print(f"   ❌ {name}")

    return docs_found >= len(doc_files) * 0.5


def generate_completion_report(checks):
    """生成完成度报告"""
    completed_checks = sum(checks.values())
    total_checks = len(checks)
    completion_rate = completed_checks / total_checks * 100

    print("\n" + "=" * 60)
    print("🎯 M5基础设施完成度评估")
    print("=" * 60)
    print(f"📊 完成度: {completed_checks}/{total_checks} ({completion_rate:.1f}%)")

    # 状态判定
    if completion_rate >= 90:
        status = "🎉 M5基础设施完美就绪！"
        color = "✅"
        ready_for_optimization = True
    elif completion_rate >= 70:
        status = "⚡ M5基础设施基本就绪，可以开始优化"
        color = "🟡"
        ready_for_optimization = True
    else:
        status = "⚠️ M5基础设施需要继续完善"
        color = "❌"
        ready_for_optimization = False

    print(f"{color} 状态: {status}")

    # 详细结果
    print("\n📋 详细检查结果:")
    for check_name, passed in checks.items():
        emoji = "✅" if passed else "❌"
        print(f"   {emoji} {check_name}")

    if ready_for_optimization:
        print("\n🚀 下一步行动:")
        print("   1. 运行 make mem-baseline --duration 1800")
        print("   2. 开始对象池/LRU优化 (W1)")
        print("   3. 实施GC调参策略 (W2)")
    else:
        print("\n🔧 需要完成的任务:")
        for check_name, passed in checks.items():
            if not passed:
                print(f"   • 修复 {check_name}")

    return {
        "completion_rate": completion_rate,
        "status": status,
        "ready_for_optimization": ready_for_optimization,
        "checks": checks,
    }


def check_m5_completion():
    """检查M5内存优化基础设施完成度"""
    print("🧠 M5内存&GC优化基础设施检查")
    print("=" * 60)

    # 执行各项检查
    checks = {
        "makefile_commands": check_makefile_commands(),
        "memory_tools": check_memory_tools(),
        "gc_profiler": os.path.exists("scripts/memory/gc_profiler.py"),
        "baseline_collector": os.path.exists("scripts/memory/mem_baseline.py"),
        "monitoring_integration": check_monitoring_integration(),
        "functionality": check_functionality(),
        "output_structure": check_output_structure(),
        "documentation": check_documentation(),
    }

    # 生成报告
    report_data = generate_completion_report(checks)

    # 保存检查报告
    report = {"timestamp": datetime.now().isoformat(), **report_data}

    os.makedirs("output", exist_ok=True)
    with open(f"output/m5_completion_{int(datetime.now().timestamp())}.json", "w") as f:
        json.dump(report, f, indent=2)

    print("=" * 60)

    return report_data["ready_for_optimization"]


if __name__ == "__main__":
    success = check_m5_completion()
    exit(0 if success else 1)
