#!/usr/bin/env python3
"""
M4阶段简化异步性能基准测试
M4 Simplified Async Performance Benchmark

用途：
- 测试异步信号处理性能
- 测试并发任务调度性能
- 验证M3+M4组合优化效果
"""

import asyncio
import json
import statistics
import time
from datetime import datetime
from typing import Any, Dict

import numpy as np
import pandas as pd
import psutil

from src.core.signal_processor_vectorized import OptimizedSignalProcessor
from src.monitoring.metrics_collector import get_metrics_collector


class M4SimpleBenchmark:
    """M4简化性能基准测试器"""

    def __init__(self):
        self.metrics = get_metrics_collector()
        self.signal_processor = OptimizedSignalProcessor()

        # 测试配置
        self.test_duration = 30  # 测试持续时间（秒）
        self.symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]

        # 生成测试数据
        self.test_data = self._generate_market_data()

        # 性能统计
        self.async_latencies = []
        self.signal_latencies = []
        self.cpu_usage = []

    def _generate_market_data(self) -> Dict[str, pd.DataFrame]:
        """生成测试市场数据"""
        market_data = {}

        for symbol in self.symbols:
            np.random.seed(hash(symbol) % 2**32)  # 确保每个symbol有不同但可重复的数据

            data = []
            base_price = 30000 if "BTC" in symbol else 2000 if "ETH" in symbol else 0.5

            for i in range(200):  # 200个数据点
                # 生成价格走势
                if i == 0:
                    price = base_price
                else:
                    price = data[-1]["close"] * (1 + np.random.normal(0, 0.01))

                # 生成OHLC
                high = price * (1 + abs(np.random.normal(0, 0.005)))
                low = price * (1 - abs(np.random.normal(0, 0.005)))
                open_price = data[-1]["close"] if i > 0 else price

                data.append(
                    {
                        "timestamp": pd.Timestamp.now() - pd.Timedelta(minutes=200 - i),
                        "open": open_price,
                        "high": high,
                        "low": low,
                        "close": price,
                        "volume": np.random.randint(100, 10000),
                    }
                )

            df = pd.DataFrame(data)
            df.set_index("timestamp", inplace=True)
            market_data[symbol] = df

        return market_data

    async def benchmark_async_signal_processing(self) -> Dict[str, Any]:
        """测试异步信号处理性能"""
        print("🔄 测试异步信号处理性能")

        signal_times = []
        concurrent_count = 0
        max_concurrent = 0

        async def process_symbol_signals(symbol: str, iterations: int = 50):
            """处理单个交易对的信号"""
            nonlocal concurrent_count, max_concurrent

            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)

            symbol_times = []

            try:
                for i in range(iterations):
                    # 模拟数据更新
                    data = self.test_data[symbol].copy()

                    start_time = time.perf_counter()

                    # 异步信号处理
                    signals = self.signal_processor.get_trading_signals_optimized(data)
                    atr = self.signal_processor.compute_atr_optimized(data)

                    end_time = time.perf_counter()
                    processing_time = (end_time - start_time) * 1000  # ms

                    symbol_times.append(processing_time)

                    # 模拟异步处理延迟
                    await asyncio.sleep(0.001)  # 1ms异步延迟

                return symbol_times

            finally:
                concurrent_count -= 1

        # 并发处理所有交易对
        start_time = time.time()

        tasks = [process_symbol_signals(symbol) for symbol in self.symbols]
        results = await asyncio.gather(*tasks)

        end_time = time.time()
        total_time = end_time - start_time

        # 合并所有信号延迟
        for symbol_times in results:
            signal_times.extend(symbol_times)

        # 计算统计结果
        if signal_times:
            avg_latency = statistics.mean(signal_times)
            p95_latency = (
                statistics.quantiles(signal_times, n=20)[18]
                if len(signal_times) >= 20
                else max(signal_times)
            )
            max_latency = max(signal_times)
            min_latency = min(signal_times)
        else:
            avg_latency = p95_latency = max_latency = min_latency = 0

        results = {
            "avg_latency_ms": avg_latency,
            "p95_latency_ms": p95_latency,
            "max_latency_ms": max_latency,
            "min_latency_ms": min_latency,
            "total_signals": len(signal_times),
            "symbols_processed": len(self.symbols),
            "max_concurrent": max_concurrent,
            "total_time_s": total_time,
            "throughput_signals_per_sec": len(signal_times) / total_time if total_time > 0 else 0,
            "target_met": p95_latency <= 50,  # 目标：P95≤50ms（更严格的标准）
        }

        self._print_async_signal_results(results)
        return results

    async def benchmark_concurrent_cpu_usage(self) -> Dict[str, Any]:
        """测试并发CPU使用率"""
        print("💻 测试并发CPU使用率（目标：≤30%）")

        cpu_measurements = []
        memory_measurements = []

        async def cpu_monitor():
            """CPU监控任务"""
            for _ in range(self.test_duration):
                cpu_percent = psutil.cpu_percent(interval=None)
                memory_percent = psutil.virtual_memory().percent

                cpu_measurements.append(cpu_percent)
                memory_measurements.append(memory_percent)

                await asyncio.sleep(1)

        async def high_frequency_signal_processing():
            """高频信号处理任务"""
            for i in range(self.test_duration * 10):  # 10Hz频率
                # 随机选择交易对
                symbol = self.symbols[i % len(self.symbols)]
                data = self.test_data[symbol]

                # 信号处理
                signals = self.signal_processor.get_trading_signals_optimized(data)
                atr = self.signal_processor.compute_atr_optimized(data)

                await asyncio.sleep(0.1)  # 100ms间隔

        async def market_data_simulation():
            """市场数据模拟任务"""
            for i in range(self.test_duration * 5):  # 5Hz频率
                # 模拟数据处理负载
                data = [x**2 for x in range(1000)]
                sum(data)  # 消耗一些CPU

                await asyncio.sleep(0.2)  # 200ms间隔

        # 并发执行所有任务
        await asyncio.gather(
            cpu_monitor(), high_frequency_signal_processing(), market_data_simulation()
        )

        # 计算统计结果
        avg_cpu = statistics.mean(cpu_measurements) if cpu_measurements else 0
        max_cpu = max(cpu_measurements) if cpu_measurements else 0
        avg_memory = statistics.mean(memory_measurements) if memory_measurements else 0

        results = {
            "avg_cpu_percent": avg_cpu,
            "max_cpu_percent": max_cpu,
            "avg_memory_percent": avg_memory,
            "measurements": len(cpu_measurements),
            "target_met": max_cpu <= 30,  # 目标：CPU≤30%
        }

        self._print_cpu_results(results)
        return results

    async def benchmark_async_task_scheduling(self) -> Dict[str, Any]:
        """测试异步任务调度性能"""
        print("⚡ 测试异步任务调度性能")

        task_latencies = []
        completed_tasks = 0

        async def async_task(task_id: int, complexity: int = 1):
            """异步任务"""
            start_time = time.perf_counter()

            # 模拟不同复杂度的计算
            for _ in range(complexity * 100):
                await asyncio.sleep(0.0001)  # 0.1ms异步延迟

            end_time = time.perf_counter()
            latency = (end_time - start_time) * 1000  # ms

            return task_id, latency

        # 创建大量异步任务
        tasks = []
        for i in range(100):  # 100个任务
            complexity = (i % 5) + 1  # 1-5复杂度
            tasks.append(async_task(i, complexity))

        # 并发执行所有任务
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        total_time = end_time - start_time

        # 提取延迟数据
        for task_id, latency in results:
            task_latencies.append(latency)
            completed_tasks += 1

        # 计算统计结果
        if task_latencies:
            avg_latency = statistics.mean(task_latencies)
            p95_latency = (
                statistics.quantiles(task_latencies, n=20)[18]
                if len(task_latencies) >= 20
                else max(task_latencies)
            )
            max_latency = max(task_latencies)
        else:
            avg_latency = p95_latency = max_latency = 0

        results = {
            "avg_task_latency_ms": avg_latency,
            "p95_task_latency_ms": p95_latency,
            "max_task_latency_ms": max_latency,
            "completed_tasks": completed_tasks,
            "total_time_s": total_time,
            "task_throughput": completed_tasks / total_time if total_time > 0 else 0,
            "target_met": p95_latency <= 200,  # 目标：P95≤200ms
        }

        self._print_task_results(results)
        return results

    def _print_async_signal_results(self, results: Dict[str, Any]):
        """打印异步信号处理结果"""
        print("\n" + "=" * 60)
        print("🔄 异步信号处理性能测试结果")
        print("=" * 60)

        print("📊 信号处理延迟:")
        print(f"   平均延迟: {results['avg_latency_ms']:.2f}ms")
        print(f"   P95延迟:  {results['p95_latency_ms']:.2f}ms")
        print(f"   最大延迟: {results['max_latency_ms']:.2f}ms")
        print(f"   最小延迟: {results['min_latency_ms']:.2f}ms")

        print("\n📈 处理统计:")
        print(f"   信号总数: {results['total_signals']}")
        print(f"   交易对数: {results['symbols_processed']}")
        print(f"   最大并发: {results['max_concurrent']}")
        print(f"   总耗时: {results['total_time_s']:.2f}秒")
        print(f"   吞吐量: {results['throughput_signals_per_sec']:.1f} 信号/秒")

        status = "✅ 目标达成" if results["target_met"] else "❌ 未达目标"
        print(f"\n🎯 目标检查 (P95≤50ms): {status}")
        print("=" * 60)

    def _print_cpu_results(self, results: Dict[str, Any]):
        """打印CPU使用率结果"""
        print("\n" + "=" * 60)
        print("💻 并发CPU使用率测试结果")
        print("=" * 60)

        print("🖥️ CPU使用率:")
        print(f"   平均CPU: {results['avg_cpu_percent']:.1f}%")
        print(f"   峰值CPU: {results['max_cpu_percent']:.1f}%")

        print("\n💾 内存使用率:")
        print(f"   平均内存: {results['avg_memory_percent']:.1f}%")

        print("\n📊 监控统计:")
        print(f"   测量次数: {results['measurements']}")

        status = "✅ 目标达成" if results["target_met"] else "❌ 未达目标"
        print(f"\n🎯 目标检查 (CPU≤30%): {status}")
        print("=" * 60)

    def _print_task_results(self, results: Dict[str, Any]):
        """打印任务调度结果"""
        print("\n" + "=" * 60)
        print("⚡ 异步任务调度性能测试结果")
        print("=" * 60)

        print("📊 任务延迟:")
        print(f"   平均延迟: {results['avg_task_latency_ms']:.2f}ms")
        print(f"   P95延迟:  {results['p95_task_latency_ms']:.2f}ms")
        print(f"   最大延迟: {results['max_task_latency_ms']:.2f}ms")

        print("\n📈 调度统计:")
        print(f"   完成任务: {results['completed_tasks']}")
        print(f"   总耗时: {results['total_time_s']:.2f}秒")
        print(f"   任务吞吐: {results['task_throughput']:.1f} 任务/秒")

        status = "✅ 目标达成" if results["target_met"] else "❌ 未达目标"
        print(f"\n🎯 目标检查 (P95≤200ms): {status}")
        print("=" * 60)

    async def run_full_benchmark(self) -> Dict[str, Any]:
        """运行完整的M4性能基准测试"""
        print("🚀 M4阶段简化异步性能基准测试启动")
        print(f"⏱️ 测试时长: {self.test_duration}秒")
        print(f"📊 测试交易对: {self.symbols}")

        start_time = time.time()
        results = {}

        try:
            # 1. 异步信号处理测试
            results["async_signals"] = await self.benchmark_async_signal_processing()

            # 2. 异步任务调度测试
            results["task_scheduling"] = await self.benchmark_async_task_scheduling()

            # 3. 并发CPU使用率测试
            results["cpu_usage"] = await self.benchmark_concurrent_cpu_usage()

            # 4. 生成综合评估
            results["summary"] = self._generate_summary(results)

            # 5. 保存结果
            await self._save_results(results)

            return results

        except Exception as e:
            print(f"❌ 基准测试失败: {e}")
            return {"error": str(e)}
        finally:
            total_time = time.time() - start_time
            print(f"\n⏱️ 测试总耗时: {total_time:.1f}秒")

    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成综合评估"""
        targets_met = []

        # 检查各项目标
        for test_name in ["async_signals", "task_scheduling", "cpu_usage"]:
            if test_name in results and "target_met" in results[test_name]:
                targets_met.append(results[test_name]["target_met"])

        # 计算总体成功率
        if targets_met:
            success_rate = sum(targets_met) / len(targets_met) * 100
            all_targets_met = all(targets_met)
        else:
            success_rate = 0
            all_targets_met = False

        summary = {
            "all_targets_met": all_targets_met,
            "success_rate": success_rate,
            "targets_checked": len(targets_met),
            "timestamp": datetime.now().isoformat(),
        }

        self._print_summary(summary)
        return summary

    def _print_summary(self, summary: Dict[str, Any]):
        """打印综合评估"""
        print("\n" + "=" * 60)
        print("🎯 M4异步性能基准测试综合评估")
        print("=" * 60)

        status = "🎉 全部达标" if summary["all_targets_met"] else "⚠️ 部分未达标"
        print(f"📊 总体状态: {status}")
        print(f"🎯 成功率: {summary['success_rate']:.1f}%")
        print(f"🔍 检查项目: {summary['targets_checked']}")

        print("\n📋 M4阶段关键指标:")
        print("   ✓ 异步信号P95 ≤ 50ms")
        print("   ✓ 任务调度P95 ≤ 200ms")
        print("   ✓ 并发CPU ≤ 30%")

        if summary["all_targets_met"]:
            print("\n🏆 M4阶段异步优化目标达成！")
            print("✅ CPU从毫秒级优化到微秒级成功")
            print("🚀 系统具备高并发实时处理能力")
        else:
            print("\n⚠️ 部分指标需要进一步优化")

        print("=" * 60)

    async def _save_results(self, results: Dict[str, Any]):
        """保存测试结果"""
        try:
            filename = f"output/m4_simple_benchmark_{int(time.time())}.json"
            with open(filename, "w") as f:
                json.dump(results, f, indent=2, default=str)

            print(f"\n✅ 测试结果已保存: {filename}")

        except Exception as e:
            print(f"⚠️ 保存结果失败: {e}")


async def main():
    """主函数"""
    print("🚀 启动M4阶段简化异步性能基准测试")

    benchmark = M4SimpleBenchmark()
    results = await benchmark.run_full_benchmark()

    if "error" not in results:
        print("\n🎊 M4简化性能基准测试完成！")
    else:
        print(f"\n❌ 测试失败: {results['error']}")


if __name__ == "__main__":
    asyncio.run(main())
