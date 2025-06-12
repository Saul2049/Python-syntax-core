#!/usr/bin/env python3
"""
优化版信号处理器测试 - 提高覆盖率
Optimized Signal Processor Tests - Coverage Boost

重点关注:
- src/core/signal_processor_optimized.py (当前0%覆盖率)
"""

from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

from src.core.signal_processor_optimized import (
    OptimizedSignalProcessor,
    SignalCache,
    get_optimized_processor,
    get_trading_signals_optimized,
    validate_signal_optimized,
)


class TestSignalCache:
    """测试信号缓存器"""

    def setup_method(self):
        """测试前设置"""
        self.cache = SignalCache(max_size=3)

    def test_cache_initialization(self):
        """测试缓存初始化"""
        assert self.cache.max_size == 3
        assert len(self.cache.cache) == 0
        assert len(self.cache.access_times) == 0

    def test_cache_key_generation(self):
        """测试缓存键生成"""
        # 创建测试数据
        data = pd.DataFrame(
            {"close": [100, 101, 102], "high": [105, 106, 107], "low": [98, 99, 100]}
        )

        key1 = self.cache._generate_key(data, 5, 10)
        key2 = self.cache._generate_key(data, 5, 10)
        key3 = self.cache._generate_key(data, 7, 10)

        # 相同数据和参数应该生成相同的键
        assert key1 == key2
        # 不同参数应该生成不同的键
        assert key1 != key3

    def test_cache_set_and_get(self):
        """测试缓存设置和获取"""
        data = pd.DataFrame(
            {"close": [100, 101, 102], "high": [105, 106, 107], "low": [98, 99, 100]}
        )

        test_value = {"signal": "test"}

        # 设置缓存
        self.cache.set(data, 5, 10, test_value)

        # 获取缓存
        cached_value = self.cache.get(data, 5, 10)
        assert cached_value == test_value

        # 获取不存在的缓存
        not_found = self.cache.get(data, 7, 10)
        assert not_found is None

    def test_cache_size_limit(self):
        """测试缓存大小限制"""
        data_base = pd.DataFrame(
            {"close": [100, 101, 102], "high": [105, 106, 107], "low": [98, 99, 100]}
        )

        # 添加超过最大大小的缓存项
        for i in range(5):
            data = data_base + i  # 创建不同的数据
            self.cache.set(data, 5, 10, f"value_{i}")

        # 缓存大小不应超过限制
        assert len(self.cache.cache) <= self.cache.max_size


