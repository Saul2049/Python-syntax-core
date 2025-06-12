#!/usr/bin/env python3
"""
向量化信号处理器和信号缓存测试 - 提高覆盖率
Vectorized Signal Processor and Cache Tests - Coverage Boost

重点关注:
- src/core/signal_processor_vectorized.py (当前0%覆盖率)
- src/core/signal_cache.py (当前0%覆盖率)
"""


import numpy as np
import pandas as pd
import pytest

from src.core.signal_cache import SignalCache
from src.core.signal_processor_vectorized import (
    OptimizedSignalProcessor,
    fast_atr,
    fast_ema,
    get_trading_signals_optimized,
    validate_signal_optimized,
)


class TestVectorizedFunctions:
    """测试向量化函数"""

    def test_fast_ema(self):
        """测试快速EMA计算"""
        # 创建测试价格数据
        prices = np.array([100, 101, 102, 103, 104, 105])
        window = 3

        ema = fast_ema(prices, window)

        # 验证返回值类型和长度
        assert isinstance(ema, np.ndarray)
        assert len(ema) == len(prices)

        # EMA应该是递增趋势（对于递增价格）
        assert ema[-1] > ema[0]

        # 验证EMA值的合理性
        assert all(np.isfinite(ema))

    def test_fast_ema_edge_cases(self):
        """测试EMA的边界情况"""
        # 单个价格
        single_price = np.array([100])
        ema_single = fast_ema(single_price, 5)
        assert len(ema_single) == 1
        assert ema_single[0] == 100

        # 窗口大小等于数据长度
        prices = np.array([100, 102, 104])
        ema_equal_window = fast_ema(prices, 3)
        assert len(ema_equal_window) == 3

    def test_fast_atr(self):
        """测试快速ATR计算"""
        # 创建测试OHLC数据
        periods = 20
        high = np.random.uniform(100, 110, periods)
        low = np.random.uniform(90, 100, periods)
        close = np.random.uniform(95, 105, periods)

        # 确保high >= low
        high = np.maximum(high, low + 1)

        atr = fast_atr(high, low, close, window=14)

        # 验证返回值
        assert isinstance(atr, np.ndarray)
        assert len(atr) == len(high)
        assert all(atr >= 0)  # ATR应该非负
        assert all(np.isfinite(atr))

    def test_fast_atr_minimal_data(self):
        """测试ATR计算的最小数据集"""
        # 最小数据集
        high = np.array([105, 106, 107])
        low = np.array([98, 99, 100])
        close = np.array([102, 103, 104])

        atr = fast_atr(high, low, close, window=2)

        assert isinstance(atr, np.ndarray)
        assert len(atr) == 3
        assert all(atr >= 0)


