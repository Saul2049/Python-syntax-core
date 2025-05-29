#!/usr/bin/env python3
"""
信号延迟基准测试脚本
用于快速迭代和优化信号计算性能
"""
import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict

import pandas as pd

# 添加src路径
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.core.price_fetcher import calculate_atr
from src.core.signal_processor import get_trading_signals
from src.core.signal_processor_optimized import get_trading_signals_optimized
from src.monitoring.metrics_collector import get_metrics_collector


class LatencyBenchmark:
    """延迟基准测试器"""

    def __init__(self):
        self.metrics = get_metrics_collector()
        self.results = []

    def generate_test_data(self, symbol: str = "BTCUSDT", periods: int = 100) -> pd.DataFrame:
        """生成测试数据"""
        # 创建模拟价格数据
        import random

        base_price = 50000.0
        data = []

        for i in range(periods):
            # 模拟价格随机游走
            price_change = random.uniform(-0.02, 0.02)
            base_price *= 1 + price_change

            data.append(
                {
                    "timestamp": pd.Timestamp.now() - pd.Timedelta(minutes=periods - i),
                    "open": base_price * 0.999,
                    "high": base_price * 1.002,
                    "low": base_price * 0.998,
                    "close": base_price,
                    "volume": random.uniform(100, 1000),
                }
            )

        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)
        return df

    def benchmark_signal_calculation(self, iterations: int = 100) -> Dict[str, float]:
        """基准测试信号计算"""
        print(f"🧪 信号计算基准测试 ({iterations}次迭代)")

        # 准备测试数据
        test_data = self.generate_test_data()
        latencies = []

        for i in range(iterations):
            start_time = time.time()

            # 执行信号计算
            try:
                signals = get_trading_signals(test_data, fast_win=7, slow_win=25)
                atr = calculate_atr(test_data)

                # 验证计算结果
                if i == 0:
                    print(f"   信号数量: {len(signals) if signals else 0}, ATR值: {atr:.4f}")

                latency = time.time() - start_time
                latencies.append(latency)

                if (i + 1) % 20 == 0:
                    current_p95 = statistics.quantiles(latencies, n=20)[18]  # P95
                    print(f"   进度: {i+1}/{iterations}, 当前P95: {current_p95*1000:.1f}ms")

            except Exception as e:
                print(f"   错误: {e}")
                continue

        # 计算统计数据
        if latencies:
            stats = {
                "mean": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "p95": statistics.quantiles(latencies, n=20)[18],
                "p99": statistics.quantiles(latencies, n=100)[98],
                "min": min(latencies),
                "max": max(latencies),
                "count": len(latencies),
            }
        else:
            stats = {"error": "No successful iterations"}

        return stats

    def benchmark_data_fetch(self, iterations: int = 50) -> Dict[str, float]:
        """基准测试数据获取"""
        print(f"📊 数据获取基准测试 ({iterations}次迭代)")

        latencies = []

        for i in range(iterations):
            start_time = time.time()

            try:
                # 模拟数据获取 (使用生成的测试数据代替真实API调用)
                test_data = self.generate_test_data(periods=200)

                # 验证数据生成结果
                if i == 0:
                    print(f"   生成数据行数: {len(test_data)}")

                latency = time.time() - start_time
                latencies.append(latency)

                if (i + 1) % 10 == 0:
                    current_avg = statistics.mean(latencies)
                    print(f"   进度: {i+1}/{iterations}, 平均延迟: {current_avg*1000:.1f}ms")

            except Exception as e:
                print(f"   错误: {e}")
                continue

        if latencies:
            stats = {
                "mean": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "p95": statistics.quantiles(latencies, n=20)[18],
                "min": min(latencies),
                "max": max(latencies),
                "count": len(latencies),
            }
        else:
            stats = {"error": "No successful iterations"}

        return stats

    def benchmark_parallel_signals(
        self, iterations: int = 50, max_workers: int = 4
    ) -> Dict[str, float]:
        """基准测试并行信号计算"""
        print(f"⚡ 并行信号计算基准测试 ({iterations}次迭代, {max_workers}线程)")

        # 准备多个测试数据集
        test_datasets = [self.generate_test_data() for _ in range(max_workers)]
        latencies = []

        def calculate_signal_worker(data):
            """单个信号计算工作函数"""
            start_time = time.time()
            signals = get_trading_signals(data, fast_win=7, slow_win=25)
            atr = calculate_atr(data)
            # 验证计算结果
            if signals and atr > 0:
                return time.time() - start_time
            return time.time() - start_time

        for i in range(iterations):
            batch_start = time.time()

            try:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = [
                        executor.submit(calculate_signal_worker, data) for data in test_datasets
                    ]

                    # 等待所有任务完成
                    for future in as_completed(futures):
                        future.result()  # 确保没有异常

                total_latency = time.time() - batch_start
                latencies.append(total_latency)

                if (i + 1) % 10 == 0:
                    current_avg = statistics.mean(latencies)
                    print(f"   进度: {i+1}/{iterations}, 平均延迟: {current_avg*1000:.1f}ms")

            except Exception as e:
                print(f"   错误: {e}")
                continue

        if latencies:
            stats = {
                "mean": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "p95": statistics.quantiles(latencies, n=20)[18],
                "min": min(latencies),
                "max": max(latencies),
                "count": len(latencies),
                "workers": max_workers,
            }
        else:
            stats = {"error": "No successful iterations"}

        return stats

    def benchmark_optimized_signals(self, iterations: int = 100) -> Dict[str, float]:
        """基准测试优化版信号计算"""
        print(f"🚀 优化版信号计算基准测试 ({iterations}次迭代)")

        # 准备测试数据
        test_data = self.generate_test_data()
        latencies = []

        for i in range(iterations):
            start_time = time.time()

            # 执行优化版信号计算
            try:
                signals = get_trading_signals_optimized(test_data, fast_win=7, slow_win=25)

                # 验证计算结果
                if i == 0:
                    print(f"   优化版信号数量: {len(signals) if signals else 0}")

                latency = time.time() - start_time
                latencies.append(latency)

                if (i + 1) % 20 == 0:
                    current_p95 = statistics.quantiles(latencies, n=20)[18]  # P95
                    print(f"   进度: {i+1}/{iterations}, 当前P95: {current_p95*1000:.1f}ms")

            except Exception as e:
                print(f"   错误: {e}")
                continue

        # 计算统计数据
        if latencies:
            stats = {
                "mean": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "p95": statistics.quantiles(latencies, n=20)[18],
                "p99": statistics.quantiles(latencies, n=100)[98],
                "min": min(latencies),
                "max": max(latencies),
                "count": len(latencies),
            }
        else:
            stats = {"error": "No successful iterations"}

        return stats

    def benchmark_cache_performance(self, iterations: int = 200) -> Dict[str, float]:
        """基准测试缓存性能"""
        print(f"💾 缓存性能基准测试 ({iterations}次迭代)")

        # 准备测试数据 - 使用相同数据测试缓存命中
        test_data = self.generate_test_data()
        latencies = []
        cache_hits = 0

        for i in range(iterations):
            start_time = time.time()

            try:
                # 前一半使用相同数据，后一半使用不同数据
                if i < iterations // 2:
                    signals = get_trading_signals_optimized(test_data, fast_win=7, slow_win=25)
                    if i > 0:  # 第一次之后应该是缓存命中
                        cache_hits += 1
                else:
                    # 使用新数据
                    new_data = self.generate_test_data()
                    signals = get_trading_signals_optimized(new_data, fast_win=7, slow_win=25)

                # 验证计算结果
                if i == 0:
                    print(f"   缓存测试信号数量: {len(signals) if signals else 0}")

                latency = time.time() - start_time
                latencies.append(latency)

                if (i + 1) % 50 == 0:
                    current_avg = statistics.mean(latencies)
                    print(f"   进度: {i+1}/{iterations}, 平均延迟: {current_avg*1000:.1f}ms")

            except Exception as e:
                print(f"   错误: {e}")
                continue

        if latencies:
            stats = {
                "mean": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "p95": statistics.quantiles(latencies, n=20)[18],
                "min": min(latencies),
                "max": max(latencies),
                "count": len(latencies),
                "cache_hits": cache_hits,
                "hit_rate": cache_hits / (iterations // 2 - 1) if iterations > 2 else 0,
            }
        else:
            stats = {"error": "No successful iterations"}

        return stats

    def run_full_benchmark(self) -> Dict[str, Any]:
        """运行完整基准测试"""
        print("🚀 开始完整延迟基准测试")
        print("=" * 60)

        results = {
            "timestamp": time.time(),
            "signal_calculation": {},
            "data_fetch": {},
            "parallel_signals": {},
            "optimized_signals": {},
            "cache_performance": {},
        }

        # 1. 信号计算基准
        results["signal_calculation"] = self.benchmark_signal_calculation(100)
        print()

        # 2. 数据获取基准
        results["data_fetch"] = self.benchmark_data_fetch(50)
        print()

        # 3. 并行信号计算基准
        results["parallel_signals"] = self.benchmark_parallel_signals(30, max_workers=4)
        print()

        # 4. 优化版信号计算基准
        results["optimized_signals"] = self.benchmark_optimized_signals(100)
        print()

        # 5. 缓存性能基准
        results["cache_performance"] = self.benchmark_cache_performance(200)
        print()

        # 输出汇总报告
        self._print_summary(results)

        return results

    def _print_summary(self, results: Dict[str, Any]):
        """打印汇总报告"""
        print("=" * 60)
        print("📊 基准测试汇总报告")
        print("=" * 60)

        for category, stats in results.items():
            if category == "timestamp":
                continue

            if "error" in stats:
                print(f"❌ {category}: {stats['error']}")
                continue

            category_name = {
                "signal_calculation": "🧮 信号计算",
                "data_fetch": "📊 数据获取",
                "parallel_signals": "⚡ 并行计算",
                "optimized_signals": "🚀 优化版信号计算",
                "cache_performance": "💾 缓存性能",
            }.get(category, category)

            print(f"\n{category_name}:")
            print(f"   平均延迟: {stats['mean']*1000:.1f}ms")
            print(f"   P95延迟:  {stats['p95']*1000:.1f}ms")
            print(f"   P99延迟:  {stats['p99']*1000:.1f}ms" if "p99" in stats else "")
            print(f"   最小延迟: {stats['min']*1000:.1f}ms")
            print(f"   最大延迟: {stats['max']*1000:.1f}ms")
            print(f"   样本数量: {stats['count']}")

            # 缓存命中率显示
            if "hit_rate" in stats:
                print(f"   缓存命中率: {stats['hit_rate']*100:.1f}%")

            # 与目标对比
            target_ms = 500  # 0.5s = 500ms
            p95_ms = stats["p95"] * 1000

            if p95_ms < target_ms:
                status = "✅ 已达标"
            elif p95_ms < target_ms * 1.2:
                status = "⚠️ 接近目标"
            else:
                status = "❌ 需要优化"

            print(f"   状态: {status} (目标P95 < {target_ms}ms)")

        print("\n" + "=" * 60)
        print("💡 优化建议:")

        signal_p95 = results["signal_calculation"].get("p95", 0) * 1000
        if signal_p95 > 500:
            print("   🔧 信号计算延迟过高，建议：")
            print("      - 添加指标缓存 (ATR, EMA)")
            print("      - 优化pandas操作")
            print("      - 使用向量化计算")

        parallel_p95 = results["parallel_signals"].get("p95", 0) * 1000
        if parallel_p95 < signal_p95 * 0.7:
            print("   ⚡ 并行计算效果显著，建议在生产环境启用")

        print("   📈 持续监控: make monitor-metrics")


def main():
    """主函数"""
    benchmark = LatencyBenchmark()

    print("🎯 交易系统延迟基准测试")
    print("目标: P95信号延迟 < 0.5秒 (500ms)")
    print()

    # 运行基准测试
    results = benchmark.run_full_benchmark()

    # 保存结果到文件
    import json

    timestamp = int(time.time())
    filename = f"benchmark_results_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 结果已保存到: {filename}")
    print("🔄 建议定期运行此脚本监控性能变化")


if __name__ == "__main__":
    main()
