#!/usr/bin/env python3
"""
W3 泄漏哨兵 - 连续泄漏监控
W3 Leak Sentinel - Continuous Leak Monitoring

目标: 连续6小时无内存泄漏
验收标准:
- 内存增长率 < 0.1 MB/min
- 文件描述符增长率 < 0.1 FD/min
- 清洁小时数 ≥ 6
"""

import asyncio
import gc
import os
import sys
import time
import json
import psutil
import logging
import argparse
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from scripts.memory.mem_snapshot import MemorySnapshot
from config.gc_settings import GCSettings


@dataclass
class LeakCheckpoint:
    """泄漏检查点"""

    timestamp: datetime
    rss_mb: float
    fd_count: int
    gc_gen0: int
    gc_gen1: int
    gc_gen2: int
    clean_hours: int


class W3LeakSentinel:
    """W3 泄漏哨兵"""

    def __init__(self, target_hours: int = 6):
        self.target_hours = target_hours
        self.check_interval = 300  # 5分钟检查间隔
        self.memory_snapshot = MemorySnapshot()
        self.process = psutil.Process()
        self.logger = logging.getLogger(__name__)

        # 泄漏阈值
        self.memory_leak_threshold = 0.1  # MB/min
        self.fd_leak_threshold = 0.1  # FD/min

        # 监控数据
        self.checkpoints: List[LeakCheckpoint] = []
        self.clean_hours_count = 0
        self.last_leak_detected = None

        # 统计
        self.start_time = None
        self.w3_status = {
            "started": False,
            "completed": False,
            "passed": False,
            "clean_hours": 0,
            "target_hours": target_hours,
            "last_leak": None,
            "current_streak": 0,
        }

    async def start_monitoring(self):
        """开始 W3 泄漏监控"""
        self.start_time = datetime.now()
        self.w3_status["started"] = True

        # 应用 W2 GC 配置
        GCSettings.apply_w2_optimal()

        self.logger.info(f"🔍 W3 泄漏哨兵启动")
        self.logger.info(f"🎯 目标: 连续{self.target_hours}小时无泄漏")
        self.logger.info(f"📊 监控间隔: {self.check_interval}秒")

        # 启动内存追踪
        self.memory_snapshot.start_tracing()

        # 记录初始状态
        await self._take_checkpoint("初始状态")

        try:
            while self.clean_hours_count < self.target_hours:
                await asyncio.sleep(self.check_interval)

                # 执行泄漏检查
                leak_detected = await self._check_for_leaks()

                if leak_detected:
                    self.logger.warning(f"🚨 检测到泄漏，重置清洁小时计数")
                    self.clean_hours_count = 0
                    self.last_leak_detected = datetime.now()
                    self.w3_status["last_leak"] = datetime.now().isoformat()
                    self.w3_status["current_streak"] = 0
                else:
                    # 更新清洁时间
                    elapsed_hours = (
                        datetime.now() - (self.last_leak_detected or self.start_time)
                    ).total_seconds() / 3600
                    self.clean_hours_count = int(elapsed_hours)
                    self.w3_status["clean_hours"] = self.clean_hours_count
                    self.w3_status["current_streak"] = self.clean_hours_count

                self.logger.info(f"⏰ 清洁小时数: {self.clean_hours_count}/{self.target_hours}")

            # W3 完成
            self.w3_status["completed"] = True
            self.w3_status["passed"] = True
            self.logger.info(f"🎉 W3 验收通过！连续{self.target_hours}小时无泄漏")

        except Exception as e:
            self.logger.error(f"❌ W3 监控异常: {e}")
            self.w3_status["passed"] = False
            raise

    async def _take_checkpoint(self, reason: str = "定期检查"):
        """记录检查点"""
        snapshot = self.memory_snapshot.take_snapshot()

        if "error" in snapshot:
            self.logger.error(f"❌ 快照失败: {snapshot['error']}")
            return

        checkpoint = LeakCheckpoint(
            timestamp=datetime.now(),
            rss_mb=snapshot["memory"]["rss_mb"],
            fd_count=snapshot["file_descriptors"],
            gc_gen0=snapshot["gc_stats"]["gen0_count"],
            gc_gen1=snapshot["gc_stats"]["gen1_count"],
            gc_gen2=snapshot["gc_stats"]["gen2_count"],
            clean_hours=self.clean_hours_count,
        )

        self.checkpoints.append(checkpoint)

        self.logger.info(
            f"📍 检查点 ({reason}): RSS={checkpoint.rss_mb}MB, "
            f"FDs={checkpoint.fd_count}, 清洁={checkpoint.clean_hours}h"
        )

    async def _check_for_leaks(self) -> bool:
        """检查是否存在泄漏"""
        await self._take_checkpoint()

        if len(self.checkpoints) < 2:
            return False

        # 分析最近的数据点
        window_size = min(6, len(self.checkpoints))  # 最近30分钟的数据
        recent_checkpoints = self.checkpoints[-window_size:]

        # 内存泄漏检查
        memory_leak = self._analyze_memory_trend(recent_checkpoints)
        fd_leak = self._analyze_fd_trend(recent_checkpoints)

        leak_detected = memory_leak or fd_leak

        if leak_detected:
            self.logger.warning("🚨 泄漏检测结果:")
            if memory_leak:
                self.logger.warning(f"  • 内存泄漏: 增长率超过 {self.memory_leak_threshold} MB/min")
            if fd_leak:
                self.logger.warning(f"  • FD泄漏: 增长率超过 {self.fd_leak_threshold} FD/min")

        return leak_detected

    def _analyze_memory_trend(self, checkpoints: List[LeakCheckpoint]) -> bool:
        """分析内存增长趋势"""
        if len(checkpoints) < 2:
            return False

        # 计算内存增长率 (MB/min)
        first = checkpoints[0]
        last = checkpoints[-1]

        time_diff_minutes = (last.timestamp - first.timestamp).total_seconds() / 60
        memory_diff_mb = last.rss_mb - first.rss_mb

        if time_diff_minutes > 0:
            growth_rate = memory_diff_mb / time_diff_minutes

            self.logger.debug(
                f"📊 内存增长率: {growth_rate:.3f} MB/min " f"(阈值: {self.memory_leak_threshold})"
            )

            return growth_rate > self.memory_leak_threshold

        return False

    def _analyze_fd_trend(self, checkpoints: List[LeakCheckpoint]) -> bool:
        """分析文件描述符增长趋势"""
        if len(checkpoints) < 2:
            return False

        # 计算FD增长率 (FD/min)
        first = checkpoints[0]
        last = checkpoints[-1]

        time_diff_minutes = (last.timestamp - first.timestamp).total_seconds() / 60
        fd_diff = last.fd_count - first.fd_count

        if time_diff_minutes > 0:
            growth_rate = fd_diff / time_diff_minutes

            self.logger.debug(
                f"📊 FD增长率: {growth_rate:.3f} FD/min " f"(阈值: {self.fd_leak_threshold})"
            )

            return growth_rate > self.fd_leak_threshold

        return False

    def generate_w3_report(self) -> Dict:
        """生成 W3 验收报告"""
        current_time = datetime.now()
        elapsed_hours = (
            (current_time - self.start_time).total_seconds() / 3600 if self.start_time else 0
        )

        # W3 验收检查
        w3_passed = self.w3_status["completed"] and self.clean_hours_count >= self.target_hours

        report = {
            "w3_acceptance": {
                "passed": w3_passed,
                "target_clean_hours": self.target_hours,
                "achieved_clean_hours": self.clean_hours_count,
                "completion_status": self.w3_status["completed"],
            },
            "monitoring_summary": {
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "elapsed_hours": round(elapsed_hours, 2),
                "total_checkpoints": len(self.checkpoints),
                "leak_threshold_memory_mb_per_min": self.memory_leak_threshold,
                "leak_threshold_fd_per_min": self.fd_leak_threshold,
            },
            "leak_analysis": {
                "last_leak_detected": self.w3_status.get("last_leak"),
                "current_clean_streak_hours": self.clean_hours_count,
                "total_leak_events": self._count_leak_events(),
            },
            "memory_trend": self._analyze_overall_memory_trend(),
            "checkpoints": [
                {
                    "timestamp": cp.timestamp.isoformat(),
                    "rss_mb": cp.rss_mb,
                    "fd_count": cp.fd_count,
                    "clean_hours": cp.clean_hours,
                }
                for cp in self.checkpoints[-20:]  # 最近20个检查点
            ],
        }

        return report

    def _count_leak_events(self) -> int:
        """统计泄漏事件数量"""
        # 简化版本：基于清洁小时数重置次数
        return len([cp for cp in self.checkpoints if cp.clean_hours == 0]) - 1

    def _analyze_overall_memory_trend(self) -> Dict:
        """分析整体内存趋势"""
        if len(self.checkpoints) < 2:
            return {"status": "insufficient_data"}

        first = self.checkpoints[0]
        last = self.checkpoints[-1]

        total_time_hours = (last.timestamp - first.timestamp).total_seconds() / 3600
        total_memory_change = last.rss_mb - first.rss_mb

        return {
            "total_memory_change_mb": round(total_memory_change, 2),
            "total_time_hours": round(total_time_hours, 2),
            "average_growth_rate_mb_per_hour": (
                round(total_memory_change / total_time_hours, 3) if total_time_hours > 0 else 0
            ),
            "fd_change": last.fd_count - first.fd_count,
            "status": "stable" if abs(total_memory_change) < 5 else "concerning",
        }

    def save_report(self, filename: str):
        """保存 W3 报告"""
        report = self.generate_w3_report()

        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else ".", exist_ok=True)
        with open(filename, "w") as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info(f"💾 W3 报告已保存: {filename}")
        self._print_w3_summary(report)

    def _print_w3_summary(self, report: Dict):
        """打印 W3 验收总结"""
        print("\n" + "=" * 60)
        print("🔍 W3 泄漏哨兵验收报告")
        print("=" * 60)

        acceptance = report["w3_acceptance"]
        monitoring = report["monitoring_summary"]
        leak_analysis = report["leak_analysis"]

        print(f"🎯 验收目标: 连续{acceptance['target_clean_hours']}小时无泄漏")
        print(f"⏰ 运行时长: {monitoring['elapsed_hours']:.1f}小时")
        print(
            f"🕛 清洁小时: {acceptance['achieved_clean_hours']}/{acceptance['target_clean_hours']}"
        )
        print(f"📊 检查次数: {monitoring['total_checkpoints']}次")

        print(f"\n📈 泄漏阈值:")
        print(f"   内存: ≤{monitoring['leak_threshold_memory_mb_per_min']} MB/min")
        print(f"   文件描述符: ≤{monitoring['leak_threshold_fd_per_min']} FD/min")

        print(f"\n🔍 泄漏统计:")
        print(f"   当前连续清洁: {leak_analysis['current_clean_streak_hours']}小时")
        print(f"   总泄漏事件: {leak_analysis['total_leak_events']}次")

        print(f"\n🎯 W3 验收结果: {'✅ PASS' if acceptance['passed'] else '❌ FAIL'}")

        if acceptance["passed"]:
            print(f"\n🎉 W3 泄漏哨兵验收通过！可以进入W4压力测试")
        else:
            remaining = acceptance["target_clean_hours"] - acceptance["achieved_clean_hours"]
            print(f"\n⚠️ 还需要 {remaining} 小时无泄漏才能通过验收")

        print("=" * 60)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="W3 泄漏哨兵")
    parser.add_argument("--target-hours", type=int, default=6, help="目标清洁小时数 (默认: 6)")
    parser.add_argument("--check-interval", type=int, default=300, help="检查间隔秒数 (默认: 300)")
    parser.add_argument(
        "--memory-threshold", type=float, default=0.1, help="内存泄漏阈值 MB/min (默认: 0.1)"
    )
    parser.add_argument(
        "--fd-threshold", type=float, default=0.1, help="FD泄漏阈值 FD/min (默认: 0.1)"
    )

    args = parser.parse_args()

    # 配置日志
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    print("🔍 W3 泄漏哨兵启动")
    print(f"🎯 目标: 连续{args.target_hours}小时无内存泄漏")

    # 创建哨兵
    sentinel = W3LeakSentinel(target_hours=args.target_hours)
    sentinel.check_interval = args.check_interval
    sentinel.memory_leak_threshold = args.memory_threshold
    sentinel.fd_leak_threshold = args.fd_threshold

    try:
        # 开始监控
        await sentinel.start_monitoring()

        # 生成报告
        timestamp = int(time.time())
        report_file = f"output/w3_leak_sentinel_{timestamp}.json"
        os.makedirs("output", exist_ok=True)
        sentinel.save_report(report_file)

        return sentinel.w3_status["passed"]

    except KeyboardInterrupt:
        print("\n⏸️ 用户中断监控")
        sentinel.logger.info("监控被用户中断")

        # 保存中间报告
        timestamp = int(time.time())
        report_file = f"output/w3_leak_sentinel_interrupted_{timestamp}.json"
        os.makedirs("output", exist_ok=True)
        sentinel.save_report(report_file)

        return False
    except Exception as e:
        print(f"❌ W3 监控失败: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
