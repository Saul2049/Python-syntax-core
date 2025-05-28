#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M5 GC优化管理器 - W2实现
GC Optimizer for M5 Week 2

目标: GC暂停时间减少50%
"""

import asyncio
import gc
import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ..monitoring.metrics_collector import get_metrics_collector


@dataclass
class GCProfile:
    """GC性能配置文件"""

    thresholds: Tuple[int, int, int]
    name: str
    description: str
    expected_improvement: str


class GCOptimizer:
    """M5 GC优化管理器"""

    def __init__(self):
        self.metrics = get_metrics_collector()
        self.logger = logging.getLogger(__name__)
        self.original_thresholds = gc.get_threshold()
        self.monitoring_active = False
        self.pause_history = []

        # GC配置预设
        self.gc_profiles = [
            GCProfile((700, 10, 10), "default", "Python默认设置", "基线"),
            GCProfile((900, 15, 12), "conservative", "保守优化，减少Gen0频率", "减少30%暂停"),
            GCProfile((1200, 20, 15), "aggressive", "激进优化，大幅减少GC频率", "减少50%暂停"),
            GCProfile((600, 8, 8), "high_frequency", "高频交易优化", "减少单次暂停时间"),
        ]

        self.current_profile = None
        self.optimization_results = {}

    def install_gc_callbacks(self):
        """安装GC监控回调"""
        if self._gc_callback not in gc.callbacks:
            gc.callbacks.append(self._gc_callback)
            self.monitoring_active = True
            self.logger.info("✅ GC监控回调已安装")

    def remove_gc_callbacks(self):
        """移除GC监控回调"""
        if self._gc_callback in gc.callbacks:
            gc.callbacks.remove(self._gc_callback)
            self.monitoring_active = False
            self.logger.info("🛑 GC监控回调已移除")

    def _gc_callback(self, phase: str, info: Dict):
        """GC回调函数"""
        try:
            if phase == "start":
                if not hasattr(self, "_gc_start_time"):
                    self._gc_start_time = {}
                self._gc_start_time[info.get("generation", -1)] = time.time()

            elif phase == "stop":
                generation = info.get("generation", -1)
                collected = info.get("collected", 0)

                if hasattr(self, "_gc_start_time") and generation in self._gc_start_time:
                    pause_duration = time.time() - self._gc_start_time[generation]

                    # 记录暂停历史
                    self.pause_history.append(
                        {
                            "timestamp": time.time(),
                            "generation": generation,
                            "duration": pause_duration,
                            "collected": collected,
                            "profile": (
                                self.current_profile.name if self.current_profile else "unknown"
                            ),
                        }
                    )

                    # 保持历史记录在合理范围内
                    if len(self.pause_history) > 1000:
                        self.pause_history = self.pause_history[-800:]

                    # 更新Prometheus指标
                    self.metrics.record_gc_event(generation, pause_duration, collected)

                    # 记录长暂停
                    if pause_duration > 0.02:  # >20ms
                        self.logger.warning(
                            f"🗑️ 长GC暂停: Gen{generation} {pause_duration*1000:.1f}ms"
                        )

                    del self._gc_start_time[generation]

        except Exception as e:
            self.logger.error(f"❌ GC回调错误: {e}")

    def apply_profile(self, profile: GCProfile) -> bool:
        """应用GC配置"""
        try:
            self.logger.info(f"🔧 应用GC配置: {profile.name} - {profile.description}")

            # 设置新阈值
            gc.set_threshold(*profile.thresholds)

            # 禁用GC调试（生产优化）
            gc.set_debug(0)

            # 记录当前配置
            self.current_profile = profile

            # 清空暂停历史以获得新的基线
            self.pause_history.clear()

            self.logger.info(f"✅ GC阈值已设置: {profile.thresholds}")
            return True

        except Exception as e:
            self.logger.error(f"❌ 应用GC配置失败: {e}")
            return False

    def reset_to_default(self):
        """重置到默认配置"""
        gc.set_threshold(*self.original_thresholds)
        self.current_profile = None
        self.logger.info(f"🔄 GC已重置到默认阈值: {self.original_thresholds}")

    async def benchmark_profile(self, profile: GCProfile, duration_seconds: int = 300) -> Dict:
        """基准测试GC配置"""
        self.logger.info(f"🧪 开始基准测试: {profile.name} ({duration_seconds}秒)")

        # 应用配置
        self.apply_profile(profile)

        # 清理统计
        start_time = time.time()

        # 运行基准负载
        benchmark_task = asyncio.create_task(self._run_benchmark_load(duration_seconds))

        # 等待完成
        load_stats = await benchmark_task

        # 收集GC统计
        end_time = time.time()
        actual_duration = end_time - start_time

        # 分析暂停数据
        recent_pauses = [p for p in self.pause_history if p["timestamp"] >= start_time]

        if recent_pauses:
            pause_times = [p["duration"] for p in recent_pauses]
            generation_stats = self._analyze_generation_stats(recent_pauses)

            gc_stats = {
                "total_pauses": len(recent_pauses),
                "total_pause_time": sum(pause_times),
                "avg_pause_time": sum(pause_times) / len(pause_times),
                "max_pause_time": max(pause_times),
                "min_pause_time": min(pause_times),
                "p95_pause_time": (
                    sorted(pause_times)[int(len(pause_times) * 0.95)] if len(pause_times) > 0 else 0
                ),
                "p99_pause_time": (
                    sorted(pause_times)[int(len(pause_times) * 0.99)] if len(pause_times) > 0 else 0
                ),
                "pause_frequency": len(recent_pauses) / actual_duration,
                "generation_breakdown": generation_stats,
            }
        else:
            gc_stats = {
                "total_pauses": 0,
                "total_pause_time": 0,
                "avg_pause_time": 0,
                "max_pause_time": 0,
                "min_pause_time": 0,
                "p95_pause_time": 0,
                "p99_pause_time": 0,
                "pause_frequency": 0,
                "generation_breakdown": {},
            }

        benchmark_result = {
            "profile": profile.name,
            "duration": actual_duration,
            "gc_stats": gc_stats,
            "load_stats": load_stats,
            "timestamp": time.time(),
        }

        self.optimization_results[profile.name] = benchmark_result

        self.logger.info(f"✅ {profile.name}基准测试完成: P95暂停={gc_stats['p95_pause_time']*1000:.1f}ms")

        return benchmark_result

    def _analyze_generation_stats(self, pauses: List[Dict]) -> Dict:
        """分析分代GC统计"""
        generation_stats = {}

        for gen in [0, 1, 2]:
            gen_pauses = [p for p in pauses if p["generation"] == gen]

            if gen_pauses:
                pause_times = [p["duration"] for p in gen_pauses]
                collected_objects = [p["collected"] for p in gen_pauses]

                generation_stats[f"gen{gen}"] = {
                    "count": len(gen_pauses),
                    "avg_pause": sum(pause_times) / len(pause_times),
                    "max_pause": max(pause_times),
                    "total_collected": sum(collected_objects),
                    "avg_collected": sum(collected_objects) / len(collected_objects),
                }
            else:
                generation_stats[f"gen{gen}"] = {
                    "count": 0,
                    "avg_pause": 0,
                    "max_pause": 0,
                    "total_collected": 0,
                    "avg_collected": 0,
                }

        return generation_stats

    async def _run_benchmark_load(self, duration: int) -> Dict:
        """运行基准负载"""
        start_time = time.time()
        operations = 0
        allocations = 0

        # 模拟交易系统负载
        while time.time() - start_time < duration:
            # 模拟数据处理
            data = list(range(1000))  # 分配1000个整数
            processed = [x * 2 for x in data]  # 处理数据
            # 计算结果以避免编译器优化
            _ = sum(processed)

            operations += 1
            allocations += 2  # 两次列表分配

            # 间歇性大对象分配（模拟DataFrame）
            if operations % 100 == 0:
                large_data = list(range(10000))
                # 模拟使用后删除
                _ = len(large_data)  # 确保使用变量
                del large_data
                allocations += 1

            # 控制频率
            if operations % 10 == 0:
                await asyncio.sleep(0.001)  # 1ms

        return {
            "operations": operations,
            "allocations": allocations,
            "ops_per_second": operations / duration,
            "alloc_per_second": allocations / duration,
        }

    def find_optimal_profile(self) -> Optional[GCProfile]:
        """根据基准测试结果找到最优配置"""
        if not self.optimization_results:
            self.logger.warning("⚠️ 没有基准测试结果，无法找到最优配置")
            return None

        # 评分标准：P95暂停时间 (权重70%) + 暂停频率 (权重30%)
        best_profile = None
        best_score = float("inf")

        for profile_name, result in self.optimization_results.items():
            gc_stats = result["gc_stats"]

            # 归一化指标
            p95_pause = gc_stats["p95_pause_time"]
            pause_freq = gc_stats["pause_frequency"]

            # 计算综合评分（越低越好）
            score = (p95_pause * 0.7) + (pause_freq * 0.3 * 0.01)  # 频率降权

            self.logger.info(
                f"📊 {profile_name}: P95={p95_pause*1000:.1f}ms, 频率={pause_freq:.2f}/s, 评分={score:.4f}"
            )

            if score < best_score:
                best_score = score
                best_profile = next(p for p in self.gc_profiles if p.name == profile_name)

        if best_profile:
            self.logger.info(f"🏆 最优GC配置: {best_profile.name}")

        return best_profile

    async def auto_optimize(self, test_duration: int = 300) -> bool:
        """自动优化GC配置"""
        self.logger.info("🚀 开始自动GC优化")

        # 安装监控
        self.install_gc_callbacks()

        try:
            # 测试所有配置
            for profile in self.gc_profiles:
                await self.benchmark_profile(profile, test_duration)

                # 短暂休息
                await asyncio.sleep(5)

            # 找到最优配置
            optimal_profile = self.find_optimal_profile()

            if optimal_profile:
                # 应用最优配置
                self.apply_profile(optimal_profile)

                # 验证改进
                improvement = self._calculate_improvement()

                self.logger.info(f"✅ GC优化完成，P95暂停时间改进: {improvement:.1f}%")

                return improvement >= 50.0  # W2目标：50%改进
            else:
                self.logger.error("❌ 未找到合适的GC配置")
                return False

        except Exception as e:
            self.logger.error(f"❌ 自动优化失败: {e}")
            return False
        finally:
            # 可选：移除监控（或保持用于生产监控）
            pass

    def _calculate_improvement(self) -> float:
        """计算改进百分比"""
        if "default" not in self.optimization_results:
            return 0.0

        default_p95 = self.optimization_results["default"]["gc_stats"]["p95_pause_time"]

        if self.current_profile and self.current_profile.name in self.optimization_results:
            current_p95 = self.optimization_results[self.current_profile.name]["gc_stats"][
                "p95_pause_time"
            ]

            if default_p95 > 0:
                improvement = ((default_p95 - current_p95) / default_p95) * 100
                return max(0, improvement)

        return 0.0

    def get_optimization_report(self) -> Dict:
        """获取优化报告"""
        report = {
            "timestamp": time.time(),
            "current_profile": self.current_profile.name if self.current_profile else None,
            "original_thresholds": self.original_thresholds,
            "current_thresholds": gc.get_threshold(),
            "optimization_results": self.optimization_results,
            "improvement_percentage": self._calculate_improvement(),
            "monitoring_active": self.monitoring_active,
            "recent_pauses_count": len(self.pause_history),
        }

        return report

    @contextmanager
    def temporary_gc_settings(self, thresholds: Tuple[int, int, int]):
        """临时GC设置上下文管理器"""
        original = gc.get_threshold()
        try:
            gc.set_threshold(*thresholds)
            yield
        finally:
            gc.set_threshold(*original)

    def force_gc_collection(self, generation: Optional[int] = None) -> int:
        """强制GC回收"""
        if generation is not None:
            collected = gc.collect(generation)
        else:
            collected = gc.collect()

        self.logger.info(f"🗑️ 手动GC回收了 {collected} 个对象")
        return collected

    def get_gc_status(self) -> Dict:
        """获取当前GC状态"""
        counts = gc.get_count()
        thresholds = gc.get_threshold()

        status = {
            "counts": {"gen0": counts[0], "gen1": counts[1], "gen2": counts[2]},
            "thresholds": {"gen0": thresholds[0], "gen1": thresholds[1], "gen2": thresholds[2]},
            "pressure": {
                "gen0_pressure": counts[0] / thresholds[0],
                "gen1_pressure": counts[1] / thresholds[1],
                "gen2_pressure": counts[2] / thresholds[2],
            },
            "current_profile": self.current_profile.name if self.current_profile else "unknown",
            "monitoring_active": self.monitoring_active,
        }

        return status
