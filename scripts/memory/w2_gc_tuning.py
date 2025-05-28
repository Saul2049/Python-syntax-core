#!/usr/bin/env python3
"""
W2 GC调参自动化脚本
GC Tuning Automation for M5 Week 2

目标: GC暂停时间减少≥50%
策略: 一次只动一阶，观察Gen0↘ / Gen2↗
"""

import gc
import os
import sys
import time
import asyncio
import json
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from src.core.gc_optimizer import GCOptimizer
from scripts.memory.gc_profiler import GCProfiler


@dataclass
class GCTestResult:
    """GC测试结果"""

    profile_name: str
    thresholds: Tuple[int, int, int]
    p95_pause_ms: float
    avg_pause_ms: float
    gen0_frequency: float
    gen2_frequency: float
    total_collections: int
    improvement_vs_baseline: float


class W2GCTuner:
    """W2 GC调参器"""

    def __init__(self):
        self.optimizer = GCOptimizer()
        self.profiler = GCProfiler(enable_prometheus=False)
        self.logger = logging.getLogger(__name__)

        # W2目标
        self.target_improvement = 50.0  # 50%改进
        self.baseline_result = None
        self.test_results = []

        # 🔥W2渐进式调参策略
        self.tuning_profiles = [
            # 基线
            (700, 10, 10, "baseline", "Python默认配置"),
            # Step 1: 只调Gen0，减少频率
            (900, 10, 10, "step1_gen0_conservative", "Gen0保守优化"),
            (1200, 10, 10, "step1_gen0_moderate", "Gen0中等优化"),
            (1500, 10, 10, "step1_gen0_aggressive", "Gen0激进优化"),
            # Step 2: 在最佳Gen0基础上调Gen1
            (None, 15, 10, "step2_gen1_moderate", "Gen1优化"),
            (None, 20, 10, "step2_gen1_aggressive", "Gen1激进优化"),
            # Step 3: 微调Gen2
            (None, None, 15, "step3_gen2_moderate", "Gen2优化"),
            (None, None, 20, "step3_gen2_aggressive", "Gen2激进优化"),
            # 特殊配置: 高频交易优化
            (600, 8, 8, "hft_optimized", "高频交易专用"),
            (2000, 25, 25, "batch_optimized", "批处理专用"),
        ]

        self.fast_mode = os.getenv("FAST", "0") == "1"
        self.test_duration = 60 if self.fast_mode else 300  # 1min vs 5min

    async def run_gc_baseline(self) -> GCTestResult:
        """运行基线测试"""
        self.logger.info("📊 运行GC基线测试...")

        # 重置为默认配置
        gc.set_threshold(700, 10, 10)

        # 运行测试
        result = await self._test_gc_configuration((700, 10, 10), "baseline", "Python默认配置")

        self.baseline_result = result
        self.logger.info(f"✅ 基线建立: P95={result.p95_pause_ms:.1f}ms")

        return result

    async def _test_gc_configuration(
        self, thresholds: Tuple[int, int, int], name: str, description: str
    ) -> GCTestResult:
        """测试单个GC配置"""

        # 应用配置
        gc.set_threshold(*thresholds)
        self.logger.info(f"🔧 测试配置 {name}: {thresholds}")

        # 清理内存并重启GC监控
        gc.collect()
        await asyncio.sleep(1)

        # 启动监控
        self.profiler.start_monitoring()

        # 运行负载测试
        await self._simulate_gc_load()

        # 停止监控并获取统计
        self.profiler.stop_monitoring()
        stats = self.profiler.get_statistics()

        if "error" in stats:
            self.logger.error(f"❌ 配置{name}测试失败")
            return None

        # 计算关键指标
        gen0_stats = stats["by_generation"].get(0, {})
        gen2_stats = stats["by_generation"].get(2, {})

        p95_pause = (
            max(gen0_stats.get("p95_pause", 0), gen2_stats.get("p95_pause", 0)) * 1000
        )  # 转换为毫秒

        avg_pause = stats["avg_pause_time"] * 1000
        gen0_freq = gen0_stats.get("count", 0) / stats["monitoring_duration"]
        gen2_freq = gen2_stats.get("count", 0) / stats["monitoring_duration"]
        total_collections = stats["total_gc_events"]

        # 计算相对基线的改进
        improvement = 0.0
        if self.baseline_result:
            if self.baseline_result.p95_pause_ms > 0:
                improvement = (
                    (self.baseline_result.p95_pause_ms - p95_pause)
                    / self.baseline_result.p95_pause_ms
                ) * 100

        result = GCTestResult(
            profile_name=name,
            thresholds=thresholds,
            p95_pause_ms=p95_pause,
            avg_pause_ms=avg_pause,
            gen0_frequency=gen0_freq,
            gen2_frequency=gen2_freq,
            total_collections=total_collections,
            improvement_vs_baseline=improvement,
        )

        self.test_results.append(result)

        self.logger.info(
            f"📈 {name}: P95={p95_pause:.1f}ms, "
            f"Gen0={gen0_freq:.1f}/s, 改进={improvement:+.1f}%"
        )

        return result

    async def _simulate_gc_load(self):
        """模拟GC负载"""

        # 导入策略来产生真实负载
        from src.strategies.cache_optimized_strategy import CacheOptimizedStrategy

        strategy = CacheOptimizedStrategy({})
        test_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]

        # 计算负载量
        signals_per_second = 10 if self.fast_mode else 5
        total_signals = self.test_duration * signals_per_second

        self.logger.info(f"🔄 模拟负载: {total_signals}个信号, {self.test_duration}秒")

        start_time = time.time()
        signals_generated = 0

        while time.time() - start_time < self.test_duration:
            for symbol in test_symbols:
                # 模拟价格变动
                price = 50000 + (time.time() % 1000)

                # 生成信号 (触发GC活动)
                strategy.generate_signals(symbol, price)
                signals_generated += 1

                # 控制频率
                await asyncio.sleep(1.0 / signals_per_second / len(test_symbols))

        self.logger.info(f"✅ 负载完成: 生成{signals_generated}个信号")

    async def run_progressive_tuning(self) -> Optional[GCTestResult]:
        """运行渐进式调参"""
        self.logger.info("🚀 开始W2渐进式GC调参")

        # Step 1: 建立基线
        await self.run_gc_baseline()

        best_result = self.baseline_result
        best_gen0 = 700
        best_gen1 = 10

        # Step 2: 优化Gen0阈值
        self.logger.info("🔧 Step 1: 优化Gen0阈值")

        for gen0_threshold in [900, 1200, 1500]:
            result = await self._test_gc_configuration(
                (gen0_threshold, 10, 10), f"gen0_{gen0_threshold}", f"Gen0={gen0_threshold}"
            )

            if result and result.improvement_vs_baseline > best_result.improvement_vs_baseline:
                best_result = result
                best_gen0 = gen0_threshold
                self.logger.info(f"🎯 新的最佳Gen0配置: {gen0_threshold}")

        # Step 3: 基于最佳Gen0优化Gen1
        self.logger.info("🔧 Step 2: 优化Gen1阈值")

        for gen1_threshold in [15, 20]:
            result = await self._test_gc_configuration(
                (best_gen0, gen1_threshold, 10),
                f"gen1_{gen1_threshold}",
                f"Gen0={best_gen0}, Gen1={gen1_threshold}",
            )

            if result and result.improvement_vs_baseline > best_result.improvement_vs_baseline:
                best_result = result
                best_gen1 = gen1_threshold
                self.logger.info(f"🎯 新的最佳Gen1配置: {gen1_threshold}")

        # Step 4: 基于最佳Gen0+Gen1优化Gen2
        self.logger.info("🔧 Step 3: 优化Gen2阈值")

        for gen2_threshold in [15, 20]:
            result = await self._test_gc_configuration(
                (best_gen0, best_gen1, gen2_threshold),
                f"final_{best_gen0}_{best_gen1}_{gen2_threshold}",
                f"最终配置候选",
            )

            if result and result.improvement_vs_baseline > best_result.improvement_vs_baseline:
                best_result = result
                self.logger.info(f"🎯 新的最佳完整配置: {result.thresholds}")

        return best_result

    def apply_optimal_configuration(self, result: GCTestResult):
        """应用最优配置"""
        if not result:
            self.logger.error("❌ 没有有效的优化结果")
            return

        gc.set_threshold(*result.thresholds)

        # 🔥应用Python 3.12+的freeze优化
        try:
            if hasattr(gc, "freeze"):
                gc.freeze()
                self.logger.info("❄️ 已启用gc.freeze()优化")
        except:
            pass

        self.logger.info(f"✅ 已应用最优GC配置: {result.thresholds}")
        self.logger.info(f"📈 预期改进: {result.improvement_vs_baseline:.1f}%")

    def generate_report(self) -> Dict:
        """生成W2调参报告"""
        if not self.test_results:
            return {"error": "No test results available"}

        # 找到最佳结果
        best_result = max(self.test_results, key=lambda r: r.improvement_vs_baseline)

        # W2验收检查
        w2_passed = best_result.improvement_vs_baseline >= self.target_improvement

        report = {
            "timestamp": datetime.now().isoformat(),
            "w2_target_improvement": self.target_improvement,
            "w2_acceptance": {
                "passed": w2_passed,
                "achieved_improvement": best_result.improvement_vs_baseline,
                "target_met": best_result.improvement_vs_baseline >= self.target_improvement,
            },
            "baseline_result": {
                "p95_pause_ms": self.baseline_result.p95_pause_ms if self.baseline_result else 0,
                "thresholds": (
                    self.baseline_result.thresholds if self.baseline_result else (700, 10, 10)
                ),
            },
            "best_result": {
                "profile_name": best_result.profile_name,
                "thresholds": best_result.thresholds,
                "p95_pause_ms": best_result.p95_pause_ms,
                "improvement_vs_baseline": best_result.improvement_vs_baseline,
                "gen0_frequency": best_result.gen0_frequency,
                "gen2_frequency": best_result.gen2_frequency,
            },
            "all_results": [
                {
                    "name": r.profile_name,
                    "thresholds": r.thresholds,
                    "p95_pause_ms": r.p95_pause_ms,
                    "improvement": r.improvement_vs_baseline,
                }
                for r in self.test_results
            ],
            "recommendations": {
                "apply_configuration": best_result.thresholds,
                "use_gc_freeze": True,
                "monitoring_focus": [
                    "gc_gen2_collections_total",
                    "gc_pause_duration_seconds",
                    "memory_allocation_rate_per_second",
                ],
            },
        }

        return report

    def save_report(self, filename: str):
        """保存调参报告"""
        report = self.generate_report()

        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else ".", exist_ok=True)
        with open(filename, "w") as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info(f"💾 W2调参报告已保存: {filename}")

        # 打印总结
        self._print_summary(report)

    def _print_summary(self, report: Dict):
        """打印调参总结"""
        print("\n" + "=" * 60)
        print("🗑️ W2 GC调参总结报告")
        print("=" * 60)

        baseline = report["baseline_result"]
        best = report["best_result"]
        acceptance = report["w2_acceptance"]

        print(f"📊 基线配置: {baseline['thresholds']}")
        print(f"   P95暂停: {baseline['p95_pause_ms']:.1f}ms")

        print(f"\n🏆 最优配置: {best['thresholds']}")
        print(f"   P95暂停: {best['p95_pause_ms']:.1f}ms")
        print(f"   改进幅度: {best['improvement_vs_baseline']:+.1f}%")
        print(f"   Gen0频率: {best['gen0_frequency']:.1f}/s")
        print(f"   Gen2频率: {best['gen2_frequency']:.1f}/s")

        print(f"\n🎯 W2验收结果:")
        print(f"   目标改进: ≥{report['w2_target_improvement']:.0f}%")
        print(f"   实际改进: {acceptance['achieved_improvement']:+.1f}%")
        print(f"   验收状态: {'✅ PASS' if acceptance['passed'] else '❌ FAIL'}")

        if acceptance["passed"]:
            print(f"\n🎉 W2 GC调参成功完成！可以进入W3阶段")
        else:
            print(f"\n⚠️ W2 GC调参未达标，需要进一步优化")

        print("=" * 60)


async def main():
    """主函数"""
    # 配置日志
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    print("🗑️ W2 GC调参自动化工具")
    print("🎯 目标: GC暂停时间减少≥50%")

    # 创建调参器
    tuner = W2GCTuner()

    try:
        # 运行渐进式调参
        best_result = await tuner.run_progressive_tuning()

        if best_result:
            # 应用最优配置
            tuner.apply_optimal_configuration(best_result)

            # 生成报告
            timestamp = int(time.time())
            report_file = f"output/w2_gc_tuning_{timestamp}.json"
            os.makedirs("output", exist_ok=True)
            tuner.save_report(report_file)

            # 检查是否达到W2目标
            if best_result.improvement_vs_baseline >= tuner.target_improvement:
                print("\n🎉 W2 GC调参目标达成！")
                return True
            else:
                print(f"\n⚠️ 改进{best_result.improvement_vs_baseline:.1f}%未达到50%目标")
                return False
        else:
            print("❌ W2 GC调参失败")
            return False

    except Exception as e:
        print(f"❌ W2调参过程出错: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
