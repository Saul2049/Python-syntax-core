#!/usr/bin/env python3
"""
内存基线采集器 - M5阶段
Memory Baseline Collector for M5 Phase

用途：
- 30分钟内存基线采样
- 建立性能基准
- 为后续优化提供对比
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict

import psutil

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from scripts.memory.gc_profiler import GCProfiler
from scripts.memory.mem_snapshot import MemorySnapshot


class MemoryBaseline:
    """内存基线采集器"""

    def __init__(self, sample_interval: int = 60):
        self.sample_interval = sample_interval
        self.process = psutil.Process()
        self.baseline_data = {
            "metadata": {
                "start_time": None,
                "end_time": None,
                "duration_seconds": 0,
                "sample_interval": sample_interval,
                "python_version": sys.version,
                "platform": os.name,
            },
            "memory_samples": [],
            "gc_events": [],
            "process_stats": [],
            "system_stats": [],
        }

        self.memory_snapshot = MemorySnapshot()
        self.gc_profiler = GCProfiler(enable_prometheus=False)
        self.logger = logging.getLogger(__name__)

    async def collect_baseline(self, duration_seconds: int):
        """采集内存基线数据"""
        self.baseline_data["metadata"]["start_time"] = datetime.now().isoformat()
        self.baseline_data["metadata"]["duration_seconds"] = duration_seconds

        self.logger.info(f"🚀 开始采集内存基线 ({duration_seconds}秒)")

        # 启动内存和GC监控
        self.memory_snapshot.start_tracing()
        self.gc_profiler.start_monitoring()

        start_time = time.time()
        end_time = start_time + duration_seconds
        sample_count = 0

        try:
            while time.time() < end_time:
                # 采集当前样本
                sample = await self._collect_sample()
                sample["sample_id"] = sample_count
                sample["elapsed_seconds"] = time.time() - start_time

                self.baseline_data["memory_samples"].append(sample)

                # 进度报告
                progress = (time.time() - start_time) / duration_seconds * 100
                self.logger.info(f"📊 采样进度: {progress:.1f}% (样本 {sample_count+1})")

                sample_count += 1

                # 等待下一个采样间隔
                await asyncio.sleep(self.sample_interval)

            # 收集最终统计
            await self._finalize_baseline()

        except Exception as e:
            self.logger.error(f"❌ 基线采集错误: {e}")
            raise
        finally:
            # 停止监控
            self.gc_profiler.stop_monitoring()

        self.baseline_data["metadata"]["end_time"] = datetime.now().isoformat()
        self.logger.info(f"✅ 基线采集完成，共 {sample_count} 个样本")

        return self.baseline_data

    async def _collect_sample(self) -> Dict[str, Any]:
        """采集单个内存样本"""
        # 内存快照
        memory_snapshot = self.memory_snapshot.take_snapshot()

        # 进程统计
        try:
            process_info = {
                "cpu_percent": self.process.cpu_percent(),
                "memory_info": self.process.memory_info()._asdict(),
                "memory_percent": self.process.memory_percent(),
                "num_threads": self.process.num_threads(),
                "connections": len(self.process.connections()),
            }

            # 尝试获取文件描述符数量
            try:
                process_info["num_fds"] = self.process.num_fds()
            except AttributeError:
                # Windows不支持
                process_info["num_fds"] = len(self.process.open_files())

        except Exception as e:
            self.logger.warning(f"⚠️ 进程信息采集失败: {e}")
            process_info = {"error": str(e)}

        # 系统统计
        system_info = {
            "cpu_percent": psutil.cpu_percent(),
            "memory": psutil.virtual_memory()._asdict(),
            "swap": psutil.swap_memory()._asdict(),
            "disk_usage": psutil.disk_usage("/")._asdict() if os.name != "nt" else None,
        }

        return {
            "timestamp": datetime.now().isoformat(),
            "memory_snapshot": memory_snapshot,
            "process_info": process_info,
            "system_info": system_info,
        }

    async def _finalize_baseline(self):
        """完成基线数据收集"""
        # 获取GC统计
        gc_stats = self.gc_profiler.get_statistics()
        self.baseline_data["gc_events"] = gc_stats

        # 计算基线统计
        memory_samples = [
            s
            for s in self.baseline_data["memory_samples"]
            if "error" not in s.get("memory_snapshot", {})
        ]

        if memory_samples:
            rss_values = []
            vms_values = []
            cpu_values = []

            for sample in memory_samples:
                if "memory_snapshot" in sample and "memory" in sample["memory_snapshot"]:
                    mem = sample["memory_snapshot"]["memory"]
                    rss_values.append(mem["rss_mb"])
                    vms_values.append(mem.get("vms_bytes", 0) / 1024 / 1024)

                if "process_info" in sample and "cpu_percent" in sample["process_info"]:
                    cpu_values.append(sample["process_info"]["cpu_percent"])

            # 基线统计
            baseline_stats = {
                "memory_rss": {
                    "min_mb": min(rss_values) if rss_values else 0,
                    "max_mb": max(rss_values) if rss_values else 0,
                    "avg_mb": sum(rss_values) / len(rss_values) if rss_values else 0,
                    "p50_mb": sorted(rss_values)[len(rss_values) // 2] if rss_values else 0,
                    "p95_mb": sorted(rss_values)[int(len(rss_values) * 0.95)] if rss_values else 0,
                },
                "memory_vms": {
                    "min_mb": min(vms_values) if vms_values else 0,
                    "max_mb": max(vms_values) if vms_values else 0,
                    "avg_mb": sum(vms_values) / len(vms_values) if vms_values else 0,
                },
                "cpu_usage": {
                    "min_percent": min(cpu_values) if cpu_values else 0,
                    "max_percent": max(cpu_values) if cpu_values else 0,
                    "avg_percent": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                },
                "sample_count": len(memory_samples),
                "gc_summary": {
                    "total_collections": gc_stats.get("total_gc_events", 0),
                    "avg_pause_ms": gc_stats.get("avg_pause_time", 0) * 1000,
                    "gc_frequency": gc_stats.get("gc_frequency", 0),
                },
            }

            self.baseline_data["baseline_stats"] = baseline_stats

    def save_baseline(self, filename: str):
        """保存基线数据"""
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, "w") as f:
            json.dump(self.baseline_data, f, indent=2, default=str)

        self.logger.info(f"💾 基线数据已保存: {filename}")

        # 打印基线摘要
        if "baseline_stats" in self.baseline_data:
            self._print_baseline_summary()

    def _print_baseline_summary(self):
        """打印基线摘要"""
        stats = self.baseline_data["baseline_stats"]

        print("\n" + "=" * 60)
        print("📊 M5内存基线摘要")
        print("=" * 60)
        print(f"⏱️ 采样时长: {self.baseline_data['metadata']['duration_seconds']}秒")
        print(f"📸 样本数量: {stats['sample_count']}")

        print("\n🧠 内存使用 (RSS):")
        rss = stats["memory_rss"]
        print(f"   范围: {rss['min_mb']:.1f} - {rss['max_mb']:.1f} MB")
        print(f"   平均: {rss['avg_mb']:.1f} MB")
        print(f"   P50:  {rss['p50_mb']:.1f} MB")
        print(f"   P95:  {rss['p95_mb']:.1f} MB")

        print("\n🖥️ CPU使用:")
        cpu = stats["cpu_usage"]
        print(f"   范围: {cpu['min_percent']:.1f}% - {cpu['max_percent']:.1f}%")
        print(f"   平均: {cpu['avg_percent']:.1f}%")

        print("\n🗑️ GC统计:")
        gc_summary = stats["gc_summary"]
        print(f"   总回收: {gc_summary['total_collections']}次")
        print(f"   平均暂停: {gc_summary['avg_pause_ms']:.2f}ms")
        print(f"   回收频率: {gc_summary['gc_frequency']:.2f}/秒")

        print("=" * 60)
        print("✅ 基线数据可用于后续内存优化对比")
        print("=" * 60)


def compare_with_baseline(current_data: Dict[str, Any], baseline_file: str) -> Dict[str, Any]:
    """与基线数据对比"""
    try:
        with open(baseline_file, "r") as f:
            baseline = json.load(f)

        if "baseline_stats" not in baseline:
            return {"error": "Invalid baseline file"}

        baseline_stats = baseline["baseline_stats"]
        current_stats = current_data.get("baseline_stats", {})

        comparison = {
            "memory_comparison": {},
            "cpu_comparison": {},
            "gc_comparison": {},
            "regression_detected": False,
            "improvements": [],
            "regressions": [],
        }

        # 内存对比
        if "memory_rss" in current_stats and "memory_rss" in baseline_stats:
            current_rss = current_stats["memory_rss"]
            baseline_rss = baseline_stats["memory_rss"]

            avg_change = (
                (current_rss["avg_mb"] - baseline_rss["avg_mb"]) / baseline_rss["avg_mb"]
            ) * 100
            p95_change = (
                (current_rss["p95_mb"] - baseline_rss["p95_mb"]) / baseline_rss["p95_mb"]
            ) * 100

            comparison["memory_comparison"] = {
                "avg_mb_change": avg_change,
                "p95_mb_change": p95_change,
                "current_avg": current_rss["avg_mb"],
                "baseline_avg": baseline_rss["avg_mb"],
                "current_p95": current_rss["p95_mb"],
                "baseline_p95": baseline_rss["p95_mb"],
            }

            # 回归检测
            if avg_change > 15:  # 平均内存增长>15%
                comparison["regressions"].append(f"内存使用增长 {avg_change:.1f}%")
                comparison["regression_detected"] = True
            elif avg_change < -5:  # 内存减少>5%
                comparison["improvements"].append(f"内存使用减少 {-avg_change:.1f}%")

        # CPU对比
        if "cpu_usage" in current_stats and "cpu_usage" in baseline_stats:
            current_cpu = current_stats["cpu_usage"]
            baseline_cpu = baseline_stats["cpu_usage"]

            cpu_change = (
                (current_cpu["avg_percent"] - baseline_cpu["avg_percent"])
                / baseline_cpu["avg_percent"]
            ) * 100

            comparison["cpu_comparison"] = {
                "avg_percent_change": cpu_change,
                "current_avg": current_cpu["avg_percent"],
                "baseline_avg": baseline_cpu["avg_percent"],
            }

            if cpu_change > 20:  # CPU使用增长>20%
                comparison["regressions"].append(f"CPU使用增长 {cpu_change:.1f}%")
                comparison["regression_detected"] = True

        return comparison

    except Exception as e:
        return {"error": f"Comparison failed: {e}"}


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="内存基线采集工具")
    parser.add_argument("--duration", type=int, default=1800, help="采集时长(秒，默认30分钟)")
    parser.add_argument("--interval", type=int, default=60, help="采样间隔(秒)")
    parser.add_argument("--save", required=True, help="保存基线文件路径")
    parser.add_argument("--compare", help="与指定基线文件对比")

    args = parser.parse_args()

    # 配置日志
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    print("📊 M5内存基线采集工具")
    print(f"⏱️ 采集时长: {args.duration}秒 ({args.duration//60}分钟)")
    print(f"📸 采样间隔: {args.interval}秒")

    try:
        # 创建基线采集器
        baseline = MemoryBaseline(args.interval)

        # 采集基线数据
        baseline_data = await baseline.collect_baseline(args.duration)

        # 保存基线
        baseline.save_baseline(args.save)

        # 对比（如果指定）
        if args.compare and os.path.exists(args.compare):
            print("\n🔍 与基线对比...")
            comparison = compare_with_baseline(baseline_data, args.compare)

            if "error" not in comparison:
                print(
                    f"📈 内存变化: {comparison['memory_comparison'].get('avg_mb_change', 0):+.1f}%"
                )
                print(
                    f"🖥️ CPU变化: {comparison['cpu_comparison'].get('avg_percent_change', 0):+.1f}%"
                )

                if comparison["regression_detected"]:
                    print("⚠️ 检测到性能回归:")
                    for regression in comparison["regressions"]:
                        print(f"   {regression}")

                if comparison["improvements"]:
                    print("✅ 检测到性能改进:")
                    for improvement in comparison["improvements"]:
                        print(f"   {improvement}")

        print(f"\n🎉 基线采集完成！文件保存至: {args.save}")

    except KeyboardInterrupt:
        print("\n🛑 用户中断")
    except Exception as e:
        print(f"❌ 基线采集失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