class TestOptimizedSignalProcessor:
    """测试优化版信号处理器"""

    def setup_method(self):
        """测试前设置"""
        self.processor = OptimizedSignalProcessor(enable_cache=True, cache_size=100)
        self.sample_data = self.create_sample_data()

    def create_sample_data(self):
        """创建示例数据"""
        periods = 50
        dates = pd.date_range("2024-01-01", periods=periods, freq="h")

        # 生成模拟价格数据
        np.random.seed(42)
        base_price = 100
        prices = []

        for i in range(periods):
            if i == 0:
                prices.append(base_price)
            else:
                change = np.random.normal(0, 0.02)
                new_price = prices[-1] * (1 + change)
                prices.append(max(new_price, base_price * 0.8))

        data = pd.DataFrame(
            {
                "close": prices,
                "high": [p * 1.02 for p in prices],
                "low": [p * 0.98 for p in prices],
                "open": prices,
                "volume": [1000 + np.random.randint(-100, 100) for _ in range(periods)],
            },
            index=dates,
        )

        return data

    def test_processor_initialization(self):
        """测试处理器初始化"""
        # 测试启用缓存的初始化
        processor_with_cache = OptimizedSignalProcessor(enable_cache=True)
        assert processor_with_cache.enable_cache is True
        assert processor_with_cache.cache is not None

        # 测试禁用缓存的初始化
        processor_no_cache = OptimizedSignalProcessor(enable_cache=False)
        assert processor_no_cache.enable_cache is False
        assert processor_no_cache.cache is None

    def test_calculate_moving_averages(self):
        """测试移动平均计算"""
        fast_win, slow_win = 5, 10

        fast_ma, slow_ma = self.processor.calculate_moving_averages(
            self.sample_data, fast_win, slow_win
        )

        # 验证返回的是pandas Series
        assert isinstance(fast_ma, pd.Series)
        assert isinstance(slow_ma, pd.Series)

        # 验证长度
        assert len(fast_ma) == len(self.sample_data)
        assert len(slow_ma) == len(self.sample_data)

        # 验证移动平均值的合理性
        assert not fast_ma.isna().all()
        assert not slow_ma.isna().all()

    def test_calculate_atr_optimized(self):
        """测试优化的ATR计算"""
        atr = self.processor.calculate_atr_optimized(self.sample_data)

        # 验证ATR是合理的正数
        assert isinstance(atr, float)
        assert atr >= 0

        # 测试不同的期间参数
        atr_14 = self.processor.calculate_atr_optimized(self.sample_data, period=14)
        atr_7 = self.processor.calculate_atr_optimized(self.sample_data, period=7)

        assert atr_14 >= 0
        assert atr_7 >= 0

    def test_calculate_atr_with_invalid_data(self):
        """测试ATR计算的异常处理"""
        # 测试空数据
        empty_data = pd.DataFrame()
        atr = self.processor.calculate_atr_optimized(empty_data)
        assert atr == 0.0

        # 测试缺少必要列的数据
        invalid_data = pd.DataFrame({"close": [100, 101, 102]})
        atr = self.processor.calculate_atr_optimized(invalid_data)
        assert atr == 0.0

    def test_detect_crossover(self):
        """测试交叉检测"""
        # 创建测试的移动平均数据
        fast_ma = pd.Series([98, 99, 101, 102])  # 上升趋势
        slow_ma = pd.Series([100, 100, 100, 100])  # 平稳趋势

        crossover = self.processor.detect_crossover(fast_ma, slow_ma)

        # 验证返回格式
        assert isinstance(crossover, dict)
        assert "buy_signal" in crossover
        assert "sell_signal" in crossover
        assert isinstance(crossover["buy_signal"], bool)
        assert isinstance(crossover["sell_signal"], bool)

    def test_detect_crossover_insufficient_data(self):
        """测试数据不足时的交叉检测"""
        # 数据长度小于2
        short_fast = pd.Series([100])
        short_slow = pd.Series([100])

        crossover = self.processor.detect_crossover(short_fast, short_slow)

        # 应该返回False信号
        assert crossover["buy_signal"] is False
        assert crossover["sell_signal"] is False

    @patch("src.monitoring.metrics_collector.get_metrics_collector")
    def test_get_trading_signals_optimized(self, mock_metrics):
        """测试优化版交易信号获取"""
        # 模拟metrics collector
        mock_collector = Mock()
        mock_collector.measure_signal_latency.return_value.__enter__ = Mock()
        mock_collector.measure_signal_latency.return_value.__exit__ = Mock()
        mock_metrics.return_value = mock_collector

        # 创建新的处理器以使用模拟的metrics
        processor = OptimizedSignalProcessor()

        signals = processor.get_trading_signals_optimized(self.sample_data)

        # 验证信号格式
        assert isinstance(signals, dict)
        required_keys = [
            "current_price",
            "fast_ma",
            "slow_ma",
            "buy_signal",
            "sell_signal",
            "atr",
            "timestamp",
            "data_points",
        ]
        for key in required_keys:
            assert key in signals

        # 验证数据类型
        assert isinstance(signals["current_price"], float)
        assert isinstance(signals["buy_signal"], bool)
        assert isinstance(signals["sell_signal"], bool)
        assert signals["data_points"] == len(self.sample_data)

    def test_get_trading_signals_with_cache(self):
        """测试带缓存的信号获取"""
        # 第一次调用
        signals1 = self.processor.get_trading_signals_optimized(self.sample_data)

        # 第二次调用相同参数（应该从缓存获取）
        signals2 = self.processor.get_trading_signals_optimized(self.sample_data)

        # 结果应该相同
        assert signals1 == signals2

    def test_get_trading_signals_insufficient_data(self):
        """测试数据不足时的信号获取"""
        # 创建数据不足的DataFrame
        small_data = self.sample_data.head(5)  # 只有5行数据，少于slow_win

        signals = self.processor.get_trading_signals_optimized(small_data, fast_win=7, slow_win=25)

        # 应该返回空信号的关键字段
        empty_signals = self.processor._get_empty_signals()
        assert signals["current_price"] == empty_signals["current_price"]
        assert signals["buy_signal"] == empty_signals["buy_signal"]
        assert signals["sell_signal"] == empty_signals["sell_signal"]

    def test_get_trading_signals_with_none_data(self):
        """测试空数据的信号获取"""
        # 测试None数据 - 这会在缓存层面触发异常，由异常处理返回空信号
        # 由于缓存键生成的问题，我们直接测试异常处理路径

        # 创建一个禁用缓存的处理器来测试None数据处理
        processor_no_cache = OptimizedSignalProcessor(enable_cache=False)
        signals = processor_no_cache.get_trading_signals_optimized(None)

        # 应该返回空信号的关键字段（由于异常处理）
        empty_signals = processor_no_cache._get_empty_signals()
        assert signals["current_price"] == empty_signals["current_price"]
        assert signals["buy_signal"] == empty_signals["buy_signal"]
        assert signals["sell_signal"] == empty_signals["sell_signal"]

    def test_validate_signal_optimized(self):
        """测试信号验证"""
        # 获取有效信号
        signals = self.processor.get_trading_signals_optimized(self.sample_data)

        # 验证信号
        is_valid = self.processor.validate_signal_optimized(signals, self.sample_data)
        assert isinstance(is_valid, bool)
        assert is_valid is True  # 正常信号应该有效

    def test_validate_signal_optimized_invalid(self):
        """测试无效信号验证"""
        # 创建无效信号
        invalid_signals = {
            "current_price": -1,  # 负价格
            "fast_ma": 0,
            "slow_ma": 0,
            "buy_signal": False,
            "sell_signal": False,
        }

        is_valid = self.processor.validate_signal_optimized(invalid_signals, self.sample_data)
        assert is_valid is False

    def test_get_cache_stats(self):
        """测试缓存统计"""
        # 生成一些缓存数据
        self.processor.get_trading_signals_optimized(self.sample_data)

        stats = self.processor.get_cache_stats()

        # 验证统计信息格式
        assert isinstance(stats, dict)
        assert "enabled" in stats
        if stats["enabled"]:
            assert "size" in stats
            assert "max_size" in stats


