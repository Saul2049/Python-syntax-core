#!/usr/bin/env python3
"""
优化版信号处理器测试模块
测试 src.core.signal_processor_optimized 模块的所有功能
"""

import time
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

from src.core.signal_processor_optimized import (
    OptimizedSignalProcessor,
    SignalCache,
    get_optimized_processor,
    get_trading_signals_optimized,
    validate_signal_optimized,
)


class TestSignalCache:
    """测试SignalCache类"""

    def setup_method(self):
        """测试前准备"""
        self.cache = SignalCache(max_size=3)
        self.sample_data = pd.DataFrame(
            {
                "close": [100, 101, 102, 103, 104],
                "high": [101, 102, 103, 104, 105],
                "low": [99, 100, 101, 102, 103],
            }
        )

    def test_init(self):
        """测试初始化"""
        cache = SignalCache(max_size=100)
        assert cache.max_size == 100
        assert len(cache.cache) == 0
        assert len(cache.access_times) == 0

    def test_generate_key(self):
        """测试缓存键生成"""
        key1 = self.cache._generate_key(self.sample_data, 5, 10)
        key2 = self.cache._generate_key(self.sample_data, 5, 10)
        key3 = self.cache._generate_key(self.sample_data, 7, 10)

        # 相同参数应生成相同键
        assert key1 == key2
        # 不同参数应生成不同键
        assert key1 != key3
        # 键应包含参数信息
        assert "5_10" in key1
        assert "7_10" in key3

    def test_cache_operations(self):
        """测试缓存的基本操作"""
        test_value = {"signal": "buy", "price": 100.0}

        # 测试设置和获取
        self.cache.set(self.sample_data, 5, 10, test_value)
        result = self.cache.get(self.sample_data, 5, 10)
        assert result == test_value

        # 测试缓存未命中
        result = self.cache.get(self.sample_data, 7, 14)
        assert result is None

    def test_cache_size_limit(self):
        """测试缓存大小限制"""
        # 添加超过最大大小的条目
        for i in range(5):
            test_data = pd.DataFrame({"close": [100 + i]})
            self.cache.set(test_data, i, i + 1, {"value": i})

        # 缓存大小应不超过限制
        assert len(self.cache.cache) <= self.cache.max_size

    def test_cache_lru_eviction(self):
        """测试LRU淘汰机制"""
        # 填满缓存
        data_sets = []
        for i in range(3):
            data = pd.DataFrame({"close": [100 + i]})
            data_sets.append(data)
            self.cache.set(data, i, i + 1, {"value": i})

        # 访问第一个条目
        self.cache.get(data_sets[0], 0, 1)
        time.sleep(0.01)  # 确保时间差异

        # 添加新条目，应该淘汰最老的未访问条目
        new_data = pd.DataFrame({"close": [200]})
        self.cache.set(new_data, 10, 11, {"value": "new"})

        # 第一个条目应该还在（因为最近访问过）
        assert self.cache.get(data_sets[0], 0, 1) is not None


