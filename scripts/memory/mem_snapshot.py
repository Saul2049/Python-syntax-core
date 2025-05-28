#!/usr/bin/env python3
"""
内存快照工具 - M5阶段
Memory Snapshot Tool for M5 Phase

用途：
- tracemalloc深度分析
- 内存泄漏检测
- 对象分配热点追踪
"""

import tracemalloc
import psutil
import os
import sys
import json
import time
import argparse
from typing import Dict, List, Any
from datetime import datetime
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class MemorySnapshot:
    """内存快照分析器"""

    def __init__(self, top_count: int = 20):
        self.top_count = top_count
        self.process = psutil.Process()
        self.snapshots = []
        self.logger = logging.getLogger(__name__)

    def start_tracing(self):
        """启动内存追踪"""
        if not tracemalloc.is_tracing():
            tracemalloc.start(25)  # 追踪最多25层调用栈
            self.logger.info("✅ tracemalloc追踪已启动")
        else:
            self.logger.info("⚠️ tracemalloc已在运行")

    def take_snapshot(self) -> Dict[str, Any]:
        """拍摄内存快照"""
        try:
            # 强制GC确保准确性
            import gc

            gc.collect()

            # tracemalloc快照
            if tracemalloc.is_tracing():
                snapshot = tracemalloc.take_snapshot()
                top_stats = snapshot.statistics("lineno")
            else:
                top_stats = []

            # 系统内存信息
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()

            # 文件描述符
            try:
                num_fds = self.process.num_fds()
            except AttributeError:
                # Windows不支持num_fds
                num_fds = len(self.process.open_files())

            # GC统计
            gc_counts = gc.get_count()

            snapshot_data = {
                "timestamp": datetime.now().isoformat(),
                "memory": {
                    "rss_bytes": memory_info.rss,
                    "vms_bytes": memory_info.vms,
                    "percent": memory_percent,
                    "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                },
                "gc_stats": {
                    "gen0_count": gc_counts[0],
                    "gen1_count": gc_counts[1],
                    "gen2_count": gc_counts[2],
                },
                "file_descriptors": num_fds,
                "top_allocations": [],
            }

            # 解析top分配
            for index, stat in enumerate(top_stats[: self.top_count]):
                allocation = {
                    "rank": index + 1,
                    "size_bytes": stat.size,
                    "size_mb": round(stat.size / 1024 / 1024, 3),
                    "count": stat.count,
                    "traceback": [],
                }

                # 添加调用栈信息
                for frame in stat.traceback:
                    allocation["traceback"].append(
                        {"filename": frame.filename, "lineno": frame.lineno}
                    )

                snapshot_data["top_allocations"].append(allocation)

            self.snapshots.append(snapshot_data)

            self.logger.info(
                f"📸 快照完成: RSS={snapshot_data['memory']['rss_mb']}MB, "
                f"FDs={num_fds}, Top分配={len(snapshot_data['top_allocations'])}"
            )

            return snapshot_data

        except Exception as e:
            self.logger.error(f"❌ 快照失败: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def compare_snapshots(self, snap1: Dict[str, Any], snap2: Dict[str, Any]) -> Dict[str, Any]:
        """比较两个快照"""
        if "error" in snap1 or "error" in snap2:
            return {"error": "Cannot compare snapshots with errors"}

        memory_diff = {
            "rss_change_mb": snap2["memory"]["rss_mb"] - snap1["memory"]["rss_mb"],
            "fd_change": snap2["file_descriptors"] - snap1["file_descriptors"],
            "gc_gen0_change": snap2["gc_stats"]["gen0_count"] - snap1["gc_stats"]["gen0_count"],
            "time_elapsed": snap2["timestamp"],
        }

        return memory_diff

    def detect_leaks(self, min_snapshots: int = 3) -> List[Dict[str, Any]]:
        """检测内存泄漏模式"""
        if len(self.snapshots) < min_snapshots:
            return []

        leaks = []

        # 检查RSS增长趋势
        rss_values = [s["memory"]["rss_mb"] for s in self.snapshots if "error" not in s]
        if len(rss_values) >= 3:
            # 简单的线性增长检测
            growth_rate = (rss_values[-1] - rss_values[0]) / len(rss_values)
            if growth_rate > 1.0:  # 每快照增长>1MB
                leaks.append(
                    {
                        "type": "rss_growth",
                        "growth_rate_mb_per_snapshot": round(growth_rate, 2),
                        "severity": "high" if growth_rate > 5 else "medium",
                    }
                )

        # 检查FD泄漏
        fd_values = [s["file_descriptors"] for s in self.snapshots if "error" not in s]
        if len(fd_values) >= 3:
            fd_growth = (fd_values[-1] - fd_values[0]) / len(fd_values)
            if fd_growth > 2:  # 每快照增长>2个FD
                leaks.append(
                    {
                        "type": "fd_leak",
                        "growth_rate_fds_per_snapshot": round(fd_growth, 1),
                        "severity": "high" if fd_growth > 10 else "medium",
                    }
                )

        return leaks

    def generate_report(self) -> Dict[str, Any]:
        """生成分析报告"""
        if not self.snapshots:
            return {"error": "No snapshots available"}

        valid_snapshots = [s for s in self.snapshots if "error" not in s]

        if not valid_snapshots:
            return {"error": "No valid snapshots"}

        # 基本统计
        rss_values = [s["memory"]["rss_mb"] for s in valid_snapshots]
        fd_values = [s["file_descriptors"] for s in valid_snapshots]

        report = {
            "summary": {
                "total_snapshots": len(self.snapshots),
                "valid_snapshots": len(valid_snapshots),
                "time_span": valid_snapshots[-1]["timestamp"] if valid_snapshots else None,
                "memory_stats": {
                    "min_rss_mb": min(rss_values),
                    "max_rss_mb": max(rss_values),
                    "avg_rss_mb": round(sum(rss_values) / len(rss_values), 2),
                    "total_growth_mb": rss_values[-1] - rss_values[0],
                },
                "fd_stats": {
                    "min_fds": min(fd_values),
                    "max_fds": max(fd_values),
                    "avg_fds": round(sum(fd_values) / len(fd_values), 1),
                    "total_growth": fd_values[-1] - fd_values[0],
                },
            },
            "leak_detection": self.detect_leaks(),
            "snapshots": valid_snapshots,
        }

        return report

    def save_report(self, filename: str):
        """保存报告到文件"""
        report = self.generate_report()

        with open(filename, "w") as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info(f"💾 报告已保存: {filename}")

        # 打印摘要
        if "summary" in report:
            summary = report["summary"]
            print("\n" + "=" * 60)
            print("📊 内存快照分析报告")
            print("=" * 60)
            print(f"📸 快照数量: {summary['valid_snapshots']}")
            print(
                f"🧠 内存范围: {summary['memory_stats']['min_rss_mb']:.1f} - {summary['memory_stats']['max_rss_mb']:.1f} MB"
            )
            print(f"📈 内存增长: {summary['memory_stats']['total_growth_mb']:+.1f} MB")
            print(f"🔗 FD范围: {summary['fd_stats']['min_fds']} - {summary['fd_stats']['max_fds']}")
            print(f"📈 FD变化: {summary['fd_stats']['total_growth']:+d}")

            # 泄漏警告
            leaks = report["leak_detection"]
            if leaks:
                print("\n⚠️ 检测到潜在泄漏:")
                for leak in leaks:
                    print(f"   {leak['type']}: {leak}")
            else:
                print("\n✅ 未检测到明显内存泄漏")

            print("=" * 60)


async def continuous_monitoring(duration_minutes: int = 60, interval_seconds: int = 60):
    """持续监控模式"""
    snapshot_tool = MemorySnapshot()
    snapshot_tool.start_tracing()

    print(f"🔄 开始连续监控 {duration_minutes} 分钟，间隔 {interval_seconds} 秒")

    end_time = time.time() + (duration_minutes * 60)

    while time.time() < end_time:
        snapshot_tool.take_snapshot()

        # 检查是否有泄漏迹象
        leaks = snapshot_tool.detect_leaks(min_snapshots=2)
        if leaks:
            for leak in leaks:
                if leak["severity"] == "high":
                    print(f"🚨 高危泄漏警告: {leak}")

        await asyncio.sleep(interval_seconds)

    # 生成最终报告
    timestamp = int(time.time())
    report_file = f"output/mem_snapshot_{timestamp}.json"
    os.makedirs("output", exist_ok=True)
    snapshot_tool.save_report(report_file)

    return report_file


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="内存快照分析工具")
    parser.add_argument("--top", type=int, default=20, help="显示top N分配")
    parser.add_argument("--save", action="store_true", help="保存快照到文件")
    parser.add_argument("--continuous", type=int, help="连续监控分钟数")
    parser.add_argument("--interval", type=int, default=60, help="连续监控间隔秒数")

    args = parser.parse_args()

    # 配置日志
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    print("📸 M5内存快照工具")

    if args.continuous:
        # 连续监控模式
        import asyncio

        report_file = asyncio.run(continuous_monitoring(args.continuous, args.interval))
        print(f"✅ 连续监控完成，报告: {report_file}")
    else:
        # 单次快照模式
        snapshot_tool = MemorySnapshot(args.top)
        snapshot_tool.start_tracing()

        time.sleep(2)  # 等待一点时间收集数据
        snapshot_data = snapshot_tool.take_snapshot()

        if args.save:
            timestamp = int(time.time())
            filename = f"output/mem_snapshot_{timestamp}.json"
            os.makedirs("output", exist_ok=True)
            snapshot_tool.save_report(filename)
        else:
            # 打印到控制台
            print(json.dumps(snapshot_data, indent=2, default=str))


if __name__ == "__main__":
    main()