class TestOptimizedSignalProcessor:
    """测试优化版向量化信号处理器"""

    def setup_method(self):
        """测试前设置"""
        self.processor = OptimizedSignalProcessor()
        self.sample_data = self.create_sample_data()

    def create_sample_data(self):
        """创建示例数据"""
        periods = 50
        dates = pd.date_range("2024-01-01", periods=periods, freq="h")

        # 生成模拟OHLC数据
        np.random.seed(42)
        base_price = 100

        data = []
        for i in range(periods):
            if i == 0:
                close = base_price
            else:
                change = np.random.normal(0, 0.02)
                close = max(data[-1]["close"] * (1 + change), base_price * 0.8)

            # 生成OHLC
            high = close * (1 + abs(np.random.normal(0, 0.01)))
            low = close * (1 - abs(np.random.normal(0, 0.01)))
            open_price = close + np.random.normal(0, close * 0.005)

            data.append(
                {
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": 1000 + np.random.randint(-100, 100),
                }
            )

        df = pd.DataFrame(data, index=dates)
        return df

    def test_processor_initialization(self):
        """测试处理器初始化"""
        processor = OptimizedSignalProcessor()

        assert hasattr(processor, "_cache")
        assert hasattr(processor, "_last_data_hash")
        assert isinstance(processor._cache, dict)
        assert processor._last_data_hash is None

    def test_get_trading_signals_optimized(self):
        """测试优化版交易信号获取"""
        signals = self.processor.get_trading_signals_optimized(self.sample_data)

        # 验证信号格式
        required_keys = [
            "buy_signal",
            "sell_signal",
            "current_price",
            "fast_ma",
            "slow_ma",
            "last_timestamp",
        ]
        for key in required_keys:
            assert key in signals

        # 验证数据类型
        assert isinstance(signals["buy_signal"], bool)
        assert isinstance(signals["sell_signal"], bool)
        assert isinstance(signals["current_price"], float)
        assert isinstance(signals["fast_ma"], float)
        assert isinstance(signals["slow_ma"], float)

        # 验证数值的合理性
        assert signals["current_price"] > 0
        assert signals["fast_ma"] > 0
        assert signals["slow_ma"] > 0

    def test_get_trading_signals_with_cache(self):
        """测试带缓存的信号获取"""
        # 第一次调用
        signals1 = self.processor.get_trading_signals_optimized(self.sample_data)

        # 第二次调用相同数据（应该使用缓存）
        signals2 = self.processor.get_trading_signals_optimized(self.sample_data)

        # 验证结果相同
        assert signals1 == signals2

    def test_get_trading_signals_different_windows(self):
        """测试不同窗口参数的信号获取"""
        signals_default = self.processor.get_trading_signals_optimized(self.sample_data)
        signals_custom = self.processor.get_trading_signals_optimized(
            self.sample_data, fast_win=5, slow_win=15
        )

        # 不同参数应该产生不同的结果
        assert (
            signals_default["fast_ma"] != signals_custom["fast_ma"]
            or signals_default["slow_ma"] != signals_custom["slow_ma"]
        )

    def test_get_trading_signals_empty_data(self):
        """测试空数据的信号获取"""
        empty_df = pd.DataFrame()
        signals = self.processor.get_trading_signals_optimized(empty_df)

        # 应该返回空信号
        empty_signals = self.processor._empty_signal()
        assert signals == empty_signals

    def test_detect_crossover_fast(self):
        """测试快速交叉检测"""
        # 创建明确的金叉场景：快线从下方穿越到上方
        fast_ma = np.array([98, 99, 100, 102])  # 从低到高穿越100
        slow_ma = np.array([100, 100, 100, 100])  # 保持在100

        buy_signal, sell_signal = self.processor._detect_crossover_fast(fast_ma, slow_ma)

        # 验证返回值类型
        assert isinstance(buy_signal, bool)
        assert isinstance(sell_signal, bool)

        # 快线从下方(99<100)穿越到上方(102>100)，应该有买入信号
        assert buy_signal is True
        assert sell_signal is False

        # 测试死叉场景：快线从上方穿越到下方
        fast_ma_sell = np.array([102, 101, 100, 98])  # 从高到低穿越100
        slow_ma_sell = np.array([100, 100, 100, 100])  # 保持在100

        buy_signal_sell, sell_signal_sell = self.processor._detect_crossover_fast(
            fast_ma_sell, slow_ma_sell
        )

        # 应该有卖出信号
        assert buy_signal_sell is False
        assert sell_signal_sell is True

    def test_detect_crossover_insufficient_data(self):
        """测试数据不足时的交叉检测"""
        short_fast = np.array([100])
        short_slow = np.array([100])

        buy_signal, sell_signal = self.processor._detect_crossover_fast(short_fast, short_slow)

        # 数据不足应该返回False
        assert buy_signal is False
        assert sell_signal is False

    def test_empty_signal(self):
        """测试空信号方法"""
        empty_signals = self.processor._empty_signal()

        # 验证空信号格式
        assert isinstance(empty_signals, dict)
        assert empty_signals["buy_signal"] is False
        assert empty_signals["sell_signal"] is False
        assert empty_signals["current_price"] == 0.0
        assert empty_signals["fast_ma"] == 0.0
        assert empty_signals["slow_ma"] == 0.0
        assert empty_signals["last_timestamp"] is None

    def test_compute_atr_optimized(self):
        """测试优化版ATR计算"""
        atr = self.processor.compute_atr_optimized(self.sample_data)

        # 验证ATR值
        assert isinstance(atr, float)
        assert atr >= 0
        assert not np.isnan(atr)

    def test_compute_atr_insufficient_data(self):
        """测试数据不足时的ATR计算"""
        small_data = self.sample_data.head(5)
        atr = self.processor.compute_atr_optimized(small_data, window=14)

        # 数据不足应该返回0
        assert atr == 0.0

    def test_compute_atr_missing_columns(self):
        """测试缺少列时的ATR计算"""
        # 只有close列的数据
        close_only_data = pd.DataFrame({"close": [100, 101, 102, 103, 104]})

        atr = self.processor.compute_atr_optimized(close_only_data)

        # 应该使用简化版本计算
        assert isinstance(atr, float)
        assert atr >= 0

    def test_get_cache_stats(self):
        """测试缓存统计"""
        # 生成一些缓存数据
        self.processor.get_trading_signals_optimized(self.sample_data)

        stats = self.processor.get_cache_stats()

        # 验证统计信息
        assert isinstance(stats, dict)
        assert "enabled" in stats
        assert "size" in stats
        assert "max_size" in stats
        assert stats["enabled"] is True
        assert stats["size"] >= 0
        assert stats["max_size"] == 100