class TestOptimizedSignalProcessor:
    """测试OptimizedSignalProcessor类"""

    def setup_method(self):
        """测试前准备"""
        self.processor = OptimizedSignalProcessor(enable_cache=True, cache_size=10)
        self.sample_data = pd.DataFrame(
            {
                "close": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 104.0, 103.0],
                "high": [101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 105.0, 104.0],
                "low": [99.0, 100.0, 101.0, 102.0, 103.0, 104.0, 103.0, 102.0],
            }
        )

    def test_init_with_cache(self):
        """测试带缓存的初始化"""
        processor = OptimizedSignalProcessor(enable_cache=True, cache_size=50)
        assert processor.enable_cache is True
        assert processor.cache is not None
        assert processor.cache.max_size == 50

    def test_init_without_cache(self):
        """测试不带缓存的初始化"""
        processor = OptimizedSignalProcessor(enable_cache=False)
        assert processor.enable_cache is False
        assert processor.cache is None

    def test_calculate_moving_averages(self):
        """测试移动平均计算"""
        fast_ma, slow_ma = self.processor.calculate_moving_averages(
            self.sample_data, fast_win=3, slow_win=5
        )

        # 检查返回类型
        assert isinstance(fast_ma, pd.Series)
        assert isinstance(slow_ma, pd.Series)

        # 检查长度
        assert len(fast_ma) == len(self.sample_data)
        assert len(slow_ma) == len(self.sample_data)

        # 检查数值合理性
        assert fast_ma.iloc[-1] > 0
        assert slow_ma.iloc[-1] > 0

    def test_calculate_atr_optimized_normal(self):
        """测试正常情况下的ATR计算"""
        atr = self.processor.calculate_atr_optimized(self.sample_data, period=3)

        assert isinstance(atr, float)
        assert atr >= 0.0

    def test_calculate_atr_optimized_insufficient_data(self):
        """测试数据不足时的ATR计算"""
        small_data = pd.DataFrame(
            {
                "close": [100.0],
                "high": [101.0],
                "low": [99.0],
            }
        )
        atr = self.processor.calculate_atr_optimized(small_data)
        assert atr >= 0.0

    def test_calculate_atr_optimized_error_handling(self):
        """测试ATR计算的错误处理"""
        # 使用无效数据
        invalid_data = pd.DataFrame({"invalid": [1, 2, 3]})

        # Mock实例的logger
        with patch.object(self.processor, "logger") as mock_logger:
            atr = self.processor.calculate_atr_optimized(invalid_data)

            assert atr == 0.0
            # 验证错误被记录
            mock_logger.error.assert_called()

    def test_detect_crossover_buy_signal(self):
        """测试买入信号检测（金叉）"""
        # 构造金叉数据：快线上穿慢线
        fast_ma = pd.Series([10.0, 11.0, 12.0])
        slow_ma = pd.Series([11.0, 11.0, 11.0])

        result = self.processor.detect_crossover(fast_ma, slow_ma)

        assert result["buy_signal"] is True
        assert result["sell_signal"] is False

    def test_detect_crossover_sell_signal(self):
        """测试卖出信号检测（死叉）"""
        # 构造死叉数据：快线下穿慢线
        fast_ma = pd.Series([12.0, 11.0, 10.0])
        slow_ma = pd.Series([11.0, 11.0, 11.0])

        result = self.processor.detect_crossover(fast_ma, slow_ma)

        assert result["buy_signal"] is False
        assert result["sell_signal"] is True

    def test_detect_crossover_no_signal(self):
        """测试无信号情况"""
        # 构造无交叉数据
        fast_ma = pd.Series([10.0, 10.5, 11.0])
        slow_ma = pd.Series([12.0, 12.0, 12.0])

        result = self.processor.detect_crossover(fast_ma, slow_ma)

        assert result["buy_signal"] is False
        assert result["sell_signal"] is False

    def test_detect_crossover_insufficient_data(self):
        """测试数据不足的交叉检测"""
        fast_ma = pd.Series([10.0])
        slow_ma = pd.Series([11.0])

        result = self.processor.detect_crossover(fast_ma, slow_ma)

        assert result["buy_signal"] is False
        assert result["sell_signal"] is False

    @patch("src.monitoring.metrics_collector.get_metrics_collector")
    def test_get_trading_signals_optimized_normal(self, mock_metrics):
        """测试正常情况下的交易信号计算"""
        # Mock metrics collector
        mock_collector = MagicMock()
        mock_collector.measure_signal_latency.return_value.__enter__ = MagicMock()
        mock_collector.measure_signal_latency.return_value.__exit__ = MagicMock()
        mock_metrics.return_value = mock_collector

        result = self.processor.get_trading_signals_optimized(
            self.sample_data, fast_win=3, slow_win=5
        )

        # 检查返回结构
        expected_keys = [
            "current_price",
            "fast_ma",
            "slow_ma",
            "buy_signal",
            "sell_signal",
            "atr",
            "timestamp",
            "data_points",
        ]
        for key in expected_keys:
            assert key in result

        # 检查数值类型
        assert isinstance(result["current_price"], float)
        assert isinstance(result["fast_ma"], float)
        assert isinstance(result["slow_ma"], float)
        assert isinstance(result["buy_signal"], bool)
        assert isinstance(result["sell_signal"], bool)
        assert isinstance(result["atr"], float)
        assert isinstance(result["data_points"], int)

    def test_get_trading_signals_optimized_insufficient_data(self):
        """测试数据不足时的信号计算"""
        small_data = pd.DataFrame({"close": [100.0]})

        result = self.processor.get_trading_signals_optimized(small_data, fast_win=5, slow_win=10)

        # 应该返回空信号
        assert "error" in result
        assert result["current_price"] == 0.0

    def test_get_trading_signals_optimized_none_data(self):
        """测试空数据的信号计算"""
        # 使用禁用缓存的处理器来避免缓存键生成问题
        processor_no_cache = OptimizedSignalProcessor(enable_cache=False)
        result = processor_no_cache.get_trading_signals_optimized(None, fast_win=5, slow_win=10)

        # 应该返回空信号
        assert "error" in result
        assert result["current_price"] == 0.0

    def test_get_trading_signals_optimized_with_cache(self):
        """测试带缓存的信号计算"""
        # 第一次计算
        result1 = self.processor.get_trading_signals_optimized(
            self.sample_data, fast_win=3, slow_win=5
        )

        # 第二次计算（应该使用缓存）
        result2 = self.processor.get_trading_signals_optimized(
            self.sample_data, fast_win=3, slow_win=5
        )

        # 结果应该相同
        assert result1["current_price"] == result2["current_price"]
        assert result1["fast_ma"] == result2["fast_ma"]

    def test_get_trading_signals_optimized_error_handling(self):
        """测试信号计算的错误处理"""
        # 使用会导致异常的数据（空DataFrame但有列名）
        invalid_data = pd.DataFrame(columns=["close", "high", "low"])

        result = self.processor.get_trading_signals_optimized(invalid_data, fast_win=3, slow_win=5)

        # 应该返回空信号（因为数据不足）
        assert "error" in result
        assert result["current_price"] == 0.0

    def test_get_empty_signals(self):
        """测试空信号生成"""
        result = self.processor._get_empty_signals()

        expected_keys = [
            "current_price",
            "fast_ma",
            "slow_ma",
            "buy_signal",
            "sell_signal",
            "atr",
            "timestamp",
            "data_points",
            "error",
        ]
        for key in expected_keys:
            assert key in result

        assert result["current_price"] == 0.0
        assert result["buy_signal"] is False
        assert result["sell_signal"] is False

    def test_validate_signal_optimized_valid(self):
        """测试有效信号验证"""
        valid_signals = {
            "current_price": 100.0,
            "fast_ma": 99.0,
            "slow_ma": 101.0,
            "buy_signal": True,
            "sell_signal": False,
            "atr": 1.5,
            "data_points": 10,
        }

        result = self.processor.validate_signal_optimized(valid_signals, self.sample_data)
        assert result is True

    def test_validate_signal_optimized_invalid_price(self):
        """测试无效价格的信号验证"""
        invalid_signals = {
            "current_price": 0.0,  # 无效价格
            "fast_ma": 99.0,
            "slow_ma": 101.0,
            "buy_signal": False,
            "sell_signal": False,
            "atr": 1.5,
            "data_points": 10,
        }

        result = self.processor.validate_signal_optimized(invalid_signals, self.sample_data)
        assert result is False

    def test_validate_signal_optimized_invalid_ma(self):
        """测试无效移动平均的信号验证"""
        invalid_signals = {
            "current_price": 100.0,
            "fast_ma": 0.0,  # 无效移动平均
            "slow_ma": 101.0,
            "buy_signal": False,
            "sell_signal": False,
            "atr": 1.5,
            "data_points": 10,
        }

        result = self.processor.validate_signal_optimized(invalid_signals, self.sample_data)
        assert result is False

    def test_validate_signal_optimized_negative_atr(self):
        """测试负ATR的信号验证"""
        invalid_signals = {
            "current_price": 100.0,
            "fast_ma": 99.0,
            "slow_ma": 101.0,
            "buy_signal": False,
            "sell_signal": False,
            "atr": -1.0,  # 负ATR
            "data_points": 10,
        }

        result = self.processor.validate_signal_optimized(invalid_signals, self.sample_data)
        assert result is False

    def test_validate_signal_optimized_insufficient_data_points(self):
        """测试数据点不足的信号验证"""
        invalid_signals = {
            "current_price": 100.0,
            "fast_ma": 99.0,
            "slow_ma": 101.0,
            "buy_signal": False,
            "sell_signal": False,
            "atr": 1.5,
            "data_points": 1,  # 数据点不足
        }

        result = self.processor.validate_signal_optimized(invalid_signals, self.sample_data)
        assert result is False

    def test_validate_signal_optimized_conflicting_signals(self):
        """测试冲突信号的验证"""
        invalid_signals = {
            "current_price": 100.0,
            "fast_ma": 99.0,
            "slow_ma": 101.0,
            "buy_signal": True,  # 同时有买卖信号
            "sell_signal": True,
            "atr": 1.5,
            "data_points": 10,
        }

        result = self.processor.validate_signal_optimized(invalid_signals, self.sample_data)
        assert result is False

    def test_validate_signal_optimized_with_error(self):
        """测试包含错误的信号验证"""
        invalid_signals = {
            "error": "Some error occurred",
            "current_price": 100.0,
        }

        result = self.processor.validate_signal_optimized(invalid_signals, self.sample_data)
        assert result is False

    def test_validate_signal_optimized_empty_signals(self):
        """测试空信号验证"""
        result = self.processor.validate_signal_optimized({}, self.sample_data)
        assert result is False

        result = self.processor.validate_signal_optimized(None, self.sample_data)
        assert result is False

    def test_validate_signal_optimized_exception(self):
        """测试信号验证的异常处理"""
        # 使用会导致异常的信号数据
        invalid_signals = {"current_price": "invalid"}  # 字符串而不是数字

        # Mock实例的logger
        with patch.object(self.processor, "logger") as mock_logger:
            result = self.processor.validate_signal_optimized(invalid_signals, self.sample_data)
            assert result is False
            # 验证错误被记录
            mock_logger.error.assert_called()

    def test_get_cache_stats_enabled(self):
        """测试启用缓存时的统计信息"""
        stats = self.processor.get_cache_stats()

        assert stats["enabled"] is True
        assert "size" in stats
        assert "max_size" in stats
        assert stats["max_size"] == 10

    def test_get_cache_stats_disabled(self):
        """测试禁用缓存时的统计信息"""
        processor = OptimizedSignalProcessor(enable_cache=False)
        stats = processor.get_cache_stats()

        assert stats["enabled"] is False