class TestModuleFunctions:
    """测试模块级函数"""

    def test_get_optimized_processor(self):
        """测试获取优化处理器"""
        processor = get_optimized_processor()
        assert isinstance(processor, OptimizedSignalProcessor)

    def test_get_trading_signals_optimized_function(self):
        """测试模块级信号获取函数"""
        # 创建测试数据
        data = pd.DataFrame(
            {
                "close": [100, 101, 102, 103, 104],
                "high": [105, 106, 107, 108, 109],
                "low": [98, 99, 100, 101, 102],
            }
        )

        signals = get_trading_signals_optimized(data)

        # 验证返回格式
        assert isinstance(signals, dict)
        assert "current_price" in signals
        assert "buy_signal" in signals
        assert "sell_signal" in signals

    def test_validate_signal_optimized_function(self):
        """测试模块级信号验证函数"""
        # 创建测试数据和信号
        data = pd.DataFrame(
            {"close": [100, 101, 102], "high": [105, 106, 107], "low": [98, 99, 100]}
        )

        signals = {
            "current_price": 102,
            "fast_ma": 101,
            "slow_ma": 100,
            "buy_signal": True,
            "sell_signal": False,
        }

        is_valid = validate_signal_optimized(signals, data)
        assert isinstance(is_valid, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
