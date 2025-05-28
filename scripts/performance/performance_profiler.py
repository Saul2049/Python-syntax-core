#!/usr/bin/env python3
"""
M3阶段性能剖析器
Performance Profiler for M3 Phase

用途：
- 生成FlameGraph定位CPU热点
- 建立性能基线
- 监控关键指标
"""

import time
import threading
from datetime import datetime
from typing import Dict, Any
import subprocess
import os

from src.core.trading_engine import TradingEngine
from src.monitoring.metrics_collector import get_metrics_collector


class PerformanceProfiler:
    """M3阶段性能剖析器"""

    def __init__(self):
        self.metrics = get_metrics_collector()
        self.results = {}

    def dry_run_trading_loop(self, duration_seconds: int = 300) -> Dict[str, Any]:
        """
        执行干跑交易循环进行性能剖析

        Args:
            duration_seconds: 运行时长（秒）

        Returns:
            性能统计结果
        """
        print(f"🚀 开始M3性能剖析 - 干跑{duration_seconds}秒")

        # 初始化交易引擎
        engine = TradingEngine()

        # 记录开始时间
        start_time = time.time()
        cycles_completed = 0

        # 性能统计
        latencies = []

        while time.time() - start_time < duration_seconds:
            cycle_start = time.time()

            try:
                # 执行一个交易周期（干跑模式）
                success = engine.execute_trading_cycle(symbol="BTCUSDT", fast_win=7, slow_win=25)

                cycle_end = time.time()
                cycle_latency = cycle_end - cycle_start
                latencies.append(cycle_latency)

                if success:
                    cycles_completed += 1

                # 每10个周期报告一次进度
                if cycles_completed % 10 == 0:
                    avg_latency = sum(latencies[-10:]) / min(10, len(latencies))
                    print(
                        f"📈 已完成{cycles_completed}个周期，最近10次平均延迟: {avg_latency*1000:.1f}ms"
                    )

                # 控制频率，避免过度请求
                time.sleep(1)

            except Exception as e:
                print(f"⚠️  交易周期异常: {e}")
                continue

        # 计算统计结果
        total_time = time.time() - start_time

        if latencies:
            latencies.sort()
            p50 = latencies[len(latencies) // 2] * 1000
            p95 = latencies[int(len(latencies) * 0.95)] * 1000
            p99 = latencies[int(len(latencies) * 0.99)] * 1000
            avg = sum(latencies) / len(latencies) * 1000
        else:
            p50 = p95 = p99 = avg = 0

        results = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": total_time,
            "cycles_completed": cycles_completed,
            "throughput_cps": cycles_completed / total_time,
            "latency_stats": {
                "p50_ms": p50,
                "p95_ms": p95,
                "p99_ms": p99,
                "avg_ms": avg,
                "samples": len(latencies),
            },
        }

        print("\n🎯 M3性能基线结果:")
        print(f"   总时长: {total_time:.1f}秒")
        print(f"   完成周期: {cycles_completed}")
        print(f"   吞吐量: {results['throughput_cps']:.2f} cycles/sec")
        print(f"   P50延迟: {p50:.1f}ms")
        print(f"   P95延迟: {p95:.1f}ms")
        print(f"   P99延迟: {p99:.1f}ms")

        self.results = results
        return results

    def generate_flame_graph(self, duration_seconds: int = 60) -> str:
        """
        生成FlameGraph性能火焰图

        Args:
            duration_seconds: 采样时长

        Returns:
            FlameGraph文件路径
        """
        print(f"🔥 开始生成FlameGraph - 采样{duration_seconds}秒")

        # 输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        flame_file = f"output/flamegraph_{timestamp}.svg"

        # 确保输出目录存在
        os.makedirs("output", exist_ok=True)

        # 启动干跑进程
        import subprocess
        import signal

        try:
            # 启动性能剖析脚本
            target_script = f"""
import time
from scripts.performance_profiler import PerformanceProfiler
profiler = PerformanceProfiler()
profiler.dry_run_trading_loop({duration_seconds})
"""

            # 写入临时脚本
            with open("temp_profile_target.py", "w") as f:
                f.write(target_script)

            # 使用py-spy生成火焰图
            cmd = [
                "py-spy",
                "record",
                "-o",
                flame_file,
                "-r",
                "999",  # 高采样率
                "-d",
                str(duration_seconds),
                "--",
                "python",
                "temp_profile_target.py",
            ]

            print(f"🔍 执行采样命令: {' '.join(cmd)}")
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=duration_seconds + 30
            )

            if result.returncode == 0:
                print(f"✅ FlameGraph已生成: {flame_file}")

                # 清理临时文件
                if os.path.exists("temp_profile_target.py"):
                    os.remove("temp_profile_target.py")

                return flame_file
            else:
                print(f"❌ FlameGraph生成失败: {result.stderr}")
                return ""

        except subprocess.TimeoutExpired:
            print("⏰ 采样超时")
            return ""
        except Exception as e:
            print(f"❌ FlameGraph生成异常: {e}")
            return ""

    def save_baseline_metrics(self) -> bool:
        """保存性能基线指标"""
        if not self.results:
            print("❌ 没有性能结果可保存")
            return False

        try:
            # 保存到文件
            import json

            baseline_file = "output/m3_performance_baseline.json"

            with open(baseline_file, "w") as f:
                json.dump(self.results, f, indent=2)

            print(f"✅ 性能基线已保存: {baseline_file}")

            # 同时更新Prometheus指标（如果启用）
            if hasattr(self.metrics, "config") and self.metrics.config.enabled:
                p95_ms = self.results["latency_stats"]["p95_ms"]
                # 记录基线P95延迟
                print(f"📊 Prometheus基线指标: P95={p95_ms:.1f}ms")

            return True

        except Exception as e:
            print(f"❌ 保存基线失败: {e}")
            return False


def main():
    """主函数 - M3性能剖析入口"""
    print("🚀 M3阶段性能剖析启动")

    profiler = PerformanceProfiler()

    # 1. 快速基线测试 (60秒)
    print("\n📊 步骤1: 快速基线测试")
    profiler.dry_run_trading_loop(60)
    profiler.save_baseline_metrics()

    # 2. 生成FlameGraph (可选，如果有足够时间)
    generate_flame = input("\n🔥 是否生成FlameGraph? (y/N): ").lower().startswith("y")
    if generate_flame:
        print("\n🔥 步骤2: 生成FlameGraph")
        flame_file = profiler.generate_flame_graph(60)
        if flame_file:
            print(f"🎯 FlameGraph已保存: {flame_file}")

    print("\n🎉 M3性能剖析完成！")
    print("📋 下一步: 分析结果，开始算法优化")


if __name__ == "__main__":
    main()