class TestGlobalFunctions:
    """测试全局函数"""

    def setup_method(self):
        """测试前准备"""
        self.sample_data = pd.DataFrame(
            {
                "close": [100.0, 101.0, 102.0, 103.0, 104.0],
                "high": [101.0, 102.0, 103.0, 104.0, 105.0],
                "low": [99.0, 100.0, 101.0, 102.0, 103.0],
            }
        )

    def test_get_optimized_processor_singleton(self):
        """测试全局处理器单例模式"""
        processor1 = get_optimized_processor()
        processor2 = get_optimized_processor()

        # 应该返回同一个实例
        assert processor1 is processor2
        assert isinstance(processor1, OptimizedSignalProcessor)

    @patch("src.monitoring.metrics_collector.get_metrics_collector")
    def test_get_trading_signals_optimized_function(self, mock_metrics):
        """测试全局交易信号计算函数"""
        # Mock metrics collector
        mock_collector = MagicMock()
        mock_collector.measure_signal_latency.return_value.__enter__ = MagicMock()
        mock_collector.measure_signal_latency.return_value.__exit__ = MagicMock()
        mock_metrics.return_value = mock_collector

        result = get_trading_signals_optimized(self.sample_data, fast_win=3, slow_win=5)

        # 检查返回结构
        expected_keys = [
            "current_price",
            "fast_ma",
            "slow_ma",
            "buy_signal",
            "sell_signal",
            "atr",
            "timestamp",
            "data_points",
        ]
        for key in expected_keys:
            assert key in result

    def test_validate_signal_optimized_function(self):
        """测试全局信号验证函数"""
        valid_signals = {
            "current_price": 100.0,
            "fast_ma": 99.0,
            "slow_ma": 101.0,
            "buy_signal": False,
            "sell_signal": False,
            "atr": 1.5,
            "data_points": 10,
        }

        result = validate_signal_optimized(valid_signals, self.sample_data)
        assert result is True


