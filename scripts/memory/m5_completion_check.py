#!/usr/bin/env python3
"""
M5内存优化完成度检查脚本
M5 Memory Optimization Completion Check
"""

import os
import json
import subprocess
from datetime import datetime

def check_m5_completion():
    """检查M5内存优化基础设施完成度"""
    
    print("🧠 M5内存&GC优化基础设施检查")
    print("="*60)
    
    checks = {
        'makefile_commands': False,
        'memory_tools': False,
        'gc_profiler': False,
        'baseline_collector': False,
        'monitoring_integration': False,
        'documentation': False
    }
    
    # 检查1: Makefile命令
    print("\n📋 检查1: Makefile命令集成")
    makefile_commands = [
        'mem-baseline', 'mem-benchmark', 'mem-snapshot', 
        'gc-profile', 'mem-health', 'mem-clean'
    ]
    
    if os.path.exists("Makefile"):
        with open("Makefile", 'r') as f:
            makefile_content = f.read()
        
        commands_found = 0
        for cmd in makefile_commands:
            if f"{cmd}:" in makefile_content:
                commands_found += 1
                print(f"   ✅ {cmd}")
            else:
                print(f"   ❌ {cmd}")
        
        checks['makefile_commands'] = commands_found >= len(makefile_commands) * 0.8
    
    # 检查2: 内存工具脚本
    print("\n🛠️ 检查2: 内存工具脚本")
    tool_scripts = {
        'scripts/memory/mem_snapshot.py': '内存快照工具',
        'scripts/memory/gc_profiler.py': 'GC性能分析器',
        'scripts/memory/mem_baseline.py': '内存基线采集器'
    }
    
    tools_working = 0
    for script, name in tool_scripts.items():
        if os.path.exists(script):
            try:
                # 快速测试脚本语法
                result = subprocess.run(['python', '-m', 'py_compile', script], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"   ✅ {name}")
                    tools_working += 1
                else:
                    print(f"   ❌ {name} (语法错误)")
            except:
                print(f"   ❌ {name} (测试失败)")
        else:
            print(f"   ❌ {name} (文件不存在)")
    
    checks['memory_tools'] = tools_working >= len(tool_scripts)
    checks['gc_profiler'] = 'scripts/memory/gc_profiler.py' in [script for script in tool_scripts.keys() if os.path.exists(script)]
    checks['baseline_collector'] = 'scripts/memory/mem_baseline.py' in [script for script in tool_scripts.keys() if os.path.exists(script)]
    
    # 检查3: 监控集成
    print("\n📊 检查3: 监控系统集成")
    metrics_file = "src/monitoring/metrics_collector.py"
    
    if os.path.exists(metrics_file):
        with open(metrics_file, 'r') as f:
            metrics_content = f.read()
        
        m5_metrics = [
            'process_memory_rss_bytes',
            'gc_pause_duration',
            'memory_growth_rate',
            'update_process_memory_stats',
            'record_gc_event'
        ]
        
        metrics_found = sum(1 for metric in m5_metrics if metric in metrics_content)
        checks['monitoring_integration'] = metrics_found >= len(m5_metrics) * 0.8
        
        print(f"   M5指标集成: {metrics_found}/{len(m5_metrics)} ({'✅' if checks['monitoring_integration'] else '❌'})")
    
    # 检查4: 功能测试
    print("\n🧪 检查4: 功能验证")
    
    # 测试内存健康检查
    try:
        result = subprocess.run(['make', 'mem-health'], 
                              capture_output=True, text=True, timeout=10)
        mem_health_works = result.returncode == 0
        print(f"   内存健康检查: {'✅' if mem_health_works else '❌'}")
    except:
        mem_health_works = False
        print(f"   内存健康检查: ❌ (执行失败)")
    
    # 测试快照工具
    try:
        result = subprocess.run(['python', 'scripts/memory/mem_snapshot.py', '--save'], 
                              capture_output=True, text=True, timeout=15)
        snapshot_works = result.returncode == 0
        print(f"   内存快照工具: {'✅' if snapshot_works else '❌'}")
    except:
        snapshot_works = False
        print(f"   内存快照工具: ❌ (执行失败)")
    
    checks['memory_tools'] = mem_health_works and snapshot_works
    
    # 检查5: 输出目录
    print("\n📁 检查5: 输出结构")
    output_files = []
    if os.path.exists("output"):
        output_files = [f for f in os.listdir("output") if f.startswith(('mem_', 'gc_'))]
        print(f"   输出文件: {len(output_files)}个 ({'✅' if len(output_files) > 0 else '❌'})")
    else:
        print(f"   输出目录: ❌ (不存在)")
    
    # 检查6: 文档完整性
    print("\n📚 检查6: 文档完整性")
    doc_files = {
        'docs/M5_MEMORY_OPTIMIZATION_GUIDE.md': 'M5内存优化指南',
        'docs/M4_INCIDENT_RUNBOOK.md': 'M4故障处理手册'
    }
    
    docs_found = 0
    for doc_file, name in doc_files.items():
        if os.path.exists(doc_file):
            print(f"   ✅ {name}")
            docs_found += 1
        else:
            print(f"   ❌ {name}")
    
    checks['documentation'] = docs_found >= len(doc_files) * 0.5  # 至少50%的文档存在
    
    # 总体评估
    completed_checks = sum(checks.values())
    total_checks = len(checks)
    completion_rate = completed_checks / total_checks * 100
    
    print("\n" + "="*60)
    print("🎯 M5基础设施完成度评估")
    print("="*60)
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
    print(f"\n📋 详细检查结果:")
    for check_name, passed in checks.items():
        emoji = "✅" if passed else "❌"
        print(f"   {emoji} {check_name}")
    
    if ready_for_optimization:
        print(f"\n🚀 下一步行动:")
        print(f"   1. 运行 make mem-baseline --duration 1800")
        print(f"   2. 开始对象池/LRU优化 (W1)")
        print(f"   3. 实施GC调参策略 (W2)")
    else:
        print(f"\n🔧 需要完成的任务:")
        for check_name, passed in checks.items():
            if not passed:
                print(f"   • 修复 {check_name}")
    
    # 保存检查报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'completion_rate': completion_rate,
        'status': status,
        'ready_for_optimization': ready_for_optimization,
        'checks': checks,
        'output_files_count': len(output_files)
    }
    
    os.makedirs("output", exist_ok=True)
    with open(f"output/m5_completion_{int(datetime.now().timestamp())}.json", 'w') as f:
        json.dump(report, f, indent=2)
    
    print("="*60)
    
    return ready_for_optimization

if __name__ == "__main__":
    success = check_m5_completion()
    exit(0 if success else 1) 