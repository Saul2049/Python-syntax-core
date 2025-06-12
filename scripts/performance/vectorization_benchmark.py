#!/usr/bin/env python3
"""
M3阶段向量化性能对比测试
Vectorization Performance Benchmark for M3 Phase

用途：
- 对比原始vs向量化信号处理性能
- 验证30-50%的CPU优化目标
- 生成性能改进报告
"""

import time
from typing import Any, Dict

import numpy as np
import pandas as pd

# 导入原始和优化版本
from src.core.signal_processor import get_trading_signals
from src.core.signal_processor_vectorized import (
    VectorizedSignalProcessor,
    get_trading_signals_optimized,
)


class VectorizationBenchmark:
    """向量化性能对比测试器"""

    def __init__(self):
        self.test_data = self._generate_test_data()

    def _generate_test_data(self, size: int = 1000) -> pd.DataFrame:
        """生成测试数据"""
        np.random.seed(42)

        # 生成模拟价格数据
        base_price = 30000
        returns = np.random.normal(0, 0.02, size)
        prices = [base_price]

        for ret in returns:
            prices.append(prices[-1] * (1 + ret))

        # 生成OHLC数据
        data = []
        for i, close in enumerate(prices[1:]):
            open_price = prices[i]
            high = max(open_price, close) * (1 + abs(np.random.normal(0, 0.005)))
            low = min(open_price, close) * (1 - abs(np.random.normal(0, 0.005)))

            data.append(
                {
                    "timestamp": pd.Timestamp("2024-01-01") + pd.Timedelta(minutes=i),
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": np.random.randint(100, 1000),
                }
            )

        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)
        return df

    def benchmark_signal_calculation(self, iterations: int = 100) -> Dict[str, float]:
        """
        信号计算性能对比

        Args:
            iterations: 测试迭代次数

        Returns:
            性能对比结果
        """
        print(f"🧪 信号计算性能对比测试 ({iterations}次迭代)")

        # 测试原始版本
        print("📊 测试原始版本...")
        original_times = []
        for i in range(iterations):
            start_time = time.perf_counter()
            _result = get_trading_signals(self.test_data)
            end_time = time.perf_counter()
            original_times.append(end_time - start_time)

            # 验证结果有效性
            if i == 0 and _result is not None:
                print(
                    f"   原始版本信号数量: {len(_result) if hasattr(_result, '__len__') else 'N/A'}"
                )

            if (i + 1) % 20 == 0:
                print(f"   进度: {i+1}/{iterations}")

        # 测试优化版本
        print("🚀 测试优化版本...")
        optimized_times = []
        for i in range(iterations):
            start_time = time.perf_counter()
            _result = get_trading_signals_optimized(self.test_data)
            end_time = time.perf_counter()
            optimized_times.append(end_time - start_time)

            # 验证结果有效性
            if i == 0 and _result is not None:
                print(
                    f"   优化版本信号数量: {len(_result) if hasattr(_result, '__len__') else 'N/A'}"
                )

            if (i + 1) % 20 == 0:
                print(f"   进度: {i+1}/{iterations}")

        # 计算统计结果
        original_avg = np.mean(original_times) * 1000  # 转换为ms
        original_p95 = np.percentile(original_times, 95) * 1000

        optimized_avg = np.mean(optimized_times) * 1000
        optimized_p95 = np.percentile(optimized_times, 95) * 1000

        improvement_avg = ((original_avg - optimized_avg) / original_avg) * 100
        improvement_p95 = ((original_p95 - optimized_p95) / original_p95) * 100

        results = {
            "original_avg_ms": original_avg,
            "original_p95_ms": original_p95,
            "optimized_avg_ms": optimized_avg,
            "optimized_p95_ms": optimized_p95,
            "improvement_avg_percent": improvement_avg,
            "improvement_p95_percent": improvement_p95,
            "iterations": iterations,
        }

        self._print_signal_results(results)
        return results

    def benchmark_with_cache(self, iterations: int = 50) -> Dict[str, float]:
        """
        缓存性能测试

        Args:
            iterations: 测试迭代次数

        Returns:
            缓存性能结果
        """
        print(f"🗄️  缓存性能测试 ({iterations}次迭代)")

        processor = VectorizedSignalProcessor()

        # 预热缓存
        processor.get_trading_signals_optimized(self.test_data)

        # 测试缓存性能
        cache_times = []
        for i in range(iterations):
            # 模拟新数据添加
            new_data = self.test_data.iloc[:-1].copy()
            new_row = self.test_data.iloc[-1:].copy()
            new_row.index = [new_row.index[0] + pd.Timedelta(minutes=1)]
            updated_data = pd.concat([new_data, new_row])

            start_time = time.perf_counter()
            _result = processor.get_trading_signals_optimized(updated_data)
            end_time = time.perf_counter()
            cache_times.append(end_time - start_time)

            # 验证缓存结果
            if i == 0 and _result is not None:
                print(
                    f"   缓存测试信号数量: {len(_result) if hasattr(_result, '__len__') else 'N/A'}"
                )

        cache_avg = np.mean(cache_times) * 1000
        cache_p95 = np.percentile(cache_times, 95) * 1000

        print(f"✅ 缓存性能: 平均 {cache_avg:.2f}ms, P95 {cache_p95:.2f}ms")

        return {"cache_avg_ms": cache_avg, "cache_p95_ms": cache_p95}

    def benchmark_atr_calculation(self, iterations: int = 100) -> Dict[str, float]:
        """ATR计算性能对比"""
        print(f"📈 ATR计算性能对比 ({iterations}次迭代)")

        from src.core.price_fetcher import calculate_atr
        from src.core.signal_processor_vectorized import OptimizedSignalProcessor

        processor = OptimizedSignalProcessor()

        # 原始ATR计算
        original_atr_times = []
        original_atr_values = []
        for i in range(iterations):
            start_time = time.perf_counter()
            atr = calculate_atr(self.test_data)
            end_time = time.perf_counter()
            original_atr_times.append(end_time - start_time)
            if i == 0:
                original_atr_values.append(atr)

        # 向量化ATR计算
        optimized_atr_times = []
        optimized_atr_values = []
        for i in range(iterations):
            start_time = time.perf_counter()
            _atr = processor.compute_atr_optimized(self.test_data)
            end_time = time.perf_counter()
            optimized_atr_times.append(end_time - start_time)
            if i == 0:
                optimized_atr_values.append(_atr)

        original_atr_avg = np.mean(original_atr_times) * 1000
        optimized_atr_avg = np.mean(optimized_atr_times) * 1000
        atr_improvement = ((original_atr_avg - optimized_atr_avg) / original_atr_avg) * 100

        print("📊 ATR性能对比:")
        print(
            f"   原始: {original_atr_avg:.2f}ms (ATR值: {original_atr_values[0] if original_atr_values else 'N/A'})"
        )
        print(
            f"   优化: {optimized_atr_avg:.2f}ms (ATR值: {optimized_atr_values[0] if optimized_atr_values else 'N/A'})"
        )
        print(f"   提升: {atr_improvement:+.1f}%")

        return {
            "atr_original_ms": original_atr_avg,
            "atr_optimized_ms": optimized_atr_avg,
            "atr_improvement_percent": atr_improvement,
        }

    def _print_signal_results(self, results: Dict[str, float]):
        """打印信号计算结果"""
        print("\n" + "=" * 60)
        print("🎯 向量化信号处理性能对比报告")
        print("=" * 60)

        print("📊 原始版本:")
        print(f"   平均延迟: {results['original_avg_ms']:.2f}ms")
        print(f"   P95延迟:  {results['original_p95_ms']:.2f}ms")

        print("\n🚀 优化版本:")
        print(f"   平均延迟: {results['optimized_avg_ms']:.2f}ms")
        print(f"   P95延迟:  {results['optimized_p95_ms']:.2f}ms")

        print("\n💡 性能改善:")
        print(f"   平均提升: {results['improvement_avg_percent']:+.1f}%")
        print(f"   P95提升:  {results['improvement_p95_percent']:+.1f}%")

        # 目标达成检查
        target_improvement = 30  # 30%目标
        if results["improvement_avg_percent"] >= target_improvement:
            print(f"✅ 达成目标: 超过{target_improvement}%改善")
        else:
            print(f"⚠️  未达目标: 需要{target_improvement}%改善")

        print("=" * 60)

    def run_full_benchmark(self) -> Dict[str, Any]:
        """运行完整性能测试"""
        print("🚀 M3阶段向量化性能全面测试")
        print(f"📊 测试数据: {len(self.test_data)}行OHLC数据")

        results = {}

        # 1. 信号计算性能
        results["signal"] = self.benchmark_signal_calculation(100)

        # 2. 缓存性能
        results["cache"] = self.benchmark_with_cache(50)

        # 3. ATR计算性能
        results["atr"] = self.benchmark_atr_calculation(100)

        # 4. 综合评估
        overall_improvement = results["signal"]["improvement_avg_percent"]
        print(f"\n🎯 综合性能改善: {overall_improvement:+.1f}%")

        if overall_improvement >= 30:
            print("🎉 M3优化目标达成: 超过30%性能提升！")
        elif overall_improvement >= 15:
            print("✅ 显著改善: 15-30%性能提升")
        else:
            print("⚠️  需要进一步优化")

        return results


def main():
    """主函数"""
    benchmark = VectorizationBenchmark()
    results = benchmark.run_full_benchmark()

    # 保存结果
    import json

    with open("output/vectorization_benchmark.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n✅ 测试结果已保存: output/vectorization_benchmark.json")


if __name__ == "__main__":
    main()