class TestEdgeCases:
    """测试边界情况"""

    def test_extreme_window_sizes(self):
        """测试极端窗口大小"""
        processor = OptimizedSignalProcessor()
        data = pd.DataFrame(
            {
                "close": list(range(100)),
                "high": list(range(1, 101)),
                "low": list(range(-1, 99)),
            }
        )

        # 测试非常大的窗口
        result = processor.get_trading_signals_optimized(data, fast_win=50, slow_win=90)
        assert "error" not in result

        # 测试窗口大小为1
        result = processor.get_trading_signals_optimized(data, fast_win=1, slow_win=2)
        assert "error" not in result

    def test_identical_window_sizes(self):
        """测试相同的窗口大小"""
        processor = OptimizedSignalProcessor()
        data = pd.DataFrame(
            {
                "close": [100, 101, 102, 103, 104],
                "high": [101, 102, 103, 104, 105],
                "low": [99, 100, 101, 102, 103],
            }
        )

        result = processor.get_trading_signals_optimized(data, fast_win=3, slow_win=3)
        # 相同窗口大小不应产生交叉信号
        assert result["buy_signal"] is False
        assert result["sell_signal"] is False

    def test_nan_values_in_data(self):
        """测试数据中包含NaN值"""
        processor = OptimizedSignalProcessor()
        data = pd.DataFrame(
            {
                "close": [100, np.nan, 102, 103, 104],
                "high": [101, 102, np.nan, 104, 105],
                "low": [99, 100, 101, np.nan, 103],
            }
        )

        result = processor.get_trading_signals_optimized(data, fast_win=2, slow_win=3)
        # 应该能处理NaN值而不崩溃
        assert isinstance(result, dict)

    def test_zero_and_negative_prices(self):
        """测试零值和负值价格"""
        processor = OptimizedSignalProcessor()
        data = pd.DataFrame(
            {
                "close": [0, -1, 1, 2, 3],
                "high": [1, 0, 2, 3, 4],
                "low": [-1, -2, 0, 1, 2],
            }
        )

        result = processor.get_trading_signals_optimized(data, fast_win=2, slow_win=3)
        # 应该能处理异常价格而不崩溃
        assert isinstance(result, dict)