class TestSignalCache:
    """测试信号缓存"""

    def setup_method(self):
        """测试前设置"""
        self.cache = SignalCache()

    def test_cache_initialization(self):
        """测试缓存初始化"""
        assert hasattr(self.cache, "cache")
        assert isinstance(self.cache.cache, dict)
        assert len(self.cache.cache) == 0

    def test_cache_set_and_get(self):
        """测试缓存设置和获取"""
        key = "test_key"
        value = {"signal": "test_value"}

        # 设置缓存
        self.cache.set(key, value)

        # 获取缓存
        cached_value = self.cache.get(key)
        assert cached_value == value

        # 获取不存在的键
        non_existent = self.cache.get("non_existent_key")
        assert non_existent is None

    def test_cache_clear(self):
        """测试缓存清空"""
        # 添加一些数据
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")

        assert len(self.cache.cache) == 2

        # 清空缓存
        self.cache.clear()

        assert len(self.cache.cache) == 0

    def test_cache_size(self):
        """测试缓存大小"""
        # 初始大小应该为0
        assert self.cache.size() == 0

        # 添加数据
        self.cache.set("key1", "value1")
        assert self.cache.size() == 1

        self.cache.set("key2", "value2")
        assert self.cache.size() == 2

        # 清空后大小应该为0
        self.cache.clear()
        assert self.cache.size() == 0

    def test_cache_overwrite(self):
        """测试缓存覆盖"""
        key = "test_key"
        value1 = "value1"
        value2 = "value2"

        # 设置初始值
        self.cache.set(key, value1)
        assert self.cache.get(key) == value1

        # 覆盖值
        self.cache.set(key, value2)
        assert self.cache.get(key) == value2

        # 缓存大小应该仍然是1
        assert self.cache.size() == 1


class TestModuleFunctions:
    """测试模块级函数"""

    def create_test_data(self):
        """创建测试数据"""
        periods = 30
        dates = pd.date_range("2024-01-01", periods=periods, freq="h")

        data = pd.DataFrame(
            {
                "close": np.random.uniform(90, 110, periods),
                "high": np.random.uniform(105, 115, periods),
                "low": np.random.uniform(85, 95, periods),
                "open": np.random.uniform(95, 105, periods),
                "volume": np.random.uniform(1000, 2000, periods),
            },
            index=dates,
        )

        return data

    def test_get_trading_signals_optimized_function(self):
        """测试模块级信号获取函数"""
        data = self.create_test_data()

        signals = get_trading_signals_optimized(data)

        # 验证返回格式
        assert isinstance(signals, dict)
        assert "buy_signal" in signals
        assert "sell_signal" in signals
        assert "current_price" in signals

    def test_validate_signal_optimized_function(self):
        """测试模块级信号验证函数"""
        data = self.create_test_data()

        # 创建有效信号
        valid_signal = {
            "buy_signal": True,
            "sell_signal": False,
            "current_price": 100.0,
            "fast_ma": 99.0,
            "slow_ma": 98.0,
        }

        is_valid = validate_signal_optimized(valid_signal, data)
        assert isinstance(is_valid, bool)

    def test_validate_signal_optimized_invalid_signal(self):
        """测试无效信号验证"""
        data = self.create_test_data()

        # 创建无效信号（缺少必要字段）
        invalid_signal = {
            "buy_signal": True
            # 缺少其他必要字段
        }

        is_valid = validate_signal_optimized(invalid_signal, data)
        assert is_valid is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
