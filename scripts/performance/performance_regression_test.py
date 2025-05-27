#!/usr/bin/env python3
"""
M3阶段性能回归测试
Performance Regression Test for M3 Phase

用途：
- PR中自动运行性能测试
- 检测性能回归（>10%的延迟增加）
- 生成性能对比报告
"""

import json
import time
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from scripts.performance_profiler import PerformanceProfiler


class PerformanceRegressionTest:
    """性能回归测试器"""
    
    def __init__(self, baseline_file: str = "output/m3_performance_baseline.json"):
        self.baseline_file = baseline_file
        self.baseline = self._load_baseline()
        self.profiler = PerformanceProfiler()
        
    def _load_baseline(self) -> Optional[Dict[str, Any]]:
        """加载性能基线"""
        try:
            if Path(self.baseline_file).exists():
                with open(self.baseline_file, 'r') as f:
                    baseline = json.load(f)
                print(f"✅ 加载基线: P95={baseline['latency_stats']['p95_ms']:.1f}ms")
                return baseline
            else:
                print(f"⚠️  基线文件不存在: {self.baseline_file}")
                return None
        except Exception as e:
            print(f"❌ 加载基线失败: {e}")
            return None
    
    def run_regression_test(self, test_duration: int = 120) -> Dict[str, Any]:
        """
        运行性能回归测试
        
        Args:
            test_duration: 测试时长（秒）
            
        Returns:
            测试结果和对比分析
        """
        print(f"🧪 开始性能回归测试 - {test_duration}秒")
        
        # 运行当前版本的性能测试
        current_results = self.profiler.dry_run_trading_loop(test_duration)
        
        if not self.baseline:
            print("⚠️  没有基线数据，仅记录当前性能")
            return {
                "status": "no_baseline",
                "current": current_results,
                "regression_detected": False
            }
        
        # 性能对比分析
        comparison = self._compare_performance(current_results)
        
        # 生成测试报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "status": "completed",
            "baseline": self.baseline,
            "current": current_results,
            "comparison": comparison,
            "regression_detected": comparison["regression_detected"]
        }
        
        # 保存测试报告
        report_file = f"output/regression_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # 输出结果
        self._print_regression_report(comparison)
        
        return report
    
    def _compare_performance(self, current: Dict[str, Any]) -> Dict[str, Any]:
        """对比性能数据"""
        baseline_p95 = self.baseline["latency_stats"]["p95_ms"]
        current_p95 = current["latency_stats"]["p95_ms"]
        
        baseline_throughput = self.baseline["throughput_cps"]
        current_throughput = current["throughput_cps"]
        
        # 计算变化百分比
        p95_change = ((current_p95 - baseline_p95) / baseline_p95) * 100
        throughput_change = ((current_throughput - baseline_throughput) / baseline_throughput) * 100
        
        # 判断是否回归
        regression_detected = False
        issues = []
        
        # P95延迟回归检测（超过10%认为回归）
        if p95_change > 10:
            regression_detected = True
            issues.append(f"P95延迟增加 {p95_change:.1f}%")
        
        # 吞吐量回归检测（下降超过15%认为回归）
        if throughput_change < -15:
            regression_detected = True
            issues.append(f"吞吐量下降 {abs(throughput_change):.1f}%")
        
        return {
            "regression_detected": regression_detected,
            "issues": issues,
            "metrics": {
                "p95_latency": {
                    "baseline_ms": baseline_p95,
                    "current_ms": current_p95,
                    "change_percent": p95_change
                },
                "throughput": {
                    "baseline_cps": baseline_throughput,
                    "current_cps": current_throughput,
                    "change_percent": throughput_change
                }
            }
        }
    
    def _print_regression_report(self, comparison: Dict[str, Any]):
        """打印回归测试报告"""
        print("\n" + "="*60)
        print("🎯 M3性能回归测试报告")
        print("="*60)
        
        metrics = comparison["metrics"]
        
        # P95延迟对比
        p95_baseline = metrics["p95_latency"]["baseline_ms"]
        p95_current = metrics["p95_latency"]["current_ms"]
        p95_change = metrics["p95_latency"]["change_percent"]
        
        print(f"📊 P95延迟对比:")
        print(f"   基线:   {p95_baseline:.1f}ms")
        print(f"   当前:   {p95_current:.1f}ms")
        print(f"   变化:   {p95_change:+.1f}% {'❌' if p95_change > 10 else '✅'}")
        
        # 吞吐量对比
        tp_baseline = metrics["throughput"]["baseline_cps"]
        tp_current = metrics["throughput"]["current_cps"]
        tp_change = metrics["throughput"]["change_percent"]
        
        print(f"\n🚀 吞吐量对比:")
        print(f"   基线:   {tp_baseline:.2f} cycles/sec")
        print(f"   当前:   {tp_current:.2f} cycles/sec")
        print(f"   变化:   {tp_change:+.1f}% {'❌' if tp_change < -15 else '✅'}")
        
        # 回归检测结果
        print(f"\n🔍 回归检测: {'❌ 检测到回归' if comparison['regression_detected'] else '✅ 无回归'}")
        
        if comparison["issues"]:
            print("⚠️  发现的问题:")
            for issue in comparison["issues"]:
                print(f"   - {issue}")
        
        print("="*60)


def main():
    """主函数 - 性能回归测试入口"""
    if len(sys.argv) > 1:
        test_duration = int(sys.argv[1])
    else:
        test_duration = 120  # 默认2分钟
    
    print("🧪 M3性能回归测试启动")
    
    # 创建测试器
    tester = PerformanceRegressionTest()
    
    # 运行回归测试
    report = tester.run_regression_test(test_duration)
    
    # 退出码：有回归则返回1，无回归返回0
    exit_code = 1 if report.get("regression_detected", False) else 0
    
    if exit_code == 1:
        print("\n❌ 性能回归检测：测试失败")
        print("💡 建议: 检查代码变更，优化性能瓶颈")
    else:
        print("\n✅ 性能回归检测：测试通过")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main() 