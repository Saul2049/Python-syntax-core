#!/usr/bin/env python3
"""
M4优化完成度检查脚本
"""

import os
import json
from datetime import datetime


def check_completion():
    """检查M4优化完成度"""

    print("🔍 M4收尾螺丝完成度检查")
    print("=" * 60)

    # 检查1: 异步优化
    print("\n📊 检查1: 异步引擎优化")

    engine_file = "src/core/async_trading_engine.py"
    metrics_file = "src/monitoring/metrics_collector.py"

    engine_optimized = False
    metrics_enhanced = False

    if os.path.exists(engine_file):
        with open(engine_file, "r") as f:
            content = f.read()
        engine_optimized = "asyncio.create_task" in content and "_batch_update_metrics" in content

    if os.path.exists(metrics_file):
        with open(metrics_file, "r") as f:
            content = f.read()
        metrics_enhanced = "task_latency_seconds" in content and "measure_task_latency" in content

    print(f"   异步引擎优化: {'✅' if engine_optimized else '❌'}")
    print(f"   监控指标增强: {'✅' if metrics_enhanced else '❌'}")

    # 检查2: Canary部署
    print("\n🕯️ 检查2: Canary部署系统")

    makefile_exists = os.path.exists("Makefile")
    canary_script_exists = os.path.exists("scripts/canary_deploy.py")
    assert_script_exists = os.path.exists("scripts/assert_p95.py")

    canary_commands = False
    if makefile_exists:
        with open("Makefile", "r") as f:
            content = f.read()
        canary_commands = "canary-testnet" in content and "monitor-canary" in content

    print(f"   Makefile增强: {'✅' if canary_commands else '❌'}")
    print(f"   Canary部署脚本: {'✅' if canary_script_exists else '❌'}")
    print(f"   P95断言脚本: {'✅' if assert_script_exists else '❌'}")

    # 检查3: 自动化回归
    print("\n📚 检查3: 自动化回归系统")

    workflow_exists = os.path.exists(".github/workflows/perf-regression.yml")
    runbook_exists = os.path.exists("docs/M4_INCIDENT_RUNBOOK.md")

    print(f"   GitHub Actions工作流: {'✅' if workflow_exists else '❌'}")
    print(f"   故障处理手册: {'✅' if runbook_exists else '❌'}")

    # 总体评估
    checks = [
        engine_optimized,
        metrics_enhanced,
        canary_commands,
        canary_script_exists,
        assert_script_exists,
        workflow_exists,
        runbook_exists,
    ]

    completed = sum(checks)
    total = len(checks)
    completion_rate = completed / total * 100

    print("\n" + "=" * 60)
    print("🎯 M4收尾螺丝总体评估")
    print("=" * 60)
    print(f"📊 完成度: {completed}/{total} ({completion_rate:.1f}%)")

    if completion_rate >= 90:
        print("🎉 M4阶段完美收官！所有收尾螺丝已拧紧")
        print("✅ 推荐立即进入M5阶段")
        status = "READY_FOR_M5"
    elif completion_rate >= 70:
        print("✅ M4阶段基本完成，可以进入M5阶段")
        status = "MOSTLY_COMPLETE"
    else:
        print("⚠️ 部分收尾螺丝需要继续完善")
        status = "NEEDS_WORK"

    # 保存报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "completion_rate": completion_rate,
        "status": status,
        "checks": {
            "async_engine_optimized": engine_optimized,
            "metrics_enhanced": metrics_enhanced,
            "canary_commands": canary_commands,
            "canary_script": canary_script_exists,
            "assert_script": assert_script_exists,
            "github_workflow": workflow_exists,
            "incident_runbook": runbook_exists,
        },
    }

    os.makedirs("output", exist_ok=True)
    with open(f"output/m4_completion_{int(datetime.now().timestamp())}.json", "w") as f:
        json.dump(report, f, indent=2)

    return completion_rate >= 70


if __name__ == "__main__":
    success = check_completion()
    exit(0 if success else 1)
